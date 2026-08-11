import io
import json
import streamlit as st
import pandas as pd
import openai
import base64
import requests
from pypdf import PdfReader
from datetime import date
import tempfile
import os
import subprocess

# Configuración visual premium
st.set_page_config(page_title="Auditoría de Reputación LinkedIn AI", layout="centered", page_icon="🧲")

st.markdown("""
    <style>
    .report-title { font-size:28px !important; font-weight: bold; color: #1e3d59; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("🧭 LinkedIn Analytical Audit")
st.write("Transforma tus datos crudos en una auditoría de marca de alto impacto en PDF.")

# --- SECCIÓN DE GUÍA DE USO ---
with st.expander("📖 Manual de Operación y Transparencia de Costes", expanded=True):
    st.markdown("""
    ### 🛡️ Privacidad Absoluta y Costes de Operación
    Esta aplicación funciona bajo una arquitectura de código abierto. Tus datos se procesan en tiempo real en la memoria del servidor y se transmiten mediante cifrado SSL directo a la API de OpenAI. Nada se almacena en servidores externos. Cada auditoría consume unos **0,06€** del saldo de tu OpenAI API Key.
    
    ---
    
    ### 🚀 Requisitos para la ejecución:
    
    1. **🔑 OpenAI API Key**: Introduce tu clave `sk-...` en el menú lateral izquierdo. *(Requiere saldo mínimo cargado en OpenAI)*.
    2. **📊 Histórico de Contenido**: Sube el archivo **Excel (.xlsx)** o **PDF** de tus analíticas de creador de LinkedIn. 
       - Haz clic en el primer botón de abajo: (Elige 365 días en esa página y expórtatelo)
    3. **🎯 Captura de SSI (¡MUY IMPORTANTE!)**:
       - Haz clic en el segundo botón de abajo. 
       - Usa la herramienta de recortes (`Win + Shift + S`).
       - **⚠️ ATENCIÓN:** Al hacer la captura de pantalla, **recorta solo la zona de los gráficos y las puntuaciones numéricas. Deja fuera de la imagen tu foto de perfil (avatar)**. Esto evita que los sistemas de censura biométrica de OpenAI bloqueen el análisis por motivos de privacidad facial. Guárdala en tu ordenador como **PNG o JPG** y súbela al casillero inferior.
    4. **📅 Fecha de Alta**: Indica el día real en que activaste tu perfil para ajustar los promedios temporales con precisión.
    """)
    
    # Botón directo para el usuario
    
    st.link_button("📊 Importa tu datos en bruto de LinkedIN", "https://www.linkedin.com/analytics/creator/content/")

    st.link_button("🎯 Ir a mi LinkedIn SSI Oficial", "https://www.linkedin.com/sales/ssi/")

# 1. Credenciales de Seguridad
with st.sidebar:
    st.header("⚙️ Seguridad de la API")
    api_key = st.text_input("OpenAI API Key", type="default", placeholder="Pega tu clave sk-...")

# 2. Captura de Variables
st.subheader("1. Parámetros Estratégicos")
col1, col2 = st.columns(2)
with col1:
    sector = st.text_input("Ecosistema / Sector Profesional", placeholder="Ej: Ciberseguridad y Formación Profesional Informática")
with col2:
    intereses = st.text_input("Núcleos de Contenido Target", placeholder="Ej: FP, Empleo, Redes, SMR, ASIR, DAM, DAW")

fecha_alta = st.date_input("Fecha de Activación Real del Perfil", date(2026, 3, 1))

st.subheader("2. Input de Datos (LinkedIn Nativos)")
ssi_image = st.file_uploader("Captura del Social Selling Index (Imagen PNG/JPG)", type=["png", "jpg", "jpeg"])
analytics_file = st.file_uploader("Histórico Analítico de Creador (Excel .xlsx o PDF)", type=["xlsx", "pdf"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

def extraer_datos_ssi(client, uploaded_file):
    base64_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
    "content": """
Eres un extractor especializado en leer capturas de pantalla del Social Selling Index (SSI) de LinkedIn.

TU ÚNICA TAREA es leer visualmente los números que aparecen en la captura.

NO debes analizar el perfil.
NO debes interpretar los resultados.
NO debes hacer recomendaciones.
NO debes calcular ningún valor.
NO debes inferir ningún valor que no aparezca en la imagen.

La captura corresponde a la pantalla de LinkedIn titulada:
"Tu índice de ventas con las redes sociales".

Debes localizar específicamente la sección:
"Los cuatro factores que determinan tu puntuación".

En esa sección aparecen cuatro barras, cada una con un valor numérico:

1. "Establece tu marca profesional"
2. "Encuentra a las personas adecuadas"
3. "Interactúa ofreciendo información"
4. "Crea relaciones"

También debes localizar el número grande que aparece junto al gráfico:
"Índice de ventas con las redes sociales actual"

Ese número corresponde al SSI TOTAL.

IMPORTANTE:
- Lee los valores directamente de la imagen.
- Conserva los decimales tal como aparecen.
- NO confundas la longitud de las barras con sus valores numéricos.
- NO confundas el porcentaje de clasificación del sector o de la red con el SSI.
- NO utilices los valores de "Mejor clasificación SSI del sector" ni "Mejor clasificación SSI de la red" para rellenar los cuatro factores.
- El valor "51 %" corresponde a la clasificación SSI del sector, NO al SSI total.
- El valor "43 %" corresponde a la clasificación SSI de la red, NO al SSI total.
- Si un dato no aparece claramente o no puede leerse, escribe exactamente "NO DISPONIBLE".
- No inventes datos.

Para esta captura, los cuatro factores están expresados con valores numéricos que pueden contener decimales.

Devuelve ÚNICAMENTE un objeto JSON válido con esta estructura:

{
  "ssi_total": "[valor]",
  "marca_profesional": "[valor]",
  "encontrar_personas_adecuadas": "[valor]",
  "interactuar_con_informacion": "[valor]",
  "construir_relaciones": "[valor]"
}

Si un dato no aparece claramente o no puede leerse, utiliza exactamente:
"NO DISPONIBLE"

No añadas ninguna explicación fuera del JSON.
"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extrae los valores visibles de esta captura de SSI de LinkedIn."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content

# ======================================================
# CSS MAESTRO DEL INFORME
# ======================================================

# ======================================================
# CSS MAESTRO DEL INFORME — CHROME / CHROMIUM
# ======================================================

CSS_INFORME = """

/* ======================================================
   BASE
   ====================================================== */

* {
    box-sizing: border-box;
}

html {
    margin: 0;
    padding: 0;
    background: #F5F7FA;
}

body {
    margin: 0;
    padding: 0;
    background: #F5F7FA;
    color: #1F2937;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 14px;
    line-height: 1.65;
}

.report {
    width: 100%;
    max-width: 1100px;
    margin: 0 auto;
    padding: 30px 28px 50px;
}


/* ======================================================
   CABECERA PRINCIPAL
   ====================================================== */

.report-header {
    background: linear-gradient(
        135deg,
        #123B5D 0%,
        #0A66C2 100%
    );
    color: #FFFFFF;
    padding: 36px 38px 32px;
    border-radius: 18px;
    margin-bottom: 26px;
    box-shadow: 0 8px 24px rgba(18, 59, 93, 0.14);
    position: relative;
    overflow: hidden;
}

.report-header::after {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -90px;
    top: -120px;
    border-radius: 50%;
    background: rgba(255,255,255,0.08);
}

.report-header-main {
    position: relative;
    z-index: 1;
    margin-bottom: 24px;
}

.report-kicker {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    opacity: 0.80;
    margin-bottom: 8px;
}

.report-header h1 {
    margin: 0 0 8px 0;
    font-size: 30px;
    line-height: 1.2;
    font-weight: 700;
}

.report-user {
    font-size: 17px;
    font-weight: 500;
    opacity: 0.95;
}


/* ======================================================
   METADATOS
   ====================================================== */

.metadata {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 20px;
}

.metadata-credit span {
    font-weight: 500;
}

.metadata-item {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 10px;
    padding: 11px 13px;
    min-height: 62px;
}

.metadata-item strong {
    display: block;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    opacity: 0.70;
    margin-bottom: 4px;
}

.metadata-item span {
    display: block;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.4;
    color: #FFFFFF;
}

.metadata-label {
    display: block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    opacity: 0.75;
    margin-bottom: 5px;
}

.metadata-value {
    display: block;
    font-size: 13px;
    font-weight: 600;
}


/* ======================================================
   SECCIONES
   ====================================================== */

.report-sections {
    width: 100%;
}

.section {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 26px 28px;
    margin-bottom: 20px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.035);
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 13px;
    border-bottom: 1px solid #E5E7EB;
}

.section-number {
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: 9px;
    background: #EAF3FB;
    color: #0A66C2;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
}

.section h2,
.section-title {
    margin: 0 0 18px 0;
    color: #123B5D;
    font-size: 19px;
    line-height: 1.3;
    font-weight: 700;
}

.section p {
    margin: 0 0 12px;
    color: #4B5563;
}

.section p:last-child {
    margin-bottom: 0;
}

.section-content {
    width: 100%;
}


/* ======================================================
   MÉTRICAS
   ====================================================== */

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    width: 100%;
    margin: 0 0 20px;
}

.metric-card {
    background: #FAFBFC;
    border: 1px solid #E5E7EB;
    border-radius: 11px;
    padding: 15px 16px;
    min-height: 100px;
    position: relative;
}

.metric-card::before {
    content: "";
    display: block;
    width: 28px;
    height: 3px;
    border-radius: 3px;
    background: #0A66C2;
    margin-bottom: 10px;
}

.metric-label {
    color: #6B7280;
    font-size: 10px;
    line-height: 1.35;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 8px;
}

.metric-value {
    color: #123B5D;
    font-size: 24px;
    font-weight: 700;
    line-height: 1.1;
    overflow-wrap: anywhere;
}


/* ======================================================
   TEXTO
   ====================================================== */

.content-text {
    color: #4B5563;
    margin: 0 0 14px;
}

.content-text:last-child {
    margin-bottom: 0;
}


/* ======================================================
   INSIGHTS / HALLAZGOS
   ====================================================== */

.insight {
    background: #EAF3FB;
    border-left: 4px solid #0A66C2;
    border-radius: 0 10px 10px 0;
    padding: 16px 19px;
    margin: 13px 0;
}

.insight-label {
    color: #0A66C2;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 5px;
}

.insight-text {
    color: #374151;
}


/* ======================================================
   DIAGNÓSTICO
   ====================================================== */

.diagnosis {
    background: #FFF3E8;
    border-left: 4px solid #E67E22;
    border-radius: 0 10px 10px 0;
    padding: 18px 20px;
    margin: 14px 0;
}

.diagnosis-label {
    color: #A95400;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}

.diagnosis-text {
    color: #4B5563;
}


/* ======================================================
   BLOQUES DE ANÁLISIS / LIMITACIONES
   ====================================================== */

.analysis-block {
    margin: 14px 0;
}

.limitation {
    background: #F8F9FA;
    border: 1px dashed #D1D5DB;
    border-radius: 10px;
    padding: 15px 17px;
    color: #4B5563;
}

.limitation-label,
.block-label {
    color: #4B5563;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 5px;
}

.block-text {
    color: #4B5563;
}


/* ======================================================
   RECOMENDACIONES
   ====================================================== */

.recommendation {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    overflow: hidden;
    margin: 16px 0;
    background: #FFFFFF;
}

.recommendation-header {
    background: #F8FAFC;
    padding: 13px 17px;
    border-bottom: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
}

.recommendation-title {
    font-weight: 700;
    color: #123B5D;
}

.priority {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 20px;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    white-space: nowrap;
}

.priority-alta {
    background: #FDEDEC;
    color: #C0392B;
}

.priority-media {
    background: #FFF3E8;
    color: #A95400;
}

.priority-baja {
    background: #EAF7F0;
    color: #198754;
}

.recommendation-body {
    padding: 17px 18px;
}

.rec-row {
    margin-bottom: 14px;
}

.rec-row:last-child {
    margin-bottom: 0;
}

.rec-label {
    color: #6B7280;
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 3px;
}

.rec-value {
    color: #4B5563;
}


/* ======================================================
   EXPERIMENTOS
   ====================================================== */

.experiment {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    overflow: hidden;
    margin: 16px 0;
    background: #FFFFFF;
}

.experiment-header {
    background: #EAF3FB;
    padding: 13px 17px;
    color: #123B5D;
    font-weight: 700;
}

.experiment-body {
    padding: 17px 18px;
    background: #FFFFFF;
}

.experiment-row {
    display: grid;
    grid-template-columns: 180px minmax(0, 1fr);
    gap: 16px;
    padding: 10px 0;
    border-bottom: 1px solid #F3F4F6;
}

.experiment-row:last-child {
    border-bottom: none;
}

.experiment-label {
    color: #6B7280;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.experiment-value {
    color: #4B5563;
}


/* ======================================================
   TABLAS
   ====================================================== */

.table-wrapper {
    width: 100%;
    margin: 15px 0 4px;
    overflow-x: auto;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    background: #FFFFFF;
    table-layout: auto;
}

.data-table th {
    background: #123B5D;
    color: #FFFFFF;
    padding: 10px 9px;
    text-align: left;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 700;
}

.data-table td {
    padding: 9px;
    border-bottom: 1px solid #E5E7EB;
    color: #4B5563;
    vertical-align: top;
    overflow-wrap: anywhere;
}

.data-table tbody tr:nth-child(even) td {
    background: #FAFBFC;
}

.data-table tbody tr:hover td {
    background: #EAF3FB;
}

.data-table a {
    color: #0A66C2;
    text-decoration: none;
    font-weight: 600;
}

.data-table a:hover {
    text-decoration: underline;
}


/* ======================================================
   BOTONES DE PUBLICACIONES
   ====================================================== */

.publication-link {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 6px;
    background: #EAF3FB;
    color: #0A66C2 !important;
    text-decoration: none !important;
    font-size: 10px;
    font-weight: 700 !important;
    white-space: nowrap;
    border: 1px solid #D7EAF8;
}

.publication-link:hover {
    background: #DCECF9;
    text-decoration: none !important;
}


/* ======================================================
   FOOTER
   ====================================================== */

.report-footer {
    margin-top: 28px;
    padding-top: 14px;
    border-top: 1px solid #E5E7EB;
    text-align: center;
    color: #6B7280;
    font-size: 10px;
}


/* ======================================================
   CONTROL DE PÁGINAS — CHROME PDF
   ====================================================== */

.report-header {
    break-inside: avoid;
    page-break-inside: avoid;
}

.section {
    break-inside: avoid;
    page-break-inside: avoid;
}

.metric-card,
.insight,
.diagnosis,
.recommendation,
.experiment,
.limitation {
    break-inside: avoid;
    page-break-inside: avoid;
}

.data-table {
    break-inside: auto;
    page-break-inside: auto;
}

.data-table tr {
    break-inside: avoid;
    page-break-inside: avoid;
}


/* ======================================================
   IMPRESIÓN
   ====================================================== */

@media print {

    html,
    body {
        background: #FFFFFF;
    }

    body {
        font-size: 12px;
    }

    .report {
        max-width: none;
        width: 100%;
        padding: 0;
        margin: 0;
    }

    .report-header {
        box-shadow: none;
    }

    .section {
        box-shadow: none;
    }

    .data-table tbody tr:hover td {
        background: inherit;
    }

}


/* ======================================================
   RESPONSIVE
   ====================================================== */

@media (max-width: 800px) {

    .report {
        padding: 18px 12px 40px;
    }

    .report-header {
        padding: 27px 23px;
    }

    .metadata {
        grid-template-columns: 1fr;
    }

    .metrics-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .section {
        padding: 22px 20px;
    }

    .experiment-row {
        grid-template-columns: 1fr;
        gap: 4px;
    }

}

@media (max-width: 500px) {

    .metrics-grid {
        grid-template-columns: 1fr;
    }

    .report-header h1 {
        font-size: 24px;
    }

    .section h2,
    .section-title {
        font-size: 17px;
    }

    .recommendation-header {
        align-items: flex-start;
        flex-direction: column;
    }

}
"""

# ======================================================
# FUNCIÓN — GENERACIÓN DEL HTML DESDE EL JSON AUDITADO
# ======================================================

def generar_html(analysis_json):

    metadata = analysis_json.get("metadata", {})
    sections = analysis_json.get("sections", [])

    def escapar(valor):
        """Escapa texto para HTML."""
        if valor is None:
            return ""

        from html import escape

        return escape(str(valor))

#-------------------------------------------
    def es_url(valor):

        if not isinstance(valor, str):
            return False

        return (
            valor.startswith("http://")
            or valor.startswith("https://")
        )

    # ==================================================
    # RENDERIZADO DE CONTENIDOS
    # ==================================================

    def render_content(item):

        item_type = item.get("type")

        # --------------------------------------------------
        # TEXTO
        # --------------------------------------------------

        if item_type == "text":

            return f"""
            <div class="content-text">
                {escapar(item.get("text", ""))}
            </div>
            """

        # --------------------------------------------------
        # MÉTRICA
        # --------------------------------------------------

        elif item_type == "metric":

            return f"""
            <div class="metric-card">

                <div class="metric-label">
                    {escapar(item.get("label", ""))}
                </div>

                <div class="metric-value">
                    {escapar(item.get("value", ""))}
                </div>

            </div>
            """

        # --------------------------------------------------
        # INSIGHT
        # --------------------------------------------------

        elif item_type == "insight":

            return f"""
            <div class="insight">

                <div class="insight-label">
                    {escapar(item.get("label", "HALLAZGO"))}
                </div>

                <div class="insight-text">
                    {escapar(item.get("text", ""))}
                </div>

            </div>
            """

        # --------------------------------------------------
        # LIMITACIÓN
        # --------------------------------------------------

        elif item_type == "limitation":

            return f"""
            <div class="analysis-block limitation">

                <div class="block-label">
                    LIMITACIÓN
                </div>

                <div class="block-text">
                    {escapar(item.get("text", ""))}
                </div>

            </div>
            """

        # --------------------------------------------------
        # DIAGNÓSTICO
        # --------------------------------------------------

        elif item_type == "diagnosis":

            print("ENTRANDO EN RENDER DIAGNOSIS")
            print("ITEM TYPE:", repr(item_type))
            print("ITEM:", item)

            html = ""

            # ----------------------------------------------
            # FORTALEZA
            # ----------------------------------------------

            fortalezas = (
                item.get("primary_strength")
                or item.get("fortalezas")
                or item.get("fortaleza")
            )

            if fortalezas:

                html += f"""
                <div class="diagnosis">

                    <div class="diagnosis-label">
                        FORTALEZA
                    </div>

                    <div class="diagnosis-text">
                        {escapar(fortalezas)}
                    </div>

                </div>
                """

            # ----------------------------------------------
            # LIMITACIÓN
            # ----------------------------------------------

            limitaciones = (
                item.get("primary_limitation")
                or item.get("limitaciones")
                or item.get("limitacion")
            )

            if limitaciones:

                html += f"""
                <div class="diagnosis">

                    <div class="diagnosis-label">
                        LIMITACIÓN
                    </div>

                    <div class="diagnosis-text">
                        {escapar(limitaciones)}
                    </div>

                </div>
                """

            # ----------------------------------------------
            # OPORTUNIDAD
            # ----------------------------------------------

            oportunidades = (
                item.get("primary_opportunity")
                or item.get("oportunidades")
                or item.get("oportunidad")
            )

            if oportunidades:

                html += f"""
                <div class="diagnosis">

                    <div class="diagnosis-label">
                        OPORTUNIDAD
                    </div>

                    <div class="diagnosis-text">
                        {escapar(oportunidades)}
                    </div>

                </div>
                """

            # ----------------------------------------------
            # ANOMALÍA
            # ----------------------------------------------

            anomalias = (
                item.get("primary_anomaly")
                or item.get("anomalías")
                or item.get("anomalias")
                or item.get("anomalía")
                or item.get("anomalia")
            )

            if anomalias:

                html += f"""
                <div class="diagnosis">

                    <div class="diagnosis-label">
                        ANOMALÍA
                    </div>

                    <div class="diagnosis-text">
                        {escapar(anomalias)}
                    </div>

                </div>
                """

            # ----------------------------------------------
            # INCERTIDUMBRE
            # ----------------------------------------------

            incertidumbres = (
                item.get("primary_uncertainty")
                or item.get("incertidumbres")
                or item.get("incertidumbre")
            )

            if incertidumbres:

                html += f"""
                <div class="diagnosis">

                    <div class="diagnosis-label">
                        INCERTIDUMBRE
                    </div>

                    <div class="diagnosis-text">
                        {escapar(incertidumbres)}
                    </div>

                </div>
                """

            return html

        # --------------------------------------------------
        # RECOMENDACIÓN
        # --------------------------------------------------

        elif item_type == "recommendation":

            prioridad = item.get("priority", "")

            prioridad_class = ""

            if str(prioridad).lower() == "alta":
                prioridad_class = "priority-alta"

            elif str(prioridad).lower() == "media":
                prioridad_class = "priority-media"

            elif str(prioridad).lower() == "baja":
                prioridad_class = "priority-baja"

            html = f"""
            <div class="recommendation">

                <div class="recommendation-header">

                    <div class="recommendation-title">
                        Recomendación estratégica
                    </div>

                    <span class="priority {prioridad_class}">
                        {escapar(prioridad)}
                    </span>

                </div>

                <div class="recommendation-body">
            """

            campos = [
                ("HALLAZGO", "finding"),
                ("EVIDENCIA", "evidence"),
                ("INTERPRETACIÓN", "interpretation"),
                ("ACCIÓN", "action"),
                ("CÓMO COMPROBARLA", "verification")
            ]

            for etiqueta, campo in campos:

                valor = item.get(campo)

                if valor not in [None, ""]:

                    html += f"""
                    <div class="rec-row">

                        <div class="rec-label">
                            {etiqueta}
                        </div>

                        <div class="rec-value">
                            {escapar(valor)}
                        </div>

                    </div>
                    """

            html += """
                </div>
            </div>
            """

            return html


        # --------------------------------------------------
        # EXPERIMENTO
        # --------------------------------------------------

        elif item_type == "experiment":

            html = """
            <div class="experiment">

                <div class="experiment-header">
                    Experimento estratégico
                </div>

                <div class="experiment-body">
            """

            campos = [
                ("HIPÓTESIS", "hypothesis"),
                ("VARIABLE", "variable"),
                ("CAMBIO", "change"),
                ("MÉTRICA", "metric"),
                ("REFERENCIA", "reference"),
                ("CRITERIO DE ÉXITO", "success_criterion"),
                ("DECISIÓN POSTERIOR", "subsequent_decision")
            ]

            for etiqueta, campo in campos:

                valor = item.get(campo)

                if valor not in [None, ""]:

                    html += f"""
                    <div class="experiment-row">

                        <div class="experiment-label">
                            {escapar(etiqueta)}
                        </div>

                        <div class="experiment-value">
                            {escapar(valor)}
                        </div>

                    </div>
                    """

            html += """
                </div>

            </div>
            """

            return html

        # --------------------------------------------------
        # TABLA
        # --------------------------------------------------

        elif item_type == "table":

            columns = item.get("columns", [])
            rows = item.get("rows", [])

            html = """
            <div class="table-wrapper">

                <table class="data-table">

                    <thead>
                        <tr>
            """

            for column in columns:

                html += f"""
                            <th>
                                {escapar(column)}
                            </th>
                """

            html += """
                        </tr>
                    </thead>

                    <tbody>
            """

            for row in rows:

                html += """
                        <tr>
                """

                if isinstance(row, dict):

                    for column in columns:

                        valor = row.get(column, "")

                        if es_url(valor):

                            html += f"""
                                <td>
                                    <a
                                        class="publication-link"
                                        href="{escapar(valor)}"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        🔗 Ver publicación
                                    </a>
                                </td>
                            """

                        else:

                            html += f"""
                                <td>
                                    {escapar(valor)}
                                </td>
                            """

                elif isinstance(row, list):

                    for valor in row:

                        if es_url(valor):

                            html += f"""
                                <td>
                                    <a
                                        class="publication-link"
                                        href="{escapar(valor)}"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        Ver publicación
                                    </a>
                                </td>
                            """

                        else:

                            html += f"""
                                <td>
                                    {escapar(valor)}
                                </td>
                            """

                html += """
                        </tr>
                """

            html += """
                    </tbody>

                </table>

            </div>
            """

            return html

        # --------------------------------------------------
        # TIPO DESCONOCIDO
        # --------------------------------------------------

        return ""

    # ======================================================
    # METADATOS
    # ======================================================

    usuario = escapar(metadata.get("usuario", ""))
    periodo = escapar(metadata.get("periodo", ""))
    fecha_inicio = escapar(metadata.get("fecha_de_inicio", ""))
    fecha_fin = escapar(metadata.get("fecha_de_fin", ""))
    fecha_generacion = escapar(metadata.get("fecha_de_generacion", ""))
    estado = escapar(metadata.get("estado", ""))
    version = escapar(metadata.get("version", ""))

    # ======================================================
    # DOCUMENTO HTML
    # ======================================================

    print("LONGITUD CSS:", len(CSS_INFORME))
    print("CONTIENE ASTERISCO:", "* {" in CSS_INFORME)
    print("CONTIENE REPORT:", ".report {" in CSS_INFORME)
    print("CONTIENE METADATA:", ".metadata {" in CSS_INFORME)
    print("CONTIENE METRIC:", ".metric-card {" in CSS_INFORME)
    print("CONTIENE TABLE:", ".data-table {" in CSS_INFORME)

    # ======================================================
    # INICIO DEL DOCUMENTO
    # ======================================================

    html = f"""
<!DOCTYPE html>

<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
        content="width=device-width, initial-scale=1.0">

    <title>
        Auditoría Estratégica de LinkedIn
    </title>

    <style>

        {CSS_INFORME}

    </style>

</head>

<body>

    <main class="report">

        <!-- ==========================================
            CABECERA
            ========================================== -->

        <header class="report-header">

            <div class="report-header-main">

                <div class="report-kicker">
                    AUDITORÍA ESTRATÉGICA DE LINKEDIN
                </div>

                <h1>
                    Informe Ejecutivo
                </h1>

                <div class="report-user">
                    {usuario}
                </div>

            </div>

            <!-- ======================================
                INFORMACIÓN DEL INFORME
                ====================================== -->

            <div class="metadata">

                <div class="metadata-item">

                    <strong>Periodo analizado</strong>

                    <span>
                        {periodo}
                    </span>

                </div>

                <div class="metadata-item">

                    <strong>Actividad analizada</strong>

                    <span>
                        {len(analizador.df)} publicaciones
                    </span>

                </div>

                <div class="metadata-item">

                    <strong>Elaborado por</strong>

                    <span>
                        Ruta TI
                    </span>

                </div>

                <div class="metadata-item metadata-credit">

                    <strong>Asistencia</strong>

                    <span>
                        Análisis asistido por ChatGPT
                    </span>

                </div>

            </div>

        </header>

        
        <div class="report-sections">

"""

    # ======================================================
    # SECCIONES
    # ======================================================

    for section in sections:

        numero = section.get("number", "")
        titulo = section.get("title", "")
        contenido = section.get("content", [])

        html += f"""

            <section class="section">

                <div class="section-number">

                    {escapar(numero)}

                </div>

                <h2>

                    {escapar(titulo)}

                </h2>

                <div class="section-content">

"""

        # --------------------------------------------------
        # MÉTRICAS
        # --------------------------------------------------

        metricas = [

            item
            for item in contenido
            if item.get("type") == "metric"

        ]

        if metricas:

            html += """

                    <div class="metrics-grid">

"""

            for item in metricas:

                html += render_content(item)

            html += """

                    </div>

"""

        # --------------------------------------------------
        # RESTO DEL CONTENIDO
        # --------------------------------------------------

        for item in contenido:

            if item.get("type") == "metric":
                continue

            if item.get("type") == "diagnosis":

                print("DEBUG DIAGNOSIS:", item)

                resultado_diagnosis = render_content(item)

                print("DEBUG HTML DIAGNOSIS:", repr(resultado_diagnosis))

                html += resultado_diagnosis

            else:

                html += render_content(item)

        html += """

                </div>

            </section>

"""

    # ======================================================
    # CIERRE DEL DOCUMENTO
    # ======================================================

    html += """

        </div>

    </main>

</body>

</html>

"""

    return html

# 3. Procesamiento y Renderizado del Informe Ejecutivo
if st.button("🚀 Ejecutar Auditoría Estratégica Completa"):
    if not api_key:
        st.error("Error de autenticación: Introduce tu OpenAI API Key del menú lateral.")
    elif not ssi_image or not analytics_file:
        st.error("Error de datos: Es obligatorio adjuntar tanto la captura visual del SSI como el registro analítico.")
    else:
        with st.spinner("Generando auditoría corporativa y maquetando PDF ejecutivo... Por favor, espera."):
            try:
                hoy = date.today()
                dias_activos = (hoy - fecha_alta).days
                meses_activos = max(1, round(dias_activos / 30.4))
                
                if analytics_file.name.endswith('.pdf'):
                    reader = PdfReader(analytics_file)
                    analytics_text = "".join([page.extract_text() + "\n" for page in reader.pages])
                else:
                    from linkedin_analyzer import LinkedInAnalyzer

                    excel = pd.ExcelFile(analytics_file)

                    st.write("Hojas encontradas:")
                    st.write(excel.sheet_names)

                    df = pd.read_excel(
                        analytics_file,
                        sheet_name="PUBLICACIONES PRINCIPALES",
                        header=2
                    )

                    st.dataframe(df.head())

                    # ======================================================
                    # PROPIEDADES DEL EXCEL
                    # ======================================================

                    from openpyxl import load_workbook

                    wb = load_workbook(analytics_file, read_only=True)

                    props = wb.properties

                    st.write("===== PROPIEDADES EXCEL =====")
                    st.write("title:", props.title)
                    st.write("subject:", props.subject)
                    st.write("creator:", props.creator)
                    st.write("description:", props.description)
                    st.write("keywords:", props.keywords)

                    wb.close()

                    # ======================================================
                    # IDENTIFICACIÓN DEL USUARIO
                    # ======================================================

                    import re

                    excel_title = props.title or ""

                    linkedin_name = excel_title

                    # Eliminar prefijo generado por LinkedIn
                    if linkedin_name.startswith("AnalisisConjunto_"):
                        linkedin_name = linkedin_name[len("AnalisisConjunto_"):]

                    # Eliminar extensión
                    if linkedin_name.lower().endswith(".xlsx"):
                        linkedin_name = linkedin_name[:-5]

                    # Eliminar las dos fechas finales
                    linkedin_name = re.sub(
                        r"_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}$",
                        "",
                        linkedin_name
                    )

                    # Eliminar emojis e iconos del nombre
                    linkedin_name = re.sub(
                        r"[\U0001F000-\U0001FAFF"
                        r"\U00002600-\U000027BF"
                        r"\U0001F1E6-\U0001F1FF]+",
                        "",
                        linkedin_name
                    )

                    # Limpiar espacios sobrantes
                    linkedin_name = re.sub(r"\s+", " ", linkedin_name).strip()

                    st.write("===== USUARIO IDENTIFICADO =====")
                    st.write(linkedin_name)

                    analizador = LinkedInAnalyzer(df)

                    destacadas = analizador.publicaciones_destacadas()

                    st.write("TOP 5:", destacadas["Top 5"])
                    st.write("BOTTOM 5:", destacadas["Bottom 5"])
                    st.write("TOP 5 ENGAGEMENT:", destacadas["Top 5 Engagement"])

                    st.write(
                        "MÉTRICAS PYTHON:",
                        analizador.metricas()
                    )

                    rendimiento = analizador.analisis_rendimiento()

                    st.write(
                        "ANÁLISIS DE RENDIMIENTO:",
                        rendimiento
                    )
                    st.write(
                        "NIVEL DE MADUREZ:",
                        analizador.nivel_madurez()
                    )
                    analytics_text = analizador.resumen_para_ia()

                    madurez = analizador.nivel_madurez()

                    st.subheader("Resumen procesado por Python")

                    st.code(analytics_text)

                base64_image = encode_image(ssi_image)
                st.info(f"SSI cargado correctamente: {ssi_image.name}")

                client = openai.OpenAI(api_key=api_key)

                ssi_text = extraer_datos_ssi(client, ssi_image)

                st.subheader("Datos SSI extraídos")
                st.code(ssi_text)

                
                sector_real = sector if sector else "Ciberseguridad y Formación Profesional"
                intereses_real = intereses if intereses else "FP, Empleo, Redes, SMR, ASIR, DAM, DAW"

                # ======================================================
                # METADATOS OFICIALES DEL INFORME
                # ======================================================

                from datetime import datetime

                # Fecha de generación
                report_generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

                # Fechas para presentación
                fecha_alta_display = (
                    fecha_alta.strftime("%d/%m/%Y")
                    if hasattr(fecha_alta, "strftime")
                    else str(fecha_alta)
                )

                hoy_display = (
                    hoy.strftime("%d/%m/%Y")
                    if hasattr(hoy, "strftime")
                    else str(hoy)
                )

                # Periodo REAL del análisis
                analysis_period = f"{fecha_alta_display} — {hoy_display}"

                # Estado del informe
                report_status = "BETA · FASE PRELIMINAR"

                # Metadatos oficiales
                report_metadata = {
                    "usuario": linkedin_name,
                    "periodo": analysis_period,
                    "fecha_inicio": fecha_alta_display,
                    "fecha_fin": hoy_display,
                    "fecha_generacion": report_generated_at,
                    "estado": report_status
                }

                # ======================================================
                # PRUEBA DE METADATOS
                # ======================================================

                st.write("===== METADATOS DEL INFORME =====")
                st.write("USUARIO:", linkedin_name)
                st.write("PERIODO:", analysis_period)
                st.write("FECHA DE INICIO:", fecha_alta_display)
                st.write("FECHA DE FIN:", hoy_display)
                st.write("GENERADO:", report_generated_at)
                st.write("ESTADO:", report_status)


                system_prompt = f"""

                # ======================================================
                # MÓDULO 0 — IDENTIDAD, ROL Y PRINCIPIOS DEL ANALISTA
                # ======================================================

                ## 0.1 — IDENTIDAD

                Actúas como un ANALISTA ESTRATÉGICO Y MENTOR ESPECIALIZADO
                EN ANALÍTICA DE ACTIVIDAD PROFESIONAL EN LINKEDIN.

                Tu función no es generar consejos genéricos sobre LinkedIn,
                ni redactar contenido motivacional.

                Tu función es transformar los datos disponibles de una cuenta
                en conocimiento útil para su propietario.

                La pregunta fundamental es:

                ¿Qué está ocurriendo realmente en esta cuenta?

                Y posteriormente:

                ¿Qué puede afirmarse con seguridad, qué constituye un indicio,
                qué sigue siendo una hipótesis y qué no puede determinarse
                con los datos disponibles?

                ---

                ## 0.2 — MÉTODO DE ANÁLISIS

                Antes de formular conclusiones:

                1. observa los datos;
                2. comprueba su coherencia;
                3. compara las métricas relevantes;
                4. identifica patrones, diferencias y valores extremos;
                5. distingue comportamiento habitual de excepcional;
                6. separa hechos, indicios e hipótesis;
                7. identifica las incertidumbres;
                8. construye el diagnóstico;
                9. formula acciones únicamente cuando exista base analítica.

                No busques problemas artificialmente.

                No partas de recomendaciones previamente decididas.

                Primero determina qué muestran los datos.
                Después interpreta su significado.
                Finalmente decide si existe alguna acción justificable.

                ---

                ## 0.3 — FUENTE DE VERDAD

                Los valores numéricos proporcionados por Python constituyen
                la fuente de verdad del análisis cuantitativo.

                Debes:

                - utilizar exclusivamente los valores disponibles;
                - conservar las cifras proporcionadas;
                - utilizar únicamente cálculos que puedan obtenerse de esos datos;
                - indicar expresamente cuando falte información.

                No inventes, completes, estimes ni supongas:

                - métricas;
                - publicaciones;
                - fechas;
                - impresiones;
                - interacciones;
                - engagement;
                - URLs;
                - contenidos;
                - características de las publicaciones.

                La ausencia de un dato debe tratarse como una limitación
                del análisis, no como una invitación a inferirlo.

                ---

                ## 0.4 — EVIDENCIA Y NIVEL DE CERTEZA

                Toda conclusión relevante debe poder vincularse con una evidencia
                disponible.

                Utiliza tres niveles:

                HECHO
                Conclusión directamente demostrable mediante los datos.

                INDICIO
                Patrón observado que merece atención, pero que todavía no
                permite establecer una conclusión definitiva.

                HIPÓTESIS
                Explicación posible que necesita comprobación.

                No presentes una hipótesis como hecho.

                Cuando los datos no permitan determinar algo, dilo explícitamente.

                ---

                ## 0.5 — CAUSALIDAD

                Los datos descriptivos permiten observar resultados y relaciones,
                pero no demuestran por sí solos sus causas.

                No atribuyas automáticamente un resultado a:

                - tema;
                - formato;
                - horario;
                - hashtags;
                - algoritmo;
                - audiencia;
                - calidad;
                - CTA;
                - frecuencia;
                - viralidad;
                - comportamiento de los usuarios.

                Solo puede establecerse causalidad cuando los datos proporcionados
                permitan demostrarla.

                Cuando exista únicamente una relación observable, utiliza formulaciones
                como:

                - "se observa";
                - "coincide con";
                - "constituye un indicio";
                - "podría estar relacionado con";
                - "debería comprobarse".

                ---

                ## 0.6 — CONTENIDO NO DISPONIBLE

                Las métricas cuantitativas no permiten conocer por sí solas
                las características cualitativas de una publicación.

                No inventes:

                - tema;
                - título;
                - formato;
                - tono;
                - horario;
                - hashtags;
                - imagen;
                - vídeo;
                - CTA;
                - audiencia;
                - estructura;
                - intención;
                - calidad;
                - relevancia.

                Una URL puede conservarse como referencia de la publicación,
                pero no constituye por sí misma evidencia suficiente para
                establecer un patrón de contenido.

                ---

                ## 0.7 — ACTIVIDAD, RESULTADO Y EFICACIA

                No confundas:

                ACTIVIDAD
                con
                RESULTADO

                ni:

                RESULTADO
                con
                EFICACIA ESTRATÉGICA.

                El número de publicaciones describe actividad.
                No demuestra por sí mismo experiencia, eficacia ni madurez estratégica.

                Una cuenta puede publicar mucho y obtener resultados modestos,
                o publicar menos y presentar publicaciones especialmente eficientes.

                La actividad debe interpretarse siempre junto con sus resultados.

                El número de publicaciones NO debe utilizarse como indicador
                directo de experiencia avanzada en LinkedIn.

                ---

                ## 0.8 — DIMENSIONES DEL RENDIMIENTO

                Distingue siempre:

                ALCANCE
                = impresiones.

                INTERACCIONES
                = número absoluto de interacciones.

                ENGAGEMENT
                = proporción de interacciones respecto a las impresiones,
                según la metodología proporcionada por Python.

                Estas dimensiones describen aspectos diferentes del rendimiento.

                Un valor elevado en una dimensión no implica automáticamente
                un resultado superior en las demás.

                No determines que una publicación es "mejor" utilizando
                una única métrica de forma aislada.

                ---

                ## 0.9 — PRINCIPIO COMPARATIVO

                No interpretes los valores únicamente de forma aislada.

                Cuando existan datos suficientes, utiliza las referencias
                proporcionadas por Python para comparar:

                - media;
                - mediana;
                - mínimo;
                - máximo;
                - rango;
                - desviación estándar;
                - proporciones;
                - posiciones relativas;
                - rankings;
                - concentración;
                - relaciones entre métricas.

                La pregunta no es únicamente:

                "¿Cuánto obtuvo?"

                También:

                "¿Cómo se compara con el comportamiento de esta cuenta?"

                ---

                ## 0.10 — HUMILDAD ANALÍTICA

                No conviertas una métrica alta automáticamente en una fortaleza.

                No conviertas una métrica baja automáticamente en una debilidad.

                No conviertas una anomalía automáticamente en un problema.

                No fuerces una conclusión cuando los datos no la permitan.

                Un análisis riguroso debe identificar tanto lo que los datos
                permiten conocer como aquello que todavía permanece incierto.

                ---

                ## 0.11 — PRINCIPIO DE ESPECIFICIDAD

                El informe debe describir ESTA cuenta.

                Evita conclusiones o recomendaciones que podrían copiarse
                literalmente en cualquier otro perfil.

                Las buenas prácticas generales solo pueden utilizarse cuando
                estén vinculadas a un hallazgo concreto de esta cuenta.

                ---

                ## 0.12 — PROFUNDIDAD

                La madurez estratégica del usuario modifica la forma de explicar
                los resultados, pero no reduce el rigor del análisis.

                Adapta:

                - lenguaje;
                - explicación pedagógica;
                - complejidad de las acciones.

                No reduzcas:

                - rigor;
                - comparación;
                - detección de patrones;
                - identificación de anomalías;
                - separación entre evidencia e hipótesis.

                ---

                ## 0.13 — OBJETIVO

                El resultado debe permitir al propietario comprender aspectos
                que no podría identificar simplemente observando sus métricas.

                El análisis debe transformar:

                DATOS
                → EVIDENCIA
                → INTERPRETACIÓN
                → DIAGNÓSTICO
                → ACCIÓN
                → APRENDIZAJE

                No transformar datos directamente en consejos.

                No generar recomendaciones por obligación.

                Una recomendación solo existe cuando puede derivarse de un hallazgo.

                Una hipótesis solo existe para reducir una incertidumbre.

                El objetivo final es producir conocimiento útil y verificable
                sobre el comportamiento de esta cuenta.

                
                # ======================================================
                # BLOQUE 1 — ARQUITECTURA DEL INFORME
                # ======================================================

                La arquitectura del informe es FIJA. Debe contener exactamente estas
                14 secciones y en este orden:

                1. RESUMEN EJECUTIVO
                2. ESTADO ACTUAL DEL PERFIL
                3. RADIOGRAFÍA CUANTITATIVA
                4. DISTRIBUCIÓN DEL RENDIMIENTO
                5. FRECUENCIA Y ACTIVIDAD
                6. ANÁLISIS DEL ALCANCE
                7. ANÁLISIS DEL ENGAGEMENT
                8. TOP 5 PUBLICACIONES POR IMPRESIONES
                9. BOTTOM 5 PUBLICACIONES POR IMPRESIONES
                10. TOP 5 PUBLICACIONES POR ENGAGEMENT
                11. CRUCE ENTRE ALCANCE Y ENGAGEMENT
                12. DIAGNÓSTICO ESTRATÉGICO
                13. RECOMENDACIONES PRIORITARIAS
                14. EXPERIMENTOS Y PRÓXIMOS PASOS

                REGLAS:

                - Mantén exactamente estos nombres, orden y número de secciones.
                - No añadas, elimines, combines ni dividas secciones principales.
                - Si faltan datos, conserva la sección e indica la limitación.
                - Personaliza mediante el contenido y el análisis de los datos proporcionados, sin modificar la arquitectura.
                - Cada sección debe aportar una función analítica diferente; evita repetir
                conclusiones ya desarrolladas.
                - Las secciones forman una única pieza analítica y deben mantener coherencia
                entre sí.

                FLUJO ANALÍTICO:# ======================================================
                DATOS → DISTRIBUCIÓN → ALCANCE → ENGAGEMENT →
                CRUCE DE MÉTRICAS → DIAGNÓSTICO → RECOMENDACIONES → EXPERIMENTOS

                No adelantes conclusiones propias de secciones posteriores.
                Las recomendaciones siguen al diagnóstico y los experimentos siguen a
                las recomendaciones.

                # ======================================================
                # BLOQUE 2 — CONTENIDO DE CADA SECCIÓN
                # ======================================================

                Cada sección tiene una función específica dentro del informe.

                No repitas mecánicamente información entre secciones.

                La información debe avanzar desde la descripción de los datos hasta
                el diagnóstico y la toma de decisiones.

                Las reglas detalladas de interpretación se encuentran en los BLOQUES 3–8.


                # ======================================================
                # 2.1 — RESUMEN EJECUTIVO
                # ======================================================

                Sintetiza el diagnóstico completo para permitir comprender rápidamente:

                - situación actual;
                - principal fortaleza;
                - principal limitación, cuando exista;
                - principal oportunidad;
                - principal incertidumbre;
                - prioridad estratégica.

                No enumeres todas las métricas ni introduzcas recomendaciones que todavía
                no hayan sido justificadas.


                # ======================================================
                # 2.2 — ESTADO ACTUAL DEL PERFIL
                # ======================================================

                Describe la situación general de la cuenta integrando:

                - actividad;
                - resultados observados;
                - tracción;
                - madurez estratégica, cuando Python la proporcione.

                Debe responder:

                "¿En qué situación se encuentra actualmente la cuenta?"

                Distingue actividad, resultado y eficacia estratégica.


                # ======================================================
                # 2.3 — RADIOGRAFÍA CUANTITATIVA
                # ======================================================

                Presenta las principales métricas del periodo analizado y explica qué
                muestran conjuntamente sobre el comportamiento de la cuenta.

                Utiliza únicamente las métricas disponibles y calculadas por Python.


                # ======================================================
                # 2.4 — DISTRIBUCIÓN DEL RENDIMIENTO
                # ======================================================

                Explica cómo se distribuyen los resultados entre las publicaciones.

                Analiza, cuando los datos lo permitan:

                - concentración;
                - dispersión;
                - comportamiento habitual;
                - valores extremos;
                - estabilidad;
                - resultados excepcionales.

                Puede utilizarse la comparación entre grupos, extremos y medidas centrales.


                # ======================================================
                # 2.5 — FRECUENCIA Y ACTIVIDAD
                # ======================================================

                Describe el patrón de actividad durante el periodo analizado utilizando,
                cuando estén disponibles:

                - publicaciones;
                - frecuencia semanal y mensual;
                - intervalo entre publicaciones;
                - duración del periodo;
                - resultados observados.

                No conviertas la frecuencia en una recomendación automática.


                # ======================================================
                # 2.6 — ANÁLISIS DEL ALCANCE
                # ======================================================

                Analiza el comportamiento de las impresiones.

                Explica:

                - comportamiento habitual;
                - valores centrales y extremos;
                - concentración;
                - publicaciones que destacan por exposición.

                No interpretes las impresiones automáticamente como calidad, relevancia
                o éxito estratégico.


                # ======================================================
                # 2.7 — ANÁLISIS DEL ENGAGEMENT
                # ======================================================

                Analiza la eficiencia relativa de interacción y su relación con:

                - impresiones;
                - interacciones absolutas;
                - publicaciones con mayor engagement.

                Distingue siempre eficiencia, volumen de interacción y alcance.


                # ======================================================
                # 2.8 — TOP 5 PUBLICACIONES POR IMPRESIONES
                # ======================================================

                Presenta las cinco publicaciones con mayor número de impresiones,
                conservando los datos proporcionados por Python:

                - posición;
                - fecha;
                - impresiones;
                - interacciones;
                - engagement;
                - URL.

                Explica qué representan dentro de la distribución del alcance.


                # ======================================================
                # 2.9 — BOTTOM 5 PUBLICACIONES POR IMPRESIONES
                # ======================================================

                Presenta las cinco publicaciones con menor número de impresiones,
                conservando los mismos datos disponibles.

                Explica qué representan dentro de la distribución del alcance.

                No las clasifiques automáticamente como publicaciones deficientes.


                # ======================================================
                # 2.10 — TOP 5 PUBLICACIONES POR ENGAGEMENT
                # ======================================================

                Presenta las cinco publicaciones con mayor engagement y sus métricas
                disponibles.

                Analiza conjuntamente eficiencia de interacción y volumen de exposición.


                # ======================================================
                # 2.11 — CRUCE ENTRE ALCANCE Y ENGAGEMENT
                # ======================================================

                Integra las dimensiones de alcance y eficiencia.

                Compara los rankings anteriores e identifica, cuando existan:

                - coincidencias;
                - diferencias;
                - separación entre exposición y eficiencia;
                - casos excepcionales.

                No inventes combinaciones que no estén presentes en los datos.


                # ======================================================
                # 2.12 — DIAGNÓSTICO ESTRATÉGICO
                # ======================================================

                Integra los hallazgos anteriores para responder:

                "¿Qué comportamiento está demostrando realmente esta cuenta?"

                Cuando exista evidencia suficiente, identifica:

                - fortalezas;
                - limitaciones;
                - oportunidades;
                - anomalías;
                - incertidumbres;
                - prioridad estratégica.

                No repitas mecánicamente las secciones anteriores.


                # ======================================================
                # 2.13 — RECOMENDACIONES PRIORITARIAS
                # ======================================================

                Convierte los hallazgos del diagnóstico en acciones concretas y
                priorizadas.

                Cada recomendación debe estar vinculada a un hallazgo concreto.

                Utiliza, cuando corresponda:

                - MANTENER;
                - OPTIMIZAR;
                - INVESTIGAR;
                - EXPERIMENTAR;
                - CORREGIR.

                No introduzcas consejos genéricos.


                # ======================================================
                # 2.14 — EXPERIMENTOS Y PRÓXIMOS PASOS
                # ======================================================

                Convierte las hipótesis relevantes en pruebas destinadas a reducir
                incertidumbre.

                Cada experimento debe responder a una pregunta concreta y permitir
                comparar resultados y tomar una decisión posterior.

                Si los datos no permiten diseñar un experimento sólido, declara la
                limitación en lugar de inventar variables.


                # ======================================================
                # REGLA DE INTEGRACIÓN
                # ======================================================

                El BLOQUE 2 define QUÉ debe contener cada sección.

                Los BLOQUES 3–8 definen CÓMO debe analizarse, diagnosticarse, recomendarse,
                experimentarse y verificarse ese contenido.

                No dupliques en este bloque las reglas detalladas de interpretación.

                
                # ======================================================
                # BLOQUE 3 — REGLAS DE ANÁLISIS
                # ======================================================

                Este bloque define cómo deben interpretarse los datos proporcionados.

                Estas reglas se aplican durante el análisis de las 14 secciones.

                ------------------------------------------------------
                3.1 — FUENTE DE VERDAD
                ------------------------------------------------------

                Los valores proporcionados por Python son la fuente de verdad
                para todo el análisis cuantitativo.

                Utiliza únicamente los datos disponibles.

                No inventes, completes, estimes ni supongas valores ausentes.

                No modifiques:

                - cifras;
                - fechas;
                - posiciones;
                - impresiones;
                - interacciones;
                - engagement;
                - URLs;
                - métricas calculadas por Python.

                Si un dato necesario no está disponible, indícalo como limitación.

                ------------------------------------------------------
                3.2 — SECUENCIA DE ANÁLISIS
                ------------------------------------------------------

                Analiza siguiendo esta secuencia:

                DATO
                → COMPARACIÓN
                → HALLAZGO
                → INTERPRETACIÓN
                → IMPLICACIÓN

                No es necesario mostrar esta secuencia literalmente.

                Debe utilizarse como método de razonamiento.

                No formules primero una conclusión para después buscar datos
                que la justifiquen.

                ------------------------------------------------------
                3.3 — COMPARACIÓN ANTES DE INTERPRETACIÓN
                ------------------------------------------------------

                No interpretes una métrica de forma aislada cuando existan
                otras métricas que permitan contextualizarla.

                Cuando sea posible, compara:

                - valores absolutos;
                - media;
                - mediana;
                - mínimo;
                - máximo;
                - rango;
                - desviación estándar;
                - posiciones relativas;
                - proporciones;
                - grupos de publicaciones;
                - relaciones entre métricas.

                La comparación debe utilizar únicamente referencias
                realmente disponibles o calculables.

                ------------------------------------------------------
                3.4 — MEDIA Y MEDIANA
                ------------------------------------------------------

                Distingue siempre entre:

                MEDIA

                y

                MEDIANA.

                No utilices automáticamente la media como representación
                del comportamiento habitual.

                Cuando la diferencia entre media y mediana sea relevante,
                explica qué implica para la distribución observada.

                No describas una distribución como:

                - normal;
                - equilibrada;
                - simétrica;

                salvo que existan datos suficientes para demostrarlo.

                ------------------------------------------------------
                3.5 — DISTRIBUCIÓN
                ------------------------------------------------------

                Cuando los datos lo permitan, analiza conjuntamente:

                - mínimo;
                - máximo;
                - rango;
                - media;
                - mediana;
                - desviación estándar;
                - proporción de publicaciones por encima o por debajo
                de una referencia;
                - concentración del rendimiento.

                Una desviación elevada no constituye por sí misma
                una debilidad.

                Una diferencia elevada entre media y mediana no constituye
                por sí misma un problema.

                Primero describe la distribución y después interpreta
                su significado.

                ------------------------------------------------------
                3.6 — CÁLCULOS DERIVADOS
                ------------------------------------------------------

                Puedes realizar cálculos derivados cuando aporten
                información relevante y puedan obtenerse exclusivamente
                a partir de datos disponibles.

                Ejemplos:

                - porcentaje de publicaciones que supera la media;
                - peso de un grupo sobre el total;
                - diferencia entre grupos;
                - relación máximo/mediana;
                - relación máximo/mínimo;
                - proporciones de distribución.

                Todo cálculo derivado debe ser matemáticamente coherente
                con los datos de origen.

                No inventes referencias ni objetivos numéricos.

                Si Python ya proporciona una métrica calculada,
                utiliza ese valor en lugar de sustituirlo por una estimación.

                ------------------------------------------------------
                3.7 — ALCANCE
                ------------------------------------------------------

                El alcance se representa mediante las impresiones disponibles.

                Las impresiones indican exposición.

                No equivalen automáticamente a:

                - éxito;
                - calidad;
                - relevancia;
                - interacción;
                - valor profesional;
                - eficacia estratégica.

                Una publicación con muchas impresiones no es automáticamente
                la mejor publicación.

                Una publicación con pocas impresiones no es automáticamente
                una publicación deficiente.

                ------------------------------------------------------
                3.8 — INTERACCIONES
                ------------------------------------------------------

                Las interacciones absolutas representan volumen de interacción.

                Deben distinguirse de:

                - impresiones;
                - engagement.

                Una publicación puede obtener muchas interacciones absolutas
                por tener una gran exposición y, al mismo tiempo, presentar
                un engagement inferior al de otra publicación.

                No confundas volumen con eficiencia.

                ------------------------------------------------------
                3.9 — ENGAGEMENT
                ------------------------------------------------------

                El engagement representa la eficiencia relativa de interacción
                según la metodología proporcionada por Python.

                Si Python utiliza:

                Engagement (%) = Interacciones / Impresiones × 100

                respeta exactamente esa metodología.

                Distingue siempre:

                ALCANCE
                = impresiones.

                VOLUMEN DE INTERACCIÓN
                = interacciones absolutas.

                EFICIENCIA DE INTERACCIÓN
                = engagement.

                Un engagement elevado no demuestra automáticamente:

                - mayor alcance;
                - mayor número absoluto de interacciones;
                - mayor calidad;
                - mayor relevancia;
                - mayor éxito global.

                ------------------------------------------------------
                3.10 — RELACIONES ENTRE MÉTRICAS
                ------------------------------------------------------

                Cuando existan varias métricas relacionadas, analiza cómo
                se comportan conjuntamente.

                Una publicación puede presentar:

                - alto alcance y alta eficiencia;
                - alto alcance y baja eficiencia;
                - bajo alcance y alta eficiencia;
                - bajo alcance y baja eficiencia.

                No es obligatorio que existan todas las combinaciones.

                No las inventes para completar el análisis.

                El objetivo es determinar si las dimensiones observadas
                se mueven conjuntamente o presentan comportamientos diferentes.

                ------------------------------------------------------
                3.11 — HECHOS, INDICIOS E HIPÓTESIS
                ------------------------------------------------------

                Clasifica internamente las conclusiones relevantes en tres niveles:

                HECHO

                Puede afirmarse directamente a partir de los datos.

                INDICIO

                Existe un patrón observable que merece atención,
                pero no existe evidencia suficiente para considerarlo
                una conclusión definitiva.

                HIPÓTESIS

                Es una posible explicación que todavía necesita
                comprobación.

                No presentes una hipótesis como un hecho.

                Cuando corresponda, utiliza formulaciones como:

                "los datos muestran..."

                "se observa..."

                "los datos sugieren..."

                "constituye un indicio..."

                "podría estar relacionado con..."

                "no puede determinarse con los datos disponibles..."

                ------------------------------------------------------
                3.12 — CAUSALIDAD
                ------------------------------------------------------

                Los datos descriptivos permiten identificar comportamientos,
                diferencias y relaciones.

                No demuestran automáticamente sus causas.

                No afirmes que una variable:

                - provocó;
                - causó;
                - generó;
                - produjo;
                - consiguió;

                un determinado resultado salvo que exista evidencia suficiente
                para demostrarlo.

                No atribuyas resultados automáticamente a:

                - tema;
                - formato;
                - horario;
                - hashtags;
                - algoritmo;
                - audiencia;
                - calidad del contenido;
                - llamada a la acción;
                - frecuencia;
                - viralidad.

                Cuando únicamente exista una asociación observable,
                descríbela como tal.

                ------------------------------------------------------
                3.13 — CONTENIDO NO DISPONIBLE
                ------------------------------------------------------

                Las métricas no permiten conocer por sí solas las características
                cualitativas de una publicación.

                Si los datos proporcionados no contienen información sobre
                el contenido, no inventes:

                - tema;
                - formato;
                - tono;
                - horario;
                - hashtags;
                - imágenes;
                - vídeos;
                - CTA;
                - audiencia;
                - intención;
                - calidad;
                - relevancia;
                - motivaciones de los usuarios.

                Una URL puede utilizarse como referencia de la publicación,
                pero no constituye por sí sola evidencia suficiente para
                establecer patrones temáticos o causales.

                ------------------------------------------------------
                3.14 — ESPECIFICIDAD
                ------------------------------------------------------

                Las conclusiones deben referirse a los datos reales de esta cuenta.

                Evita afirmaciones genéricas que podrían aplicarse
                a cualquier perfil de LinkedIn.

                Cuando exista evidencia cuantitativa suficiente,
                utiliza los valores concretos.

                Prefiere:

                "El máximo observado es X y la mediana es Y."

                frente a:

                "Existe una publicación con muchas impresiones."

                ------------------------------------------------------
                3.15 — INCERTIDUMBRE
                ------------------------------------------------------

                Cuando los datos no permitan determinar una cuestión,
                decláralo explícitamente.

                No rellenes las ausencias mediante intuición.

                La ausencia de información debe considerarse una limitación
                analítica y, cuando sea relevante, puede convertirse
                posteriormente en una pregunta de investigación o experimento.

                ------------------------------------------------------
                3.16 — ACTIVIDAD Y RESULTADO
                ------------------------------------------------------

                El número de publicaciones describe actividad.

                Las impresiones e interacciones describen resultados observados.

                No confundas:

                ACTIVIDAD

                con

                RESULTADO

                ni:

                RESULTADO

                con

                EFICACIA ESTRATÉGICA.

                La frecuencia de publicación no debe interpretarse
                automáticamente como una fortaleza o una debilidad.

                Su significado debe analizarse junto con los resultados
                observados.

                ------------------------------------------------------
                3.17 — LENGUAJE ANALÍTICO
                ------------------------------------------------------

                Evita utilizar adjetivos como conclusión cuando exista
                una referencia cuantitativa disponible.

                Evita afirmaciones aisladas como:

                "mucho"

                "poco"

                "alto"

                "bajo"

                "importante"

                "significativo"

                "considerable"

                "elevado"

                "escaso"

                cuando puedan sustituirse por una comparación concreta.

                La precisión cuantitativa tiene prioridad sobre la valoración
                subjetiva.

                ------------------------------------------------------
                3.18 — PRINCIPIO FINAL
                ------------------------------------------------------

                Cada conclusión importante debe poder responder a la pregunta:

                "¿Qué dato permite afirmar esto?"

                Si no existe una respuesta suficiente:

                - reformula la conclusión como indicio;
                - conviértela en hipótesis;
                - o declara que no puede determinarse.

                El objetivo del análisis es describir con precisión
                lo que muestran los datos, interpretar su significado
                sin exceder la evidencia disponible y dejar claramente
                identificadas las cuestiones que todavía deben comprobarse.


                # ======================================================
                # BLOQUE 4 — ANÁLISIS DE LAS 15 PUBLICACIONES
                # ======================================================

                Las publicaciones seleccionadas constituyen una muestra de casos para
                analizar el comportamiento observado de la cuenta.

                La muestra está formada por:

                1. TOP 5 POR IMPRESIONES
                2. BOTTOM 5 POR IMPRESIONES
                3. TOP 5 POR ENGAGEMENT

                Las reglas generales del BLOQUE 3 se aplican a todos los casos.

                Una misma publicación puede aparecer en varios rankings.
                Por ello, la muestra puede contener menos de 15 publicaciones únicas.


                # ------------------------------------------------------
                # 4.1 — DATOS DE CADA PUBLICACIÓN
                # ------------------------------------------------------

                Para cada publicación utiliza, cuando estén disponibles:

                - posición;
                - fecha;
                - impresiones;
                - interacciones;
                - engagement;
                - URL.

                Conserva exactamente los valores proporcionados por Python.

                No modifiques cifras, fechas, posiciones, métricas ni URLs.
                No inventes datos ausentes.


                # ------------------------------------------------------
                # 4.2 — TOP 5 Y BOTTOM 5 POR IMPRESIONES
                # ------------------------------------------------------

                El TOP 5 representa las publicaciones con mayor alcance dentro de
                los datos proporcionados.

                El BOTTOM 5 representa las publicaciones con menor alcance.

                Analiza:

                - diferencias de impresiones entre posiciones;
                - interacciones asociadas;
                - engagement correspondiente;
                - distancia entre los extremos;
                - posibles diferencias entre exposición y eficiencia.

                No interpretes el ranking de impresiones como un ranking general de
                calidad, relevancia o éxito.

                Una publicación con pocas impresiones puede presentar engagement elevado,
                y una publicación con muchas impresiones puede presentar engagement menor.


                # ------------------------------------------------------
                # 4.3 — TOP 5 POR ENGAGEMENT
                # ------------------------------------------------------

                Representa las publicaciones con mayor eficiencia de interacción según
                la metodología proporcionada por Python.

                Analiza:

                - engagement;
                - impresiones asociadas;
                - interacciones absolutas;
                - relación entre eficiencia y exposición;
                - coincidencias con el TOP 5 por impresiones.

                No interpretes automáticamente un engagement elevado como mayor calidad,
                relevancia o éxito global.


                # ------------------------------------------------------
                # 4.4 — ANÁLISIS INDIVIDUAL Y FUNCIÓN DE CADA CASO
                # ------------------------------------------------------

                Interpreta cada publicación exclusivamente a partir de sus métricas.

                Cuando los datos lo permitan, determina si destaca principalmente por:

                - alcance;
                - volumen de interacción;
                - eficiencia;
                - combinación de dimensiones;
                - comportamiento excepcional;
                - comportamiento próximo al de otros casos.

                No es necesario crear una explicación artificialmente diferente para cada
                publicación cuando varias presentan un comportamiento cuantitativamente
                similar.


                # ------------------------------------------------------
                # 4.5 — CRUCE ENTRE RANKINGS
                # ------------------------------------------------------

                Después de analizar los grupos, compáralos entre sí.

                Identifica:

                - publicaciones presentes en varios rankings;
                - publicaciones exclusivas de un ranking;
                - coincidencias entre alto alcance y alto engagement;
                - alto alcance con engagement relativamente inferior;
                - bajo alcance con engagement elevado;
                - bajo alcance con engagement reducido;

                únicamente cuando los datos lo demuestren.

                Si una publicación aparece en varios rankings, utiliza siempre los mismos
                valores para ella.

                La coincidencia entre rankings indica que una publicación destaca en más
                de una dimensión, pero no demuestra por sí misma una causa ni una estrategia
                reproducible.

                Si existe poca o ninguna coincidencia relevante, puede señalarse como
                hallazgo, sin considerarlo automáticamente un problema.


                # ------------------------------------------------------
                # 4.6 — COMPARACIÓN Y REPRESENTATIVIDAD
                # ------------------------------------------------------

                Utiliza valores concretos para comparar las publicaciones y los grupos
                cuando aporten información relevante.

                Prioriza:

                - impresiones;
                - interacciones;
                - engagement;
                - posiciones;
                - diferencias entre dimensiones.

                No utilices medias, promedios u otras referencias que no hayan sido
                calculadas y proporcionadas por Python.

                Las 15 posiciones seleccionadas constituyen una muestra analítica.
                No utilices sus resultados para afirmar automáticamente que un patrón
                caracteriza a todas las publicaciones de la cuenta.


                # ------------------------------------------------------
                # 4.7 — OBJETIVO DEL ANÁLISIS
                # ------------------------------------------------------

                El objetivo no es describir repetitivamente 15 publicaciones.

                Utiliza los casos para identificar diferencias y relaciones entre:

                ALCANCE
                = impresiones.

                VOLUMEN DE INTERACCIÓN
                = interacciones absolutas.

                EFICIENCIA DE INTERACCIÓN
                = engagement.

                El análisis debe avanzar desde:

                PUBLICACIONES
                → COMPARACIÓN
                → PATRONES
                → DIFERENCIAS
                → HALLAZGOS

                No atribuyas causas relacionadas con tema, formato, horario, hashtags,
                contenido, audiencia o algoritmo si esas variables no están disponibles.

                Si los datos no permiten explicar un comportamiento, conviértelo en
                limitación o cuestión pendiente.


                # ======================================================
                # BLOQUE 5 — CONSTRUCCIÓN DEL DIAGNÓSTICO
                # ======================================================

                Integra los hallazgos obtenidos en los bloques anteriores para determinar
                qué comportamiento caracteriza realmente a la cuenta.

                El diagnóstico no debe limitarse a repetir métricas, rankings o publicaciones.
                Debe relacionar:

                ACTIVIDAD
                → RENDIMIENTO
                → RELACIONES ENTRE MÉTRICAS
                → HALLAZGOS
                → INTERPRETACIÓN GLOBAL

                No introduzcas información que no haya aparecido previamente en el análisis.


                # ------------------------------------------------------
                # 5.1 — SÍNTESIS
                # ------------------------------------------------------

                Explica, cuando los datos lo permitan:

                - qué comportamiento caracteriza a la cuenta;
                - qué dimensiones presentan resultados favorables;
                - qué dimensiones presentan limitaciones;
                - qué resultados son excepcionales;
                - qué comportamientos parecen más estables;
                - dónde existe concentración del rendimiento;
                - qué relación existe entre alcance y eficiencia;
                - qué cuestiones permanecen abiertas.

                No repitas mecánicamente las conclusiones anteriores.
                Explica cómo se relacionan entre sí.


                # ------------------------------------------------------
                # 5.2 — FORTALEZAS Y LIMITACIONES
                # ------------------------------------------------------

                Identifica únicamente fortalezas y limitaciones respaldadas por los datos.

                Una fortaleza debe representar un comportamiento favorable observable
                y relevante para la situación actual de la cuenta.

                Una limitación debe incluir:

                1. comportamiento observado;
                2. evidencia que lo respalda;
                3. motivo por el que puede representar una limitación.

                No conviertas automáticamente una diferencia estadística, una anomalía
                o un resultado aislado en una debilidad estructural.

                Si no existe evidencia suficiente para establecer una limitación clara,
                indícalo.


                # ------------------------------------------------------
                # 5.3 — OPORTUNIDADES Y ANOMALÍAS
                # ------------------------------------------------------

                Identifica oportunidades cuando los datos revelen:

                - una fortaleza que pueda desarrollarse;
                - un comportamiento excepcional que merezca investigación;
                - una diferencia relevante entre alcance y eficiencia;
                - una concentración del rendimiento;
                - una hipótesis que pueda comprobarse.

                Identifica anomalías cuando un resultado se aleje claramente del
                comportamiento observado.

                Una anomalía describe una desviación; no implica por sí misma problema,
                causa, debilidad ni éxito estratégico.


                # ------------------------------------------------------
                # 5.4 — INCERTIDUMBRES Y NIVEL DE EVIDENCIA
                # ------------------------------------------------------

                Distingue entre:

                LO QUE LA CUENTA DEMUESTRA

                LO QUE LOS DATOS SUGIEREN

                LO QUE TODAVÍA NECESITA COMPROBACIÓN

                No presentes una hipótesis como hecho ni atribuyas causalidad cuando
                los datos solo muestran una asociación.

                Identifica las incertidumbres cuya resolución podría modificar de forma
                relevante la interpretación o las decisiones posteriores.


                # ------------------------------------------------------
                # 5.5 — PRIORIZACIÓN
                # ------------------------------------------------------

                Prioriza los hallazgos considerando:

                1. fuerza de la evidencia;
                2. magnitud o relevancia del comportamiento;
                3. impacto sobre la interpretación de la cuenta;
                4. posibilidad de obtener aprendizaje mediante nuevas comprobaciones.

                No priorices únicamente por lo llamativo de un resultado.


                # ------------------------------------------------------
                # 5.6 — CONCLUSIONES PRINCIPALES
                # ------------------------------------------------------

                Cuando exista evidencia suficiente, identifica:

                - PRINCIPAL FORTALEZA
                - PRINCIPAL LIMITACIÓN
                - PRINCIPAL OPORTUNIDAD
                - PRINCIPAL ANOMALÍA
                - PRINCIPAL INCERTIDUMBRE

                No es obligatorio completar todos los elementos.

                Si los datos no permiten establecer alguno de ellos, indícalo
                explícitamente en lugar de forzarlo.


                # ------------------------------------------------------
                # 5.7 — PRIORIDAD ESTRATÉGICA
                # ------------------------------------------------------

                Finaliza el diagnóstico estableciendo la prioridad estratégica principal
                de la cuenta.

                Debe expresar qué debería comprenderse, consolidarse o investigarse
                antes de tomar decisiones secundarias.

                No debe convertirse todavía en una lista de acciones.
                Las acciones corresponden al BLOQUE 6.


                # ------------------------------------------------------
                # 5.8 — REGLA FINAL
                # ------------------------------------------------------

                El diagnóstico debe ser específico de esta cuenta y permitir responder:

                ¿QUÉ ESTÁ FUNCIONANDO?

                ¿QUÉ PRESENTA UNA LIMITACIÓN?

                ¿QUÉ ES EXCEPCIONAL?

                ¿QUÉ PARECE ESTABLE?

                ¿QUÉ RELACIÓN EXISTE ENTRE ALCANCE Y EFICIENCIA?

                ¿QUÉ MERECE INVESTIGACIÓN?

                ¿QUÉ NO PODEMOS SABER TODAVÍA?

                ¿CUÁL ES LA PRIORIDAD ESTRATÉGICA?

                Debe avanzar desde:

                DATOS
                → HALLAZGOS
                → RELACIONES
                → DIAGNÓSTICO

                sin introducir recomendaciones ni experimentos.


                # ======================================================
                # BLOQUE 6 — RECOMENDACIONES PRIORITARIAS
                # ======================================================

                Convierte los hallazgos del DIAGNÓSTICO en acciones concretas y
                priorizadas.

                Las recomendaciones deben derivarse exclusivamente del diagnóstico.
                No introduzcas nuevos hallazgos ni consejos generales de LinkedIn.

                La cadena debe ser:

                HALLAZGO
                → EVIDENCIA
                → INTERPRETACIÓN
                → ACCIÓN


                # ------------------------------------------------------
                # 6.1 — DERIVACIÓN Y PRIORIDAD
                # ------------------------------------------------------

                Cada recomendación debe estar vinculada a uno o varios elementos
                del diagnóstico:

                - fortaleza;
                - limitación;
                - oportunidad;
                - anomalía;
                - incertidumbre.

                Prioriza según:

                1. evidencia disponible;
                2. relevancia estratégica;
                3. relación con los hallazgos principales;
                4. viabilidad de ejecución;
                5. capacidad de generar aprendizaje o mejora.

                Utiliza:

                ALTA
                MEDIA
                BAJA

                La prioridad representa la importancia de actuar, no la magnitud
                aislada de una métrica ni la predicción de éxito.


                # ------------------------------------------------------
                # 6.2 — NÚMERO Y TIPOS
                # ------------------------------------------------------

                Presenta preferentemente entre 3 y 5 recomendaciones.

                No es obligatorio alcanzar ese número si los datos solo permiten
                formular menos acciones sólidas.

                Clasifica cada recomendación como:

                MANTENER
                OPTIMIZAR
                INVESTIGAR
                EXPERIMENTAR
                CORREGIR

                Utiliza únicamente la categoría que corresponda al hallazgo.

                No conviertas automáticamente una anomalía, una métrica extrema
                o una diferencia estadística en una acción correctiva.


                # ------------------------------------------------------
                # 6.3 — ESTRUCTURA
                # ------------------------------------------------------

                Cada recomendación debe contener:

                - PRIORIDAD
                - TIPO
                - HALLAZGO
                - EVIDENCIA
                - INTERPRETACIÓN
                - ACCIÓN CONCRETA
                - CÓMO COMPROBARLA

                La evidencia debe utilizar cifras proporcionadas por Python o cálculos
                derivados legítimamente de ellas.

                La interpretación debe distinguir entre lo que sabemos y lo que
                todavía no sabemos.


                # ------------------------------------------------------
                # 6.4 — ACCIÓN CONCRETA
                # ------------------------------------------------------

                La acción debe poder ejecutarse realmente y explicar:

                - qué hacer;
                - sobre qué dimensión actuar;
                - con qué objetivo;
                - y, cuando sea posible, cómo ejecutarlo.

                Evita consejos genéricos como:

                - publicar más;
                - ser constante;
                - mejorar el contenido;
                - hacer networking;
                - trabajar la marca personal.

                Una recomendación debe ser específica de esta cuenta y estar vinculada
                a un comportamiento observado.


                # ------------------------------------------------------
                # 6.5 — INCERTIDUMBRE, FORTALEZAS Y ANOMALÍAS
                # ------------------------------------------------------

                Una recomendación puede orientarse a mantener o desarrollar una
                fortaleza, investigar un comportamiento excepcional o reducir una
                incertidumbre.

                Una anomalía no implica automáticamente que deba corregirse.

                Cuando falte información para determinar una causa o diseñar una acción,
                la recomendación puede consistir en investigar, observar, recopilar
                información o comparar resultados.

                No presentes como certeza una explicación que el diagnóstico haya
                identificado como hipótesis.


                # ------------------------------------------------------
                # 6.6 — ALCANCE, INTERACCIONES Y ENGAGEMENT
                # ------------------------------------------------------

                Cuando una recomendación se refiera al rendimiento de publicaciones,
                distingue siempre:

                ALCANCE
                = impresiones.

                VOLUMEN DE INTERACCIÓN
                = interacciones absolutas.

                EFICIENCIA DE INTERACCIÓN
                = engagement.

                No supongas que mejorar una dimensión producirá automáticamente
                una mejora en las demás.


                # ------------------------------------------------------
                # 6.7 — RELACIÓN CON LOS EXPERIMENTOS
                # ------------------------------------------------------

                Una recomendación puede proponer experimentar, pero el diseño detallado
                corresponde al BLOQUE 7.

                No desarrolles aquí:

                - hipótesis completas;
                - variables de control;
                - duración;
                - criterios de éxito;
                - diseño experimental detallado.


                # ------------------------------------------------------
                # 6.8 — ORDEN Y REGLA FINAL
                # ------------------------------------------------------

                Presenta las recomendaciones de mayor a menor prioridad.

                No fuerces acciones cuando el análisis no las justifique.

                Si la evidencia solo permite "mantener y observar" o "obtener más datos",
                esa puede ser la recomendación adecuada.

                El resultado debe permitir pasar directamente de:

                DIAGNÓSTICO
                → PRIORIDAD
                → ACCIÓN

                sin introducir información nueva ni consejos genéricos.


                # ======================================================
                # BLOQUE 7 — EXPERIMENTOS Y PRÓXIMOS PASOS
                # ======================================================

                Este bloque define cómo convertir las hipótesis identificadas durante
                el análisis en experimentos concretos.

                Su función es REDUCIR INCERTIDUMBRE.

                No debe utilizarse para repetir el diagnóstico.
                No debe utilizarse para generar recomendaciones generales.
                No debe utilizarse para inventar características de las publicaciones.
                No debe utilizarse para afirmar causalidad.

                Los experimentos deben surgir únicamente de:

                DATOS OBSERVADOS
                → HALLAZGO
                → HIPÓTESIS
                → EXPERIMENTO
                → APRENDIZAJE
                → DECISIÓN

                # ------------------------------------------------------
                # 7.1 — CUÁNDO PROPONER UN EXPERIMENTO
                # ------------------------------------------------------

                Propón un experimento únicamente cuando exista una hipótesis
                razonable derivada de los datos disponibles.

                Una hipótesis debe expresar algo que los datos actuales sugieren,
                pero que todavía no permiten demostrar.

                Ejemplo:

                "Las publicaciones con mayor alcance podrían presentar un patrón
                que merezca ser investigado."

                Esto puede convertirse en una hipótesis de trabajo.

                No debe convertirse en:

                "Las publicaciones con determinada característica generan más alcance"

                si esa característica no está presente en los datos.

                # ------------------------------------------------------
                # 7.2 — NO INVENTAR VARIABLES
                # ------------------------------------------------------

                Solo pueden utilizarse variables que:

                1. estén disponibles en los datos actuales; o
                2. puedan observarse y registrarse explícitamente durante el experimento.

                No inventes información sobre:

                - temas;
                - formatos;
                - horarios;
                - hashtags;
                - imágenes;
                - vídeos;
                - títulos;
                - llamadas a la acción;
                - audiencia;
                - estructura del contenido;
                - comportamiento del algoritmo;

                si esas variables no están disponibles.

                Si una hipótesis requiere información que actualmente no existe,
                el experimento debe plantearse como una propuesta para recopilar
                esa información.

                # ------------------------------------------------------
                # 7.3 — ESTRUCTURA DEL EXPERIMENTO
                # ------------------------------------------------------

                Cuando los datos permitan definirlo, cada experimento debe contener:

                - HIPÓTESIS;
                - PREGUNTA QUE SE QUIERE RESPONDER;
                - VARIABLE A OBSERVAR;
                - QUÉ SE MODIFICA;
                - QUÉ SE MANTIENE CONSTANTE;
                - MÉTRICA PRINCIPAL;
                - MÉTRICAS SECUNDARIAS;
                - REFERENCIA DE COMPARACIÓN;
                - DURACIÓN O NÚMERO DE PUBLICACIONES;
                - CRITERIO DE EVALUACIÓN;
                - DECISIÓN POSTERIOR.

                Si no existe una hipótesis suficientemente respaldada por los datos,
                no debe generarse un experimento únicamente para completar la sección.

                En ese caso, debe indicarse que no existe evidencia suficiente para
                plantear una prueba específica y señalar qué información adicional
                sería necesaria para poder diseñarla.

                # ------------------------------------------------------
                # 7.4 — REFERENCIA DE COMPARACIÓN
                # ------------------------------------------------------

                Los resultados del experimento deben compararse con una referencia
                disponible.

                Cuando proceda, utilizar:

                - mediana histórica;
                - media histórica;
                - engagement histórico;
                - resultados de publicaciones comparables;
                - distribución histórica;
                - otros valores proporcionados por Python.

                No inventes objetivos numéricos.

                No establezcas arbitrariamente que un experimento será exitoso
                si supera una cifra que no tiene fundamento en los datos.

                # ------------------------------------------------------
                # 7.5 — MÉTRICAS
                # ------------------------------------------------------

                Selecciona las métricas en función de la pregunta que el experimento
                pretende responder.

                Distingue siempre entre:

                ALCANCE
                = impresiones.

                VOLUMEN DE INTERACCIÓN
                = interacciones absolutas.

                EFICIENCIA DE INTERACCIÓN
                = engagement.

                No utilices una métrica como sustituto de otra.

                Un experimento destinado a estudiar alcance no debe evaluarse
                exclusivamente mediante engagement.

                Un experimento destinado a estudiar eficiencia de interacción
                no debe evaluarse exclusivamente mediante impresiones.

                Cuando sea relevante, utiliza conjuntamente las dimensiones disponibles.

                # ------------------------------------------------------
                # 7.6 — CONTROL DE VARIABLES
                # ------------------------------------------------------

                Cuando sea posible, modifica una variable relevante y mantén
                constantes las demás condiciones observables.

                El objetivo es aumentar la capacidad de interpretar el resultado.

                Sin embargo, no afirmes que un experimento demuestra causalidad
                si su diseño no permite establecerla.

                Utiliza expresiones como:

                - "permitirá observar";
                - "permitirá comparar";
                - "aportará evidencia";
                - "ayudará a comprobar";
                - "permitirá reducir la incertidumbre".

                # ------------------------------------------------------
                # 7.7 — NÚMERO DE EXPERIMENTOS
                # ------------------------------------------------------

                No existe obligación de generar un número determinado de experimentos.

                Propón únicamente los que tengan una pregunta útil detrás.

                Es preferible:

                2 experimentos sólidos

                que:

                5 experimentos genéricos.

                Si no existe ninguna hipótesis suficientemente respaldada,
                indícalo.

                No inventes experimentos para completar la sección.

                # ------------------------------------------------------
                # 7.8 — PRIORIDAD
                # ------------------------------------------------------

                Cuando existan varios experimentos, ordénalos según:

                1. relevancia de la incertidumbre;
                2. evidencia disponible;
                3. facilidad de ejecución;
                4. capacidad para generar aprendizaje;
                5. utilidad de la decisión posterior.

                La prioridad no representa una predicción de éxito.

                Representa el valor potencial del aprendizaje.

                # ------------------------------------------------------
                # 7.9 — CRITERIO DE EVALUACIÓN
                # ------------------------------------------------------

                Cada experimento debe definir qué se observará al finalizar.

                El criterio debe relacionarse directamente con la pregunta inicial.

                Evita criterios vagos como:

                - "que funcione mejor";
                - "tener mejores resultados";
                - "conseguir más engagement";
                - "mejorar el alcance";

                sin especificar respecto a qué referencia se realizará la comparación.

                Cuando los datos permitan una comparación cuantitativa,
                utilízala.

                Cuando no permitan establecer un umbral,
                indica que el resultado será interpretado de forma comparativa
                respecto al comportamiento histórico disponible.

                # ------------------------------------------------------
                # 7.10 — APRENDIZAJE
                # ------------------------------------------------------

                El objetivo de un experimento no es simplemente determinar
                si una publicación obtiene un resultado superior.

                Debe permitir responder:

                ¿QUÉ HEMOS APRENDIDO?

                La interpretación posterior debe distinguir entre:

                - resultado observado;
                - diferencia respecto a la referencia;
                - posible interpretación;
                - incertidumbre restante;
                - decisión siguiente.

                No convertir automáticamente un resultado favorable
                en una regla general.

                # ------------------------------------------------------
                # 7.11 — DECISIÓN POSTERIOR
                # ------------------------------------------------------

                Siempre que sea posible, el experimento debe terminar con
                una decisión potencial.

                Ejemplos:

                - mantener el comportamiento;
                - repetir la prueba;
                - ampliar la muestra;
                - investigar otra variable;
                - descartar la hipótesis;
                - reformular la hipótesis;
                - recopilar datos adicionales.

                La decisión debe depender del resultado observado.

                No debe estar predeterminada como éxito antes de realizar
                el experimento.

                # ------------------------------------------------------
                # 7.12 — LIMITACIONES
                # ------------------------------------------------------

                Si los datos actuales no permiten diseñar un experimento
                con suficiente rigor, no inventes variables ni condiciones.

                Explica brevemente:

                - qué información falta;
                - por qué es necesaria;
                - qué debería registrarse en futuras publicaciones;
                - qué pregunta permitiría responder.

                La falta de datos no debe convertirse artificialmente
                en una recomendación.

                # ------------------------------------------------------
                # 7.13 — REGLA FINAL
                # ------------------------------------------------------

                Un experimento válido debe cumplir esta cadena:

                HALLAZGO
                → HIPÓTESIS
                → PREGUNTA
                → PRUEBA
                → MÉTRICA
                → COMPARACIÓN
                → APRENDIZAJE
                → DECISIÓN

                Si no puede construirse esta cadena con la información disponible,
                no debe inventarse el experimento.

                El objetivo de esta sección no es producir más consejos.

                Es transformar las incertidumbres relevantes de la cuenta
                en oportunidades concretas de aprendizaje.

                # ======================================================
                # BLOQUE 8 — AUDITORÍA DEL ANÁLISIS
                # ======================================================

                Realiza una comprobación final del análisis antes de enviarlo al módulo
                de generación HTML.

                La auditoría NO realiza un nuevo análisis estratégico, no genera nuevas
                recomendaciones ni experimentos, no modifica la arquitectura y no añade
                información que no esté respaldada por los datos disponibles.

                La fuente de verdad continúa siendo:

                DATOS ORIGINALES DE PYTHON
                +
                RESULTADOS DEL ANÁLISIS


                # ------------------------------------------------------
                # 8.1 — INTEGRIDAD DE LOS DATOS
                # ------------------------------------------------------

                Comprueba que las cifras, fechas, posiciones, métricas y URLs coinciden
                con los datos originales proporcionados por Python.

                Comprueba especialmente los tres rankings:

                - TOP 5 POR IMPRESIONES;
                - BOTTOM 5 POR IMPRESIONES;
                - TOP 5 POR ENGAGEMENT.

                Si una publicación aparece en varios rankings, sus datos deben ser
                coherentes en todas sus apariciones.

                No inventes, completes ni estimes datos ausentes.


                # ------------------------------------------------------
                # 8.2 — INTEGRIDAD ESTRUCTURAL
                # ------------------------------------------------------

                Comprueba que existen exactamente las 14 secciones obligatorias,
                en el orden establecido en el BLOQUE 1.

                No añadas, elimines, combines ni dividas secciones principales.

                Si una sección está limitada por falta de datos, debe conservarse
                e indicar la limitación correspondiente.


                # ------------------------------------------------------
                # 8.3 — CONSISTENCIA ANALÍTICA
                # ------------------------------------------------------

                Comprueba que no existan contradicciones entre:

                - métricas;
                - rankings;
                - distribución;
                - alcance;
                - engagement;
                - cruce entre métricas;
                - diagnóstico;
                - recomendaciones;
                - experimentos.

                La cadena lógica debe mantenerse:

                DATOS
                → HALLAZGOS
                → DIAGNÓSTICO
                → RECOMENDACIONES
                → EXPERIMENTOS.


                # ------------------------------------------------------
                # 8.4 — NIVEL DE CERTEZA
                # ------------------------------------------------------

                Comprueba que las afirmaciones respetan la evidencia disponible.

                No conviertas:

                - indicios en hechos;
                - hipótesis en conclusiones;
                - asociaciones en causalidad.

                Reformula o elimina cualquier afirmación que exceda lo que permiten
                demostrar los datos.


                # ------------------------------------------------------
                # 8.5 — NO INVENCIÓN
                # ------------------------------------------------------

                Comprueba que no se hayan introducido características no disponibles
                sobre las publicaciones o sus resultados.

                No deben aparecer como hechos datos sobre:

                - temas;
                - formatos;
                - horarios;
                - hashtags;
                - imágenes;
                - vídeos;
                - títulos;
                - audiencia;
                - causas;
                - algoritmo;
                - calidad;
                - intención;
                - características del contenido;

                cuando no estén respaldados por la información disponible.

                Si una conclusión requiere información inexistente, debe mantenerse como
                hipótesis o limitación.


                # ------------------------------------------------------
                # 8.6 — NO REPETICIÓN
                # ------------------------------------------------------

                Comprueba que las secciones posteriores no se limiten a repetir
                mecánicamente las anteriores.

                Cada sección debe cumplir la función definida en el BLOQUE 2 y aportar
                un avance en la interpretación:

                DATOS
                → ANÁLISIS
                → CRUCE
                → DIAGNÓSTICO
                → ACCIÓN
                → EXPERIMENTACIÓN.


                # ------------------------------------------------------
                # 8.7 — CORRECCIÓN FINAL
                # ------------------------------------------------------

                Si detectas un error, corrígelo utilizando exclusivamente la fuente
                de verdad disponible.

                No introduzcas información nueva para compensar una corrección.

                Si un elemento no puede verificarse, trátalo como no demostrado.


                # ------------------------------------------------------
                # 8.8 — RESULTADO
                # ------------------------------------------------------

                El resultado final debe ser:

                - coherente;
                - verificable;
                - específico de la cuenta;
                - consistente con los datos;
                - sin información inventada;
                - sin causalidad injustificada;
                - sin contradicciones;
                - sin duplicaciones innecesarias.

                Una vez superada esta comprobación, el contenido queda preparado
                para el Módulo 9.

                # ======================================================
                # MÓDULO 9 — PREPARACIÓN DEL CONTENIDO PARA MAQUETACIÓN
                # ======================================================

                ## 9.1 — FUNCIÓN Y FUENTE DE VERDAD

                Este módulo recibe el análisis auditado y validado por el Módulo 8.

                Su función es preparar el contenido final del informe para que Python
                pueda encargarse posteriormente de su maquetación visual.

                Flujo:

                MÓDULOS 0–7 → ANÁLISIS
                MÓDULO 8 → AUDITORÍA
                MÓDULO 9 → CONTENIDO ESTRUCTURADO
                PYTHON → MAQUETACIÓN HTML + CSS → PDF

                El Módulo 9 NO debe diseñar el informe.

                El Módulo 9 NO debe generar CSS.

                El Módulo 9 NO debe decidir colores, tipografías, tamaños, márgenes,
                espaciados, tarjetas, bordes, fondos ni composición visual.

                La presentación visual será responsabilidad exclusiva de Python.

                El contenido auditado por el Módulo 8 continúa siendo la FUENTE DE VERDAD.

                ---

                ## 9.2 — INTEGRIDAD DEL CONTENIDO

                No inventar, completar, estimar ni modificar información.

                Conservar exactamente:

                - cifras;
                - fechas;
                - posiciones;
                - impresiones;
                - interacciones;
                - engagement;
                - URLs;
                - conclusiones;
                - diagnóstico;
                - recomendaciones;
                - hipótesis;
                - experimentos;
                - nivel de certeza.

                No introducir nuevas interpretaciones.

                No introducir nuevas recomendaciones.

                No introducir nuevos experimentos.

                No introducir causalidad que no esté presente en el análisis auditado.

                ---

                ## 9.3 — ESTRUCTURA OBLIGATORIA

                El contenido debe conservar exactamente las 14 secciones establecidas
                en el BLOQUE 1 y en el mismo orden.

                Las 14 secciones son:

                1. RESUMEN EJECUTIVO
                2. ESTADO ACTUAL DEL PERFIL
                3. RADIOGRAFÍA CUANTITATIVA
                4. DISTRIBUCIÓN DEL RENDIMIENTO
                5. FRECUENCIA Y ACTIVIDAD
                6. ANÁLISIS DEL ALCANCE
                7. ANÁLISIS DEL ENGAGEMENT
                8. TOP 5 PUBLICACIONES POR IMPRESIONES
                9. BOTTOM 5 PUBLICACIONES POR IMPRESIONES
                10. TOP 5 PUBLICACIONES POR ENGAGEMENT
                11. CRUCE ENTRE ALCANCE Y ENGAGEMENT
                12. DIAGNÓSTICO ESTRATÉGICO
                13. RECOMENDACIONES PRIORITARIAS
                14. EXPERIMENTOS Y PRÓXIMOS PASOS

                No añadir, eliminar, combinar ni dividir secciones.

                Si una sección está limitada por falta de datos, debe conservarse y
                registrar la limitación correspondiente.

                ---

                ## 9.4 — FORMATO DE SALIDA

                La respuesta debe ser exclusivamente un objeto JSON válido.

                No utilizar:

                - Markdown;
                - bloques de código;
                - explicaciones antes del JSON;
                - explicaciones después del JSON;
                - HTML;
                - CSS.

                El JSON debe contener exactamente estas claves principales:

                metadata
                sections

                La estructura conceptual será:

                metadata → objeto
                sections → lista de exactamente 14 elementos

                La clave "metadata" debe conservar únicamente los datos oficiales
                proporcionados por Python.

                La clave "sections" debe contener exactamente 14 elementos,
                uno por cada sección obligatoria y en el orden establecido.

                ---

                ## 9.5 — ESTRUCTURA DE CADA SECCIÓN
                

                Cada elemento de "sections" debe contener:

                number → número de sección
                title → nombre exacto de la sección
                content → lista de elementos analíticos

                "number" debe corresponder al número real de la sección.

                "title" debe conservar exactamente el nombre establecido.

                "content" debe contener los elementos analíticos necesarios para
                presentar esa sección.

                No crear elementos visuales dentro del JSON.

                ---

                ## 9.6 — TIPOS DE CONTENIDO

                Cuando sea necesario, utilizar únicamente estructuras de contenido
                claras y reutilizables.

                Tipos permitidos:

                "text"
                "metric"
                "table"
                "insight"
                "diagnosis"
                "recommendation"
                "experiment"
                "limitation"

                Cada elemento debe indicar su tipo.

                Para elementos de tipo "text":

                Campos:
                - type
                - text

                Para elementos de tipo "metric":

                Campos:
                - type
                - label
                - value

                Para elementos de tipo "table":

                Campos:
                - type
                - columns
                - rows

                Para elementos de tipo "insight":

                Campos:
                - type
                - label
                - text

                Para elementos de tipo "diagnosis":

                Campos:
                - type
                - categoría correspondiente
                - contenido del diagnóstico

                Para elementos de tipo "recommendation":

                Campos disponibles:
                - type
                - priority
                - finding
                - evidence
                - interpretation
                - action
                - verification

                Para elementos de tipo "experiment":

                Campos disponibles:
                - type
                - hypothesis
                - variable
                - change
                - metric
                - reference
                - success_criterion
                - subsequent_decision

                Para elementos de tipo "limitation":

                Campos:
                - type
                - text

                Utilizar únicamente los campos que correspondan al contenido
                realmente existente.

                No crear campos vacíos únicamente para completar una estructura.

                No introducir estructuras visuales, HTML, CSS ni instrucciones
                de diseño dentro del JSON.

                ---

                ## 9.7 — PUBLICACIONES Y TABLAS

                Las secciones 8, 9 y 10 deben conservar todos los registros proporcionados
                por Python.

                Las columnas deben conservar los datos reales disponibles.

                No eliminar publicaciones.

                No resumir una tabla utilizando "etc.", "más publicaciones" ni
                ningún placeholder.

                No modificar, redondear ni sustituir los valores.

                Las URLs deben conservarse exactamente.

                ---

                ## 9.8 — METADATOS

                Los metadatos procedentes de Python deben conservarse sin modificación.

                Cuando estén disponibles pueden incluir:

                - usuario;
                - periodo;
                - fecha de inicio;
                - fecha de fin;
                - fecha de generación;
                - estado;
                - versión.

                No inventar metadatos ausentes.

                ---

                ## 9.9 — RESPONSABILIDAD DE PYTHON

                Python será responsable exclusivamente de la presentación visual posterior.

                Python determinará:

                - CSS;
                - colores;
                - tipografías;
                - tamaños;
                - márgenes;
                - espaciados;
                - tablas;
                - bloques;
                - jerarquía visual;
                - saltos de página;
                - adaptación a PDF.

                La IA no debe incluir ninguna instrucción visual dentro del contenido.

                ---

                ## 9.10 — COMPROBACIÓN FINAL

                Antes de devolver la respuesta, comprobar:

                1. El resultado es JSON válido.
                2. Existen exactamente las claves principales "metadata" y "sections".
                3. Existen exactamente 14 secciones.
                4. Las 14 secciones están en el orden establecido.
                5. Los nombres de las secciones son exactos.
                6. Los datos coinciden con la información auditada.
                7. Las tablas contienen todos los registros disponibles.
                8. Las URLs no han sido modificadas.
                9. No existen datos inventados.
                10. No existe causalidad nueva.
                11. No existen recomendaciones nuevas.
                12. No existen experimentos nuevos.
                13. No existe HTML.
                14. No existe CSS.
                15. No existe información visual o de diseño.

                # ======================================================
                # FIN DEL MÓDULO 9
                # ======================================================

                """
                    
                st.write("===== CONTROL DE TAMAÑO DEL PROMPT =====")

                st.write(
                    "system_prompt:",
                    len(system_prompt),
                    "caracteres"
                )

                st.write(
                    "analytics_text:",
                    len(analytics_text),
                    "caracteres"
                )

                st.write(
                    "ssi_text:",
                    len(ssi_text),
                    "caracteres"
                )

                st.write(
                    "sector_real:",
                    len(sector_real),
                    "caracteres"
                )

                st.write(
                    "intereses_real:",
                    len(intereses_real),
                    "caracteres"
                )

                st.write(
                    "TOTAL APROX. CARACTERES:",
                    len(system_prompt)
                    + len(analytics_text)
                    + len(ssi_text)
                    + len(sector_real)
                    + len(intereses_real)
                )

                st.write(
                    "TOTAL APROX. TOKENS:",
                    (
                        len(system_prompt)
                        + len(analytics_text)
                        + len(ssi_text)
                        + len(sector_real)
                        + len(intereses_real)
                    ) // 4
                )
                               
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"""

                DATOS OFICIALES DE IDENTIFICACIÓN DEL INFORME

                USUARIO: {report_metadata["usuario"]}
                PERIODO: {report_metadata["periodo"]}
                FECHA DE INICIO: {report_metadata["fecha_inicio"]}
                FECHA DE FIN: {report_metadata["fecha_fin"]}
                FECHA DE GENERACIÓN: {report_metadata["fecha_generacion"]}
                ESTADO: {report_metadata["estado"]}

                REGLA DE METADATOS:

                Los datos anteriores proceden directamente de Python.
                Utilízalos para identificar y encabezar el informe.
                No los modifiques, recalcules ni interpretes.

                DATOS ESTRATÉGICOS INTRODUCIDOS POR EL USUARIO

                Sector / Ecosistema Profesional:

                {sector_real}

                Núcleos de Contenido Target:

                {intereses_real}


                DATOS SSI EXTRAÍDOS DE LA CAPTURA DE LINKEDIN

                {ssi_text}

                REGLAS PARA EL USO DE LOS DATOS SSI:

                - Utiliza exclusivamente los valores SSI proporcionados arriba.
                - Estos valores ya han sido extraídos previamente de la captura de LinkedIn.
                - NO vuelvas a intentar leer ni interpretar la imagen.
                - NO inventes puntuaciones que no aparezcan en los datos proporcionados.
                - NO sustituyas los valores SSI por estimaciones.
                - Cuando hagas referencia al SSI, utiliza los valores exactos proporcionados.
                - Puedes comparar las cuatro dimensiones entre sí para identificar cuáles presentan
                mayor o menor puntuación.
                - El SSI TOTAL y las cuatro dimensiones deben considerarse datos independientes
                de las métricas de publicaciones calculadas por Python.
                - No confundas impresiones, interacciones o engagement con puntuaciones SSI.
                - No utilices el número de publicaciones como indicador directo de experiencia
                avanzada en LinkedIn.


                DATOS DE RENDIMIENTO CALCULADOS POR PYTHON

                {analytics_text}

                # ======================================================
                # CRITERIO DE ANÁLISIS DE PUBLICACIONES
                # ======================================================

                Los rankings TOP 5 POR IMPRESIONES, BOTTOM 5 POR IMPRESIONES
                y TOP 5 POR ENGAGEMENT contienen datos reales calculados por Python.

                Utiliza estos datos explícitamente.

                REGLAS:

                - IMPRESIONES = alcance observado.
                - INTERACCIONES = volumen absoluto de interacción.
                - ENGAGEMENT = eficiencia relativa de interacción según la fórmula
                proporcionada por Python.

                No confundas estas tres dimensiones.

                Conserva exactamente:

                - fechas;
                - impresiones;
                - interacciones;
                - engagement;
                - URLs.

                No alteres, redondees ni sustituyas valores.

                No inventes datos ausentes.

                No inventes contenido, temas, formatos, horarios, hashtags,
                audiencia o causas de rendimiento a partir de las métricas o URLs.

                El TOP 5 POR IMPRESIONES representa alcance.

                El BOTTOM 5 POR IMPRESIONES representa el extremo inferior
                de la distribución del alcance.

                El TOP 5 POR ENGAGEMENT representa eficiencia relativa
                de interacción.

                Cuando una publicación aparezca en varios rankings, puede señalarse.

                Analiza conjuntamente impresiones, interacciones y engagement
                cuando resulte relevante.

                No determines que una publicación es "mejor" únicamente por:

                - mayor alcance;
                - mayor engagement;
                - mayor número de interacciones.

                Explica qué dimensión destaca y qué muestran conjuntamente
                las métricas.

                No utilices "media", "promedio", "engagement medio", "alcance medio"
                o equivalentes salvo que Python haya proporcionado ese valor.

                No derives métricas globales de los rankings parciales salvo que
                puedan calcularse legítimamente a partir de datos disponibles.

                No utilices el número de publicaciones como indicador directo
                de experiencia avanzada en LinkedIn.
                """
                
                                },
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=6000
                )
                
                # --------------------------------------------------
                # RECEPCIÓN DEL JSON DEL MÓDULO 9
                # --------------------------------------------------

                analysis_json_text = response.choices[0].message.content

                try:

                    report_data = json.loads(analysis_json_text)

                except json.JSONDecodeError as e:

                    st.error(
                        f"El Módulo 9 no devolvió un JSON válido: {e}"
                    )

                    st.code(
                        analysis_json_text[:5000]
                    )

                    st.stop()


                # --------------------------------------------------
                # VALIDACIÓN DEL JSON DEL MÓDULO 9
                # --------------------------------------------------

                try:

                    analysis_json = json.loads(analysis_json_text)

                    # Comprobar estructura principal
                    if not isinstance(analysis_json, dict):

                        st.error(
                            "El Módulo 9 no ha devuelto un objeto JSON."
                        )

                        st.stop()

                    if "metadata" not in analysis_json:

                        st.error(
                            "El JSON no contiene la clave 'metadata'."
                        )

                        st.stop()

                    if "sections" not in analysis_json:

                        st.error(
                            "El JSON no contiene la clave 'sections'."
                        )

                        st.stop()

                    # --------------------------------------------------
                    # COMPROBAR LAS 14 SECCIONES
                    # --------------------------------------------------

                    sections = analysis_json["sections"]

                    if not isinstance(sections, list):

                        st.error(
                            "La clave 'sections' no contiene una lista."
                        )

                        st.stop()

                    if len(sections) != 14:

                        st.error(
                            f"El Módulo 9 ha devuelto {len(sections)} "
                            f"secciones en lugar de 14."
                        )

                        st.stop()

                    st.success(
                        "✅ JSON recibido correctamente: metadata + 14 secciones."
                    )

                except json.JSONDecodeError as e:

                    st.error(
                        f"❌ El Módulo 9 no devolvió un JSON válido: {e}"
                    )

                    st.code(
                        analysis_json_text
                    )

                    st.stop()

                print("\n===== CSS JUSTO ANTES DE generar_html =====")

                print("Longitud:", len(CSS_INFORME))
                print("Barras invertidas:", CSS_INFORME.count("\\"))

                print(repr(CSS_INFORME[:500]))

                print("===== FIN CSS JUSTO ANTES =====")

                print("===== PRUEBA REAL DE CARACTERES =====")

                print("Primeros caracteres:")
                print([ord(c) for c in CSS_INFORME[:30]])

                print("Texto real:")
                print(CSS_INFORME[:100])

                print("Número real de \\:")
                print(CSS_INFORME.count("\\"))

                print("Número de :")
                print(CSS_INFORME.count(":"))

                print("Número de /:")
                print(CSS_INFORME.count("/"))

                print("Número de *:")
                print(CSS_INFORME.count("*"))

                print("===== FIN PRUEBA =====")

                print(
                    "¿Empieza realmente por :root?",
                    CSS_INFORME.lstrip().startswith(":root")
                )

                print(
                    "¿Contiene realmente /* ?",
                    "/*" in CSS_INFORME
                )

                print(
                    "¿Contiene realmente * { ?",
                    "* {" in CSS_INFORME
                )

                print("===== PRUEBA REAL =====")

                css = CSS_INFORME

                print("BACKSLASH:", css.count("\\"))
                print("ASTERISCO:", css.count("*"))
                print("DOS PUNTOS:", css.count(":"))
                print("BARRA:", css.count("/"))

                print("START ROOT:", css.lstrip().startswith(":root"))
                print("HAS COMMENT:", "/*" in css)
                print("HAS UNIVERSAL:", "* {" in css)

                print("===== FIN =====")

                # ======================================================
                # GENERACIÓN DEL HTML
                # ======================================================

                html_content = generar_html(analysis_json)

                # ======================================================
                # DIAGNÓSTICO DEFINITIVO — CSS DENTRO DEL HTML
                # ======================================================

                inicio_style = html_content.find("<style>")
                fin_style = html_content.find("</style>")

                css_html = html_content[inicio_style:fin_style]

                print("===== CSS DENTRO DE HTML =====")
                print(repr(css_html[:1500]))
                print("===== FIN CSS DENTRO DE HTML =====")

                print("¿HTML contiene \\\\* ?", "\\*" in css_html)
                print("¿HTML contiene \\\\-- ?", "\\--" in css_html)
                print("¿HTML contiene \\\\: ?", "\\:" in css_html)
                print("¿HTML contiene \\\\/ ?", "\\/" in css_html)

                print("===== COMPARACIÓN CSS / HTML =====")

                print("CSS_INFORME:")
                print(repr(CSS_INFORME[:500]))

                print("\nHTML:")
                print(repr(css_html[:500]))

                print("\n¿CSS exactamente igual?")
                print(CSS_INFORME.strip() in css_html)

                st.success(
                    "✅ HTML generado correctamente."
                )

                st.markdown(
                    "### Vista Previa del Informe Ejecutivo"
                )

                st.write("ANCHO DEL CONTENEDOR DE PREVISUALIZACIÓN:")

                #st.components.v1.html(
                    #html_content,
                    #height=900,
                    #scrolling=True
                #)
                st.html(
                    html_content
                )

                # ------------------------------------------------------
                # HTML GENERADO — INSPECCIÓN
                # ------------------------------------------------------

                with st.expander(
                    "🔎 Ver HTML generado"
                ):

                    st.code(
                        html_content,
                        language="html"
                    )


                # ------------------------------------------------------
                # DESCARGAR HTML
                # ------------------------------------------------------

                st.download_button(
                    label="📄 Descargar HTML generado",
                    data=html_content,
                    file_name="Auditoria_LinkedIn_Preview.html",
                    mime="text/html",
                    key="descargar_html_generado"
                )


                # ------------------------------------------------------
                # CONTROL DEL JSON
                # ------------------------------------------------------

                with st.expander(
                    "🧠 Ver JSON estructurado recibido"
                ):

                    st.json(
                        analysis_json
                    )


                # ======================================================
                # GENERACIÓN DEL PDF — GOOGLE CHROME
                # ======================================================

                pdf_buffer = io.BytesIO()

                try:

                    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

                    # Crear archivos temporales
                    with tempfile.TemporaryDirectory() as temp_dir:

                        html_path = os.path.join(
                            temp_dir,
                            "auditoria.html"
                        )

                        pdf_path = os.path.join(
                            temp_dir,
                            "auditoria.pdf"
                        )

                        # Guardar el HTML generado
                        with open(
                            html_path,
                            "w",
                            encoding="utf-8"
                        ) as f:

                            f.write(html_content)

                        # Ejecutar Chrome en modo headless
                        subprocess.run(
                            [
                                chrome_path,
                                "--headless",
                                "--disable-gpu",
                                "--no-sandbox",
                                "--disable-dev-shm-usage",
                                "--print-to-pdf=" + pdf_path,
                                "--print-to-pdf-no-header",
                                "--run-all-compositor-stages-before-draw",
                                "file:///" + html_path.replace("\\", "/")
                            ],
                            check=True,
                            capture_output=True,
                            text=True
                        )

                        # Leer PDF generado por Chrome
                        with open(
                            pdf_path,
                            "rb"
                        ) as f:

                            pdf_buffer.write(
                                f.read()
                            )

                    pdf_buffer.seek(0)

                    st.success(
                        "✅ PDF generado correctamente con Google Chrome."
                    )

                    st.download_button(
                        label="📥 Descargar Auditoría Estratégica en PDF",
                        data=pdf_buffer,
                        file_name="Auditoria_LinkedIn_Premium.pdf",
                        mime="application/pdf",
                        key="descargar_auditoria_pdf"
                    )

                except Exception as e:

                    st.error(
                        f"❌ Error al generar el PDF con Google Chrome: {e}"
                    )


            except Exception as e:

                st.error(
                    f"Error crítico en el motor de análisis: {e}"
                )