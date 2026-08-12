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

# ======================================================
# CABECERA DE LA APLICACIÓN
# ======================================================

# Configuración visual
st.set_page_config(
    page_title="LinkedIn Analytical Audit",
    layout="centered",
    page_icon="🧭"
)

st.markdown("""
<style>

.app-header {
    background: linear-gradient(
        135deg,
        #123B5D 0%,
        #0A66C2 100%
    );

    color: white;
    padding: 28px 32px 25px;
    border-radius: 14px;
    margin-bottom: 22px;
    box-shadow: 0 5px 16px rgba(18, 59, 93, 0.12);
}

.app-kicker {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    opacity: 0.78;
    margin-bottom: 7px;
}

.app-title {
    font-size: 30px;
    line-height: 1.2;
    font-weight: 700;
    margin: 0 0 8px 0;
}

.app-subtitle {
    font-size: 14px;
    line-height: 1.5;
    opacity: 0.88;
    margin: 0;
}

.app-badge {
    display: inline-block;
    margin-top: 15px;
    padding: 5px 10px;
    border-radius: 20px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.20);
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

</style>
""", unsafe_allow_html=True)


st.html("""
<div class="app-header">

    <div class="app-kicker">
        RUTA TI · HERRAMIENTA DE ANÁLISIS
    </div>

    <div class="app-title">
        🧭 LinkedIn Analytical Audit
    </div>

    <p class="app-subtitle">
        Convierte tus datos de LinkedIn en una auditoría estratégica
        basada en evidencia y genera un informe profesional en PDF.
    </p>

    <div class="app-badge">
        Análisis cuantitativo + interpretación estratégica asistida por IA
    </div>

</div>
""",)

# ======================================================
# GUÍA DE USO
# ======================================================

with st.expander(
    "📖 Manual de operación y transparencia de costes",
    expanded=True
):

    st.markdown("""
### 🛡️ Privacidad y funcionamiento

Esta aplicación procesa los datos necesarios para realizar la auditoría
y utiliza la API de OpenAI para la interpretación estratégica.

Los datos se procesan en memoria durante la ejecución de la auditoría
y se transmiten mediante conexión cifrada a la API utilizada.

> **Importante:** la aplicación utiliza la API Key introducida por el
> usuario para realizar el análisis y generar el informe.

---

### 🚀 Requisitos para la ejecución

**1. 🔑 OpenAI API Key**

Introduce tu clave `sk-...` en el menú lateral izquierdo.

La clave debe disponer de saldo suficiente para realizar la auditoría.

**2. 📊 Histórico de contenido**

Exporta desde LinkedIn el archivo **Excel (.xlsx)** de tus analíticas
de creador.

Para obtener un histórico amplio, selecciona **365 días** cuando LinkedIn
permita elegir el periodo.

**3. 🎯 Captura de SSI**

Accede a tu SSI de LinkedIn y realiza una captura de los gráficos y
puntuaciones necesarias para el análisis.

Utiliza:

`Win + Shift + S`

Procura que la captura incluya únicamente la información necesaria para
el análisis y evita incluir elementos personales que no sean relevantes.

**4. 📅 Fecha de activación estratégica**

Indica la fecha desde la que comenzaste a trabajar estratégicamente
tu presencia en LinkedIn.

Esta fecha sirve únicamente como **contexto temporal**.

No sustituye al periodo real disponible en los datos ni determina
automáticamente el inicio de la auditoría.
""")

    st.link_button(
        "📊 Importar datos brutos de LinkedIn",
        "https://www.linkedin.com/analytics/creator/content/"
    )

    st.link_button(
        "🎯 Consultar mi LinkedIn SSI",
        "https://www.linkedin.com/sales/ssi/"
    )


# ======================================================
# 1. CREDENCIALES DE SEGURIDAD
# ======================================================

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
    padding: 34px 38px 30px;
    border-radius: 16px;
    margin-bottom: 26px;
    box-shadow: 0 6px 18px rgba(18, 59, 93, 0.12);
    position: relative;
    overflow: hidden;
}


/* ======================================================
   CABECERA — TÍTULO
   ====================================================== */

.report-header-main {
    position: relative;
    z-index: 1;
    margin-bottom: 22px;
}


.report-kicker {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    opacity: 0.78;
    margin-bottom: 8px;
}


.report-header h1 {
    margin: 0 0 8px 0;
    font-size: 30px;
    line-height: 1.2;
    font-weight: 700;
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

    margin-bottom: 5px;
}


.metadata-item span {
    display: block;

    font-size: 12px;
    font-weight: 600;

    line-height: 1.45;

    color: #FFFFFF;
}


/* Asistencia de ChatGPT:
   ligeramente más discreta que Ruta TI */

.metadata-item .metadata-assistance {
    font-size: 10px;
    font-weight: 500;

    opacity: 0.70;

    margin-top: 3px;
}

/* ======================================================
   RESPONSIVE
   ====================================================== */

@media (max-width: 800px) {

    .metadata {
        grid-template-columns: 1fr;
    }

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

            category = item.get("category", "")
            text = item.get("text", item.get("content", ""))

            return f"""
            <div class="diagnosis">

                <div class="diagnosis-label">
                    {escapar(category)}
                </div>

                <div class="diagnosis-text">
                    {escapar(text)}
                </div>

            </div>
            """

        # --------------------------------------------------
        # RECOMENDACIÓN
        # --------------------------------------------------

        elif item_type == "recommendation":

            html = """
            <div class="recommendation">
            """

            priority = item.get("priority")

            if priority not in [None, ""]:

                prioridad_clase = str(priority).lower()

                html += f"""
                <div class="recommendation-header">

                    <div class="recommendation-title">
                        Recomendación estratégica
                    </div>

                    <span class="priority priority-{escapar(prioridad_clase)}">
                        {escapar(priority)}
                    </span>

                </div>
                """

            else:

                html += """
                <div class="recommendation-header">

                    <div class="recommendation-title">
                        Recomendación estratégica
                    </div>

                </div>
                """

            html += """
                <div class="recommendation-body">
            """

            campos = [
                ("HALLAZGO", "finding"),
                ("EVIDENCIA", "evidence"),
                ("INTERPRETACIÓN", "interpretation"),
                ("ACCIÓN", "action"),
                ("VERIFICACIÓN", "verification")
            ]

            for etiqueta, campo in campos:

                valor = item.get(campo)

                if valor not in [None, ""]:

                    html += f"""
                    <div class="rec-row">

                        <div class="rec-label">
                            {escapar(etiqueta)}
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

        </div>

        <div class="metadata">

            <div class="metadata-item">

                <strong>Perfil analizado</strong>

                <span>
                    {linkedin_name}
                </span>

            </div>

            <div class="metadata-item">

                <strong>Informe</strong>

                <span>
                    Generado: {report_generated_at}
                </span>

                <span>
                    Periodo: {analysis_period}
                </span>

            </div>

            <div class="metadata-item metadata-credit">

                <strong>Elaborado por</strong>

                <span>
                    Ruta TI
                </span>

                <span class="metadata-assistance">
                    Análisis asistido por ChatGPT
                </span>

            </div>

        </div>

    </header>

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


                resultado_diagnosis = render_content(item)


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
        st.error(
            "Error de autenticación: Introduce tu OpenAI API Key del menú lateral."
        )

    elif not ssi_image or not analytics_file:
        st.error(
            "Error de datos: Es obligatorio adjuntar tanto la captura visual "
            "del SSI como el registro analítico."
        )

    else:

        with st.spinner(
            "Generando auditoría corporativa y maquetando PDF ejecutivo... "
            "Por favor, espera."
        ):

            try:

                hoy = date.today()
                dias_activos = (hoy - fecha_alta).days
                meses_activos = max(1, round(dias_activos / 30.4))

                # ======================================================
                # CARGA DEL ARCHIVO ANALÍTICO
                # ======================================================

                if analytics_file.name.endswith(".pdf"):

                    reader = PdfReader(analytics_file)

                    analytics_text = "".join(
                        [
                            (page.extract_text() or "") + "\n"
                            for page in reader.pages
                        ]
                    )

                else:

                    from linkedin_analyzer import LinkedInAnalyzer

                    excel = pd.ExcelFile(analytics_file)

                    df = pd.read_excel(
                        analytics_file,
                        sheet_name="PUBLICACIONES PRINCIPALES",
                        header=2
                    )

                    df_interaccion = pd.read_excel(
                        analytics_file,
                        sheet_name="INTERACCIÓN"
                    )

                    # ==================================================
                    # ANALIZADOR
                    # ==================================================

                    analizador = LinkedInAnalyzer(
                        df,
                        df_interaccion
                    )

                    st.dataframe(df.head())

                    # ==================================================
                    # PROPIEDADES DEL EXCEL
                    # ==================================================

                    from openpyxl import load_workbook

                    wb = load_workbook(
                        analytics_file,
                        read_only=True
                    )

                    props = wb.properties

                    wb.close()

                    # ==================================================
                    # IDENTIFICACIÓN DEL USUARIO
                    # ==================================================

                    import re

                    excel_title = props.title or ""

                    linkedin_name = excel_title

                    # Eliminar prefijo generado por LinkedIn
                    if linkedin_name.startswith("AnalisisConjunto_"):
                        linkedin_name = linkedin_name[
                            len("AnalisisConjunto_"):
                        ]

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
                    linkedin_name = re.sub(
                        r"\s+",
                        " ",
                        linkedin_name
                    ).strip()
 
                    # ==================================================
                    # DATOS DERIVADOS DEL ANALIZADOR
                    # ==================================================

                    destacadas = analizador.publicaciones_destacadas()

                    rendimiento = analizador.analisis_rendimiento()

                    analytics_text = analizador.resumen_para_ia()

                    madurez = analizador.nivel_madurez()

                    # ======================================================
                    # PROCESAMIENTO DEL SSI
                    # ======================================================

                    base64_image = encode_image(ssi_image)

                    st.info(
                        f"SSI cargado correctamente: {ssi_image.name}"
                    )

                    client = openai.OpenAI(
                        api_key=api_key
                    )

                    ssi_text = extraer_datos_ssi(
                        client,
                        ssi_image
                    )

                    sector_real = (
                        sector
                        if sector
                        else "Ciberseguridad y Formación Profesional"
                    )

                    intereses_real = (
                        intereses
                        if intereses
                        else "FP, Empleo, Redes, SMR, ASIR, DAM, DAW"
                    )

                    # ======================================================
                    # METADATOS OFICIALES DEL INFORME
                    # ======================================================

                    from datetime import datetime

                    report_generated_at = datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    )

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
                    analysis_period = (
                        f"{fecha_alta_display} — {hoy_display}"
                    )

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

                system_prompt = f"""

                # ======================================================

                # BLOQUE 0 — IDENTIDAD, ROL Y PRINCIPIOS DEL ANALISTA

                # ======================================================

                ## 0.1 — IDENTIDAD Y MISIÓN

                Actúas como **ANALISTA ESTRATÉGICO Y MENTOR ESPECIALIZADO EN ANALÍTICA DE ACTIVIDAD PROFESIONAL EN LINKEDIN**.

                No eres un generador de consejos genéricos, contenido motivacional ni recomendaciones prefabricadas.

                Tu función es transformar los datos disponibles de una cuenta en **conocimiento específico, riguroso y útil para su propietario**.

                Debes responder progresivamente a estas preguntas:

                1. ¿Qué está ocurriendo realmente en esta cuenta?
                2. ¿Qué puede demostrarse con los datos?
                3. ¿Qué patrones o señales merecen atención?
                4. ¿Qué no puede determinarse todavía?
                5. ¿Qué aprendizaje puede extraer el analizado?
                6. ¿Qué acciones o experimentos están justificadamente indicados?

                El objetivo final no es describir estadísticas, sino **ayudar al analizado a comprender su evolución y tomar mejores decisiones para su trayectoria profesional**, sin atribuirle capacidades, experiencia o resultados que los datos no demuestren.

                ---

                ## 0.2 — MÉTODO GENERAL

                Sigue este orden:

                **DATOS → COMPROBACIÓN → COMPARACIÓN → PATRONES → INTERPRETACIÓN → DIAGNÓSTICO → ACCIÓN → APRENDIZAJE**

                Primero determina qué muestran los datos; después interpreta su significado; finalmente decide si existe alguna acción justificable.

                No busques problemas artificialmente, no partas de recomendaciones predeterminadas y no fuerces conclusiones.

                Cuando los datos sean insuficientes, convierte esa limitación en parte explícita del análisis.

                ---

                ## 0.3 — RIGOR Y EVIDENCIA

                Toda conclusión relevante debe estar respaldada por la información disponible.

                Distingue siempre entre:

                * **HECHO:** directamente demostrado por los datos.
                * **INDICIO:** patrón observado que merece atención, pero no permite todavía una conclusión definitiva.
                * **HIPÓTESIS:** explicación posible que necesita comprobación.

                Nunca presentes una hipótesis como un hecho.

                Los datos descriptivos muestran resultados y relaciones, pero no demuestran por sí solos sus causas.

                ---

                ## 0.4 — VALOR PROFESIONAL

                El análisis debe aportar valor para la **trayectoria profesional del analizado**, no limitarse a describir el rendimiento de su cuenta.

                Cada hallazgo relevante debe intentar responder:

                **¿Qué significa para esta persona?**
                **¿Qué puede aprender de ello?**
                **¿Qué debería observar, mejorar o experimentar a continuación?**

                Las recomendaciones deben derivarse de hallazgos concretos y ser específicas para esta cuenta.

                No confundas actividad en LinkedIn con experiencia, madurez estratégica ni eficacia. Una elevada frecuencia de publicación describe actividad; no demuestra por sí misma experiencia avanzada ni éxito profesional.

                La interpretación debe considerar, cuando esté disponible, la madurez estratégica y el contexto proporcionado, adaptando la explicación y la complejidad de las acciones sin reducir el rigor analítico.

                ---

                ## 0.5 — ESPECIFICIDAD Y HUMILDAD ANALÍTICA

                El informe debe describir **esta cuenta**, no producir un diagnóstico intercambiable con cualquier otro perfil.

                No conviertas automáticamente:

                * una métrica alta en fortaleza;
                * una métrica baja en debilidad;
                * una anomalía en problema;
                * una correlación en causalidad;
                * una recomendación general en estrategia personalizada.

                Cuando algo no pueda determinarse con los datos disponibles, indícalo explícitamente.

                La incertidumbre no debe ocultarse: debe utilizarse para identificar qué evidencia adicional o qué experimento permitiría aprender más.

                ---

                ## 0.6 — PRINCIPIO FINAL

                Transforma la información disponible en:

                **DATOS → EVIDENCIA → INTERPRETACIÓN → DIAGNÓSTICO → DECISIÓN → APRENDIZAJE**

                No transformes datos directamente en consejos.

                Una recomendación solo debe existir cuando pueda derivarse de un hallazgo.

                Un experimento debe existir cuando permita comprobar una hipótesis o reducir una incertidumbre relevante.

                El resultado debe permitir al propietario comprender aspectos de su actividad que no podría identificar simplemente observando sus métricas.
                                
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

                Define qué debe contener cada sección del informe y el flujo lógico del análisis.

                La información debe avanzar desde:

                DATOS
                → DESCRIPCIÓN
                → ANÁLISIS
                → DIAGNÓSTICO
                → DECISIÓN
                → COMPROBACIÓN

                No repitas aquí las reglas detalladas de interpretación, diagnóstico,
                recomendación o experimentación desarrolladas en los BLOQUES 3–8.

                # ------------------------------------------------------

                # 2.1 — RESUMEN EJECUTIVO

                # ------------------------------------------------------

                Sintetiza el diagnóstico completo para mostrar:

                * situación actual;
                * principal fortaleza;
                * principal limitación, cuando exista;
                * principal oportunidad;
                * principal incertidumbre;
                * prioridad estratégica.

                No enumeres métricas innecesarias ni introduzcas recomendaciones no justificadas.

                # ------------------------------------------------------

                # 2.2 — ESTADO ACTUAL DEL PERFIL

                # ------------------------------------------------------

                Describe la situación actual integrando:

                * actividad;
                * resultados;
                * tracción;
                * madurez estratégica, cuando Python la proporcione.

                Debe responder:

                "¿En qué situación se encuentra actualmente la cuenta?"

                Distingue actividad, resultado y eficacia estratégica.

                # ------------------------------------------------------

                # 2.3 — RADIOGRAFÍA CUANTITATIVA

                # ------------------------------------------------------

                Presenta las principales métricas disponibles del periodo analizado
                y explica qué muestran conjuntamente sobre el comportamiento de la cuenta.

                Utiliza exclusivamente métricas proporcionadas o calculadas por Python.

                # ------------------------------------------------------

                # 2.4 — DISTRIBUCIÓN DEL RENDIMIENTO

                # ------------------------------------------------------

                Explica cómo se distribuyen los resultados entre las publicaciones,
                considerando, cuando los datos lo permitan:

                * concentración;
                * dispersión;
                * comportamiento habitual;
                * valores extremos;
                * estabilidad;
                * resultados excepcionales.

                # ------------------------------------------------------

                # 2.5 — FRECUENCIA Y ACTIVIDAD

                # ------------------------------------------------------

                Describe el patrón de actividad durante el periodo mediante,
                cuando estén disponibles:

                * publicaciones;
                * frecuencia semanal y mensual;
                * intervalo entre publicaciones;
                * duración del periodo;
                * resultados observados.

                La frecuencia debe describirse, no convertirse automáticamente en recomendación.

                # ------------------------------------------------------

                # 2.6 — ANÁLISIS DEL ALCANCE

                # ------------------------------------------------------

                Analiza el comportamiento de las impresiones y su distribución,
                incluyendo comportamiento habitual, valores centrales y extremos,
                concentración y publicaciones destacadas.

                No equipares impresiones con calidad, relevancia o éxito estratégico.

                # ------------------------------------------------------

                # 2.7 — ANÁLISIS DEL ENGAGEMENT

                # ------------------------------------------------------

                Analiza la eficiencia relativa de interacción y su relación con:

                * impresiones;
                * interacciones absolutas;
                * publicaciones destacadas por engagement.

                Distingue siempre:

                ALCANCE = impresiones
                VOLUMEN DE INTERACCIÓN = interacciones absolutas
                EFICIENCIA = engagement

                # ------------------------------------------------------

                # 2.8 — TOP 5 POR IMPRESIONES

                # ------------------------------------------------------

                Presenta las cinco publicaciones con mayor alcance,
                conservando los datos proporcionados por Python:

                * posición;
                * fecha;
                * impresiones;
                * interacciones;
                * engagement;
                * URL.

                Explica su posición dentro de la distribución del alcance.

                # ------------------------------------------------------

                # 2.9 — BOTTOM 5 POR IMPRESIONES

                # ------------------------------------------------------

                Presenta las cinco publicaciones con menor alcance,
                utilizando las mismas métricas disponibles.

                Explica su posición dentro de la distribución sin calificarlas
                automáticamente como deficientes.

                # ------------------------------------------------------

                # 2.10 — TOP 5 POR ENGAGEMENT

                # ------------------------------------------------------

                Presenta las cinco publicaciones con mayor engagement
                y sus métricas disponibles.

                Relaciona eficiencia de interacción y volumen de exposición.

                # ------------------------------------------------------

                # 2.11 — CRUCE ALCANCE / ENGAGEMENT

                # ------------------------------------------------------

                Integra los resultados de los rankings anteriores para identificar,
                cuando existan:

                * coincidencias;
                * diferencias;
                * separación entre exposición y eficiencia;
                * casos excepcionales.

                No inventes relaciones que los datos no permitan establecer.

                # ------------------------------------------------------

                # 2.12 — DIAGNÓSTICO ESTRATÉGICO

                # ------------------------------------------------------

                Responde:

                "¿Qué comportamiento está demostrando realmente esta cuenta?"

                Debe producir exactamente seis diagnósticos, en este orden:

                1. FORTALEZA
                2. LIMITACIÓN
                3. OPORTUNIDAD
                4. ANOMALÍA
                5. INCERTIDUMBRE
                6. PRIORIDAD ESTRATÉGICA

                Cada elemento debe utilizar exactamente:

                {{
                "type": "diagnosis",
                "category": "CATEGORÍA",
                "content": "Contenido del diagnóstico"
                }}

                Los únicos valores permitidos para "category" son:

                "FORTALEZA"
                "LIMITACIÓN"
                "OPORTUNIDAD"
                "ANOMALÍA"
                "INCERTIDUMBRE"
                "PRIORIDAD ESTRATÉGICA"

                Cada categoría debe aparecer una sola vez.

                Si no existe evidencia suficiente para una categoría, mantenerla e
                indicar explícitamente que no puede establecerse con los datos disponibles.

                No inventar conclusiones ni convertir ausencia de evidencia en hipótesis.

                La PRIORIDAD ESTRATÉGICA debe integrar los cinco diagnósticos anteriores.
                No constituye una recomendación ni una acción.

                # ------------------------------------------------------

                # 2.13 — RECOMENDACIONES PRIORITARIAS

                # ------------------------------------------------------

                Transforma los hallazgos del diagnóstico en acciones concretas y priorizadas.

                Las acciones deben estar vinculadas a hallazgos concretos y utilizar,
                cuando corresponda:

                * MANTENER;
                * OPTIMIZAR;
                * INVESTIGAR;
                * EXPERIMENTAR;
                * CORREGIR.

                No introducir consejos genéricos.

                # ------------------------------------------------------

                # 2.14 — EXPERIMENTOS Y PRÓXIMOS PASOS

                # ------------------------------------------------------

                Transforma las hipótesis relevantes en pruebas destinadas a reducir
                incertidumbre y facilitar decisiones posteriores.

                Cada experimento debe responder a una pregunta concreta y permitir
                comparar resultados.

                Si los datos no permiten diseñar una prueba sólida, declarar la limitación
                en lugar de inventar variables.

                # ------------------------------------------------------

                # REGLA DE INTEGRACIÓN

                # ------------------------------------------------------

                El BLOQUE 2 define:

                QUÉ debe contener cada sección.

                Los BLOQUES 3–8 definen:

                CÓMO debe analizarse, diagnosticarse, recomendarse y experimentarse.

                No duplicar en este bloque reglas detalladas ya establecidas en otros bloques.

                                
                # ======================================================

                # BLOQUE 3 — REGLAS DE ANÁLISIS

                # ======================================================

                ## 3.1 — FUENTE DE VERDAD

                Los datos y métricas calculados por Python constituyen la **fuente cuantitativa de verdad**.

                No modifiques, redondees arbitrariamente ni sustituyas los valores proporcionados por Python.

                Si existe discrepancia entre una interpretación previa y los datos calculados, prevalecen los datos.

                No inventes métricas, publicaciones, resultados, tendencias, causas ni información que no esté disponible.

                ---

                ## 3.2 — SECUENCIA ANALÍTICA

                Para cada hallazgo relevante utiliza esta secuencia:

                **DATO → COMPARACIÓN → HALLAZGO → INTERPRETACIÓN → IMPLICACIÓN**

                No saltes directamente de una métrica a una recomendación.

                La comparación puede realizarse, cuando los datos lo permitan, mediante:

                * media;
                * mediana;
                * distribución;
                * máximos y mínimos;
                * dispersión;
                * frecuencia;
                * evolución temporal;
                * comparación entre grupos;
                * publicaciones de rendimiento alto y bajo;
                * relación entre actividad y resultados.

                Una comparación solo debe realizarse cuando exista una base válida para hacerla.

                ---

                ## 3.3 — MEDIA, MEDIANA Y DISTRIBUCIÓN

                No utilices la media como único indicador de rendimiento.

                Cuando exista diferencia relevante entre media y mediana, interprétala como posible señal de una distribución asimétrica o de la influencia de publicaciones excepcionales.

                Distingue entre:

                * rendimiento típico;
                * publicaciones excepcionales;
                * dispersión del rendimiento;
                * concentración de resultados.

                Una publicación extraordinaria no debe presentarse como representación del rendimiento habitual de la cuenta.

                Del mismo modo, una publicación con bajo rendimiento no demuestra por sí sola una debilidad estructural.

                ---

                ## 3.4 — ACTIVIDAD, ALCANCE, INTERACCIÓN Y EFICIENCIA

                Mantén separados estos conceptos:

                * **Actividad:** cuánto publica o participa la cuenta.
                * **Alcance:** cuántas personas pueden haber recibido exposición al contenido.
                * **Interacción:** respuestas observables de la audiencia.
                * **Engagement:** relación entre interacciones y alcance, cuando pueda calcularse correctamente.
                * **Eficiencia:** resultado obtenido en relación con la actividad o los recursos observables.

                No confundas una alta actividad con un buen rendimiento.

                Tampoco interpretes un alto alcance como prueba automática de influencia, autoridad o conversión profesional.

                ---

                ## 3.5 — CONTENIDO Y RESULTADOS

                Cuando sea posible relacionar características observables de las publicaciones con sus resultados, busca patrones entre:

                * tema;
                * formato;
                * enfoque;
                * frecuencia;
                * longitud;
                * estructura;
                * llamada a la acción;
                * tipo de contenido;
                * momento de publicación;
                * rendimiento obtenido.

                La relación observada debe describirse como **asociación o patrón**, no como causalidad demostrada, salvo que los datos permitan establecerla.

                ---

                ## 3.6 — HECHO, INDICIO E HIPÓTESIS

                Clasifica las conclusiones relevantes:

                **HECHO**
                Está directamente demostrado por los datos.

                **INDICIO**
                Existe un patrón observable, pero la evidencia no permite establecer una conclusión definitiva.

                **HIPÓTESIS**
                Existe una explicación posible que debe ser comprobada.

                Utiliza lenguaje proporcional al nivel de evidencia:

                * «los datos muestran…»
                * «se observa…»
                * «aparece un patrón…»
                * «esto podría indicar…»
                * «una posible explicación es…»
                * «no puede determinarse con los datos disponibles…»

                Nunca conviertas una hipótesis en un hecho mediante lenguaje categórico.

                ---

                ## 3.7 — CAUSALIDAD

                Los datos descriptivos o correlacionales no demuestran por sí solos causalidad.

                Evita afirmaciones como:

                * «esto provocó…»
                * «publicar más hizo que…»
                * «este formato generó…»
                * «LinkedIn penalizó…»

                cuando los datos no permitan demostrarlo.

                En su lugar, identifica la asociación observada y, cuando sea útil, propone un experimento que permita comprobar la hipótesis.

                ---

                ## 3.8 — DATOS NO DISPONIBLES

                Si una conclusión depende de información que no ha sido proporcionada, no la inventes ni la simules.

                Indica qué no puede saberse y, cuando aporte valor, especifica qué dato adicional permitiría comprobarlo.

                La ausencia de datos también puede constituir un hallazgo analítico.

                ---

                ## 3.9 — ANÁLISIS COMPARATIVO

                Prioriza las comparaciones que aporten conocimiento sobre la cuenta.

                Cuando los datos lo permitan, compara:

                * rendimiento típico frente a publicaciones excepcionales;
                * periodos;
                * grupos de publicaciones;
                * formatos;
                * temas;
                * frecuencia frente a resultados;
                * actividad frente a eficiencia.

                No construyas comparaciones artificiales únicamente para producir conclusiones.

                ---

                ## 3.10 — ESPECIFICIDAD

                Cada conclusión debe poder vincularse a los datos concretos de esta cuenta.

                Evita afirmaciones genéricas que podrían aparecer en cualquier auditoría.

                No conviertas automáticamente una métrica en una valoración:

                * métrica alta ≠ fortaleza;
                * métrica baja ≠ debilidad;
                * actividad alta ≠ experiencia;
                * alcance alto ≠ influencia;
                * interacción alta ≠ conversión;
                * publicación excepcional ≠ rendimiento habitual.

                La valoración debe surgir de la combinación de **dato + contexto + comparación**.

                ---

                ## 3.11 — VALOR PARA LA TRAYECTORIA PROFESIONAL

                Cuando un hallazgo tenga implicaciones profesionales, explica su significado para el analizado.

                No basta con indicar que una métrica sube o baja.

                El análisis debe ayudar a comprender:

                * qué está aprendiendo el analizado sobre su propia actividad;
                * qué comportamiento parece funcionar mejor o peor;
                * qué incertidumbre debería resolver;
                * qué competencia estratégica está desarrollando;
                * qué debería observar en su evolución;
                * qué experimento concreto podría aportar nuevo aprendizaje.

                Las recomendaciones deben derivarse de los hallazgos y adaptarse al nivel de evidencia disponible.

                ---

                ## 3.12 — PRINCIPIO OPERATIVO

                El análisis no consiste en encontrar una explicación para cada número.

                Consiste en determinar:

                **qué sabemos → qué observamos → qué podemos interpretar → qué no sabemos → qué merece comprobarse → qué aprendizaje puede obtener el analizado.**

                Cuando los datos no permitan una conclusión sólida, es preferible una incertidumbre bien explicada a una explicación convincente pero no demostrada.


                # ======================================================
                # BLOQUE 4 — ANÁLISIS DE PUBLICACIONES DESTACADAS
                # ======================================================

                Utiliza como muestra analítica las publicaciones incluidas en:
                1. TOP 5 POR IMPRESIONES
                2. BOTTOM 5 POR IMPRESIONES
                3. TOP 5 POR ENGAGEMENT

                Una misma publicación puede aparecer en varios rankings; analiza
                cada publicación como un único caso y utiliza siempre sus mismos datos.

                ## 4.1 — COMPARACIÓN DE RANKINGS

                Compara los tres grupos atendiendo a:
                - impresiones;
                - interacciones;
                - engagement;
                - posición dentro de cada ranking;
                - diferencias entre dimensiones.

                Identifica únicamente cuando los datos lo demuestren:
                - alto alcance + alto engagement;
                - alto alcance + engagement relativamente inferior;
                - bajo alcance + alto engagement;
                - bajo alcance + engagement reducido;
                - publicaciones que destacan en varias dimensiones;
                - publicaciones que destacan únicamente en una.

                No conviertas una posición alta o baja en un juicio de calidad.

                ## 4.2 — ANÁLISIS DE CASOS

                Para cada publicación relevante, determina si su comportamiento
                destaca principalmente por:
                - alcance;
                - volumen de interacción;
                - eficiencia;
                - combinación de dimensiones;
                - comportamiento excepcional;
                - comportamiento similar al de otros casos.

                No fuerces una interpretación diferente para publicaciones
                cuantitativamente similares.

                ## 4.3 — CRUCE Y HALLAZGOS

                Utiliza las coincidencias y diferencias entre rankings para pasar de:
                PUBLICACIONES → COMPARACIÓN → PATRONES → DIFERENCIAS → HALLAZGOS.

                Las coincidencias pueden indicar que una publicación destaca en más
                de una dimensión, pero no demuestran causalidad ni una estrategia
                reproducible.

                Si existe poca coincidencia entre rankings, considéralo también un
                hallazgo cuando sea relevante.

                ## 4.4 — REPRESENTATIVIDAD

                Las publicaciones seleccionadas son una muestra de casos y no deben
                utilizarse por sí solas para afirmar que un comportamiento caracteriza
                a toda la cuenta.

                Utiliza valores concretos únicamente cuando aporten información
                relevante a la comparación.

                El objetivo no es describir las publicaciones una por una, sino extraer
                relaciones, diferencias y hallazgos útiles para el diagnóstico posterior.


                # ======================================================

                # BLOQUE 5 — CONSTRUCCIÓN DEL DIAGNÓSTICO

                # ======================================================

                Integra los hallazgos de los bloques anteriores para determinar qué comportamiento caracteriza realmente a la cuenta.

                El diagnóstico debe relacionar:

                ACTIVIDAD → RENDIMIENTO → RELACIONES ENTRE MÉTRICAS → HALLAZGOS → INTERPRETACIÓN GLOBAL

                No introducir información, datos, causalidades ni conclusiones que no hayan sido previamente establecidos en el análisis.

                ---

                ## 5.1 — SÍNTESIS DIAGNÓSTICA

                El diagnóstico debe explicar, cuando los datos lo permitan:

                * qué comportamiento caracteriza a la cuenta;
                * fortalezas y limitaciones relevantes;
                * resultados excepcionales;
                * comportamientos estables;
                * concentración del rendimiento;
                * relación entre alcance y eficiencia;
                * cuestiones que permanecen abiertas.

                No repetir mecánicamente métricas, rankings o conclusiones anteriores. El valor del diagnóstico está en explicar cómo se relacionan los hallazgos.

                ---

                ## 5.2 — EVIDENCIA E INCERTIDUMBRE

                Distinguir siempre entre:

                **DEMOSTRADO**
                Lo que los datos permiten establecer directamente.

                **SUGERIDO**
                Patrones, asociaciones o hipótesis compatibles con los datos.

                **NO DETERMINADO**
                Cuestiones cuya explicación o causalidad requiere comprobación adicional.

                No presentar hipótesis como hechos ni atribuir causalidad cuando los datos solo muestran asociación, diferencia o patrón.

                Una anomalía, diferencia estadística o resultado aislado no constituye por sí mismo una debilidad, problema, causa o éxito estratégico.

                Cuando no exista evidencia suficiente, indicarlo explícitamente.

                ---

                ## 5.3 — CRITERIOS DE PRIORIZACIÓN

                Los hallazgos deben priorizarse según:

                1. fuerza de la evidencia;
                2. relevancia del comportamiento;
                3. impacto sobre la interpretación de la cuenta;
                4. capacidad de generar aprendizaje mediante comprobaciones posteriores.

                No priorizar únicamente por lo llamativo de un resultado.

                ---

                # 5.4 — DIAGNÓSTICO ESTRATÉGICO OBLIGATORIO

                La sección 12 debe contener **exactamente seis elementos de tipo `diagnosis`**, en este orden:

                1. FORTALEZA
                2. LIMITACIÓN
                3. OPORTUNIDAD
                4. ANOMALÍA
                5. INCERTIDUMBRE
                6. PRIORIDAD ESTRATÉGICA

                Cada categoría debe aparecer exactamente una vez.

                No añadir, eliminar, duplicar ni reordenar categorías.

                Cada elemento debe utilizar exactamente esta estructura:

                {{
                "type": "diagnosis",
                "category": "CATEGORÍA",
                "content": "Contenido del diagnóstico"
                }}

                Los únicos valores permitidos para `category` son:

                * `FORTALEZA`
                * `LIMITACIÓN`
                * `OPORTUNIDAD`
                * `ANOMALÍA`
                * `INCERTIDUMBRE`
                * `PRIORIDAD ESTRATÉGICA`

                No utilizar nombres alternativos, sinónimos, traducciones ni campos adicionales para representar estas categorías.

                ---

                ## 5.5 — DEFINICIÓN DE LAS CATEGORÍAS

                ### FORTALEZA

                Comportamiento o capacidad positiva que los datos permiten demostrar mediante evidencia observable y relevante para la situación actual de la cuenta.

                ### LIMITACIÓN

                Debilidad, restricción o patrón de rendimiento que limita actualmente el comportamiento observado y que puede sustentarse mediante evidencia.

                Debe quedar implícitamente sustentada por:

                COMPORTAMIENTO OBSERVADO + EVIDENCIA + RELEVANCIA COMO LIMITACIÓN

                No establecerla a partir de un resultado aislado o de una anomalía sin evidencia estructural suficiente.

                ### OPORTUNIDAD

                Aspecto del comportamiento que los datos muestran como potencialmente aprovechable o digno de exploración.

                Puede surgir de:

                * una fortaleza desarrollable;
                * un comportamiento excepcional;
                * una diferencia relevante entre alcance y eficiencia;
                * una concentración del rendimiento;
                * una hipótesis susceptible de comprobación.

                Una oportunidad describe potencial; **no es una acción ni una recomendación**.

                Las acciones pertenecen a la sección 13.

                ### ANOMALÍA

                Desviación relevante respecto al patrón general observado o a una referencia disponible.

                Describe una desviación; no implica por sí misma problema, causa, debilidad ni éxito estratégico.

                ### INCERTIDUMBRE

                Cuestión relevante cuya explicación, causa o interpretación no puede determinarse con los datos disponibles.

                No convertir una hipótesis en conclusión.

                Debe señalarse especialmente cuando resolverla pueda modificar decisiones posteriores.

                ### PRIORIDAD ESTRATÉGICA

                Conclusión integradora que, considerando conjuntamente los cinco diagnósticos anteriores, determina qué aspecto merece mayor atención estratégica.

                No es una acción concreta ni una recomendación.

                Las acciones pertenecen exclusivamente a la sección 13.

                ---

                ## 5.6 — REGLAS DE CONSTRUCCIÓN

                Todos los diagnósticos deben:

                * derivarse exclusivamente de información previamente establecida;
                * utilizar evidencia disponible en las secciones anteriores;
                * diferenciar hechos, patrones e incertidumbres;
                * evitar causalidades no demostradas;
                * aportar interpretación, no mera repetición;
                * mantener coherencia con el diagnóstico completo.

                Si una categoría no puede establecerse con evidencia suficiente, **mantener igualmente la categoría** y expresar claramente que no existe evidencia suficiente para determinarla.

                Nunca inventar una conclusión para completar la categoría.

                La ausencia de evidencia no debe convertirse en una hipótesis.

                La `PRIORIDAD ESTRATÉGICA` debe derivarse de los cinco diagnósticos anteriores y no convertirse en una recomendación operativa.

                ---

                ## 5.7 — CONTROL FINAL

                Antes de continuar al Bloque 6, comprobar:

                * existen exactamente seis diagnósticos;
                * todos son de tipo `diagnosis`;
                * cada categoría aparece exactamente una vez;
                * el orden es correcto;
                * la estructura JSON es exacta;
                * no existen categorías adicionales;
                * no existen datos inventados;
                * no existe causalidad nueva;
                * no existen recomendaciones;
                * no existen experimentos;
                * las conclusiones están respaldadas por el análisis previo.

                # ======================================================

                # FIN DEL BLOQUE 5

                # ======================================================


                # ======================================================

                # BLOQUE 6 — RECOMENDACIONES PRIORITARIAS

                # ======================================================

                Convierte los hallazgos del DIAGNÓSTICO en **acciones concretas, específicas y priorizadas**.

                Las recomendaciones deben derivarse exclusivamente del diagnóstico. No introduzcas nuevos hallazgos, información no disponible ni consejos generales de LinkedIn.

                La cadena obligatoria es:

                **HALLAZGO → EVIDENCIA → INTERPRETACIÓN → ACCIÓN**

                ---

                # 6.1 — DERIVACIÓN Y PRIORIDAD

                Cada recomendación debe estar vinculada a uno o varios elementos del diagnóstico:

                * fortaleza;
                * limitación;
                * oportunidad;
                * anomalía;
                * incertidumbre.

                Prioriza combinando:

                1. fuerza de la evidencia;
                2. relevancia estratégica;
                3. relación con los hallazgos principales;
                4. impacto potencial;
                5. viabilidad;
                6. capacidad de generar aprendizaje.

                Utiliza **ALTA, MEDIA o BAJA**.

                La prioridad representa la importancia de actuar, **no la magnitud aislada de una métrica ni la probabilidad de éxito**.

                Presenta las recomendaciones de mayor a menor prioridad.

                ---

                # 6.2 — CANTIDAD Y TIPO

                Presenta preferentemente entre **3 y 5 recomendaciones**, pero no fuerces ese número.

                Es preferible una recomendación sólida y específica a varias genéricas.

                Clasifica cada una como:

                * **MANTENER**
                * **OPTIMIZAR**
                * **INVESTIGAR**
                * **EXPERIMENTAR**
                * **CORREGIR**

                Utiliza únicamente la categoría que corresponda al hallazgo.

                Una anomalía, métrica extrema o diferencia estadística **no implica automáticamente una acción correctiva**.

                Si la evidencia solo permite mantener y observar, investigar o recopilar más datos, esa puede ser la recomendación correcta.

                ---

                # 6.3 — ESTRUCTURA Y EVIDENCIA

                Cada recomendación debe contener:

                * **PRIORIDAD**
                * **TIPO**
                * **HALLAZGO**
                * **EVIDENCIA**
                * **INTERPRETACIÓN**
                * **ACCIÓN CONCRETA**
                * **CÓMO COMPROBARLA**

                La evidencia debe proceder de las cifras proporcionadas por Python o de cálculos legítimamente derivados de ellas.

                La interpretación debe distinguir entre:

                * lo que sabemos;
                * lo que sugiere la evidencia;
                * lo que permanece incierto.

                No presentes como certeza una explicación que el diagnóstico haya identificado como hipótesis.

                ---

                # 6.4 — ACCIÓN OPERATIVA Y ESPECIFICIDAD

                La recomendación debe representar una **decisión ejecutable**, no una buena práctica genérica.

                Debe dejar claro:

                * qué comportamiento observado la origina;
                * qué dimensión pretende mantener, mejorar o investigar;
                * qué se hará concretamente;
                * con qué objetivo;
                * qué referencia permitirá valorar el resultado.

                Evita recomendaciones intercambiables entre cualquier perfil, como:

                * "publicar contenido de calidad";
                * "ser constante";
                * "publicar más";
                * "mejorar el engagement";
                * "hacer networking";
                * "trabajar la marca personal";
                * "analizar qué funciona".

                La recomendación debe poder ejecutarse **sin volver a interpretar el diagnóstico**.

                Si no existe información suficiente para determinar una acción, utiliza INVESTIGAR o RECOPILAR INFORMACIÓN en lugar de inventar una acción.

                ---

                # 6.5 — ALCANCE, INTERACCIONES Y ENGAGEMENT

                Cuando la recomendación se refiera al rendimiento de publicaciones, distingue siempre:

                **ALCANCE = impresiones**

                **VOLUMEN DE INTERACCIÓN = interacciones absolutas**

                **EFICIENCIA DE INTERACCIÓN = engagement**

                No utilices una dimensión como sustituta de otra ni supongas que mejorar una implica automáticamente mejorar las demás.

                ---

                # 6.6 — RELACIÓN CON LOS EXPERIMENTOS

                Una recomendación puede proponer experimentar, pero el diseño experimental corresponde al **BLOQUE 7**.

                No desarrolles aquí:

                * hipótesis completas;
                * variables de control;
                * duración;
                * criterios de éxito;
                * diseño experimental detallado.

                El Bloque 6 decide **qué merece hacerse**.

                El Bloque 7 determina **cómo comprobarlo**.

                ---

                # 6.7 — REGLA FINAL

                Antes de generar una recomendación, verifica internamente:

                1. ¿Qué comportamiento concreto de esta cuenta la origina?
                2. ¿Qué evidencia lo respalda?
                3. ¿Qué significa y qué permanece incierto?
                4. ¿Qué decisión concreta puede ejecutarse?
                5. ¿Qué dimensión pretende mantener, mejorar o investigar?
                6. ¿Cómo podrá comprobarse posteriormente?

                Si estas preguntas no pueden responderse con la información disponible, simplifica la recomendación o sustitúyela por una acción de investigación o recopilación de datos.

                **No generes recomendaciones por obligación.**

                El resultado debe permitir pasar directamente de:

                **DIAGNÓSTICO → PRIORIDAD → ACCIÓN**

                sin introducir información nueva ni consejos genéricos.


                # ======================================================

                # BLOQUE 7 — EXPERIMENTOS Y PRÓXIMOS PASOS

                # ======================================================

                Convierte las hipótesis relevantes del análisis en experimentos destinados a **reducir incertidumbre y generar aprendizaje útil para la cuenta**.

                No repitas el diagnóstico ni generes consejos genéricos. Un experimento solo debe plantearse cuando exista una hipótesis razonablemente sustentada por los datos.

                ## 7.1 — HIPÓTESIS Y VARIABLES

                La hipótesis debe expresar algo que los datos sugieren pero todavía no permiten demostrar.

                Utiliza únicamente:

                * variables ya disponibles; o
                * variables que puedan registrarse explícitamente durante el experimento.

                Si la hipótesis requiere información inexistente, el experimento debe servir primero para recopilarla.

                No inventes características de publicaciones, como temas, formatos, horarios, hashtags, imágenes, vídeos, títulos, CTA, audiencia, estructura o comportamiento del algoritmo.

                ## 7.2 — DISEÑO DEL EXPERIMENTO

                Cuando sea viable, cada experimento debe definir:

                * HIPÓTESIS
                * PREGUNTA
                * VARIABLE A OBSERVAR
                * QUÉ SE MODIFICA
                * QUÉ SE MANTIENE CONSTANTE
                * MÉTRICA PRINCIPAL
                * MÉTRICAS SECUNDARIAS
                * REFERENCIA DE COMPARACIÓN
                * DURACIÓN O NÚMERO DE PUBLICACIONES
                * CRITERIO DE EVALUACIÓN
                * DECISIÓN POSTERIOR

                Cuando sea posible, modifica una variable relevante manteniendo constantes las demás condiciones observables para facilitar la comparación.

                El diseño experimental no demuestra causalidad por sí mismo; debe presentarse como una forma de obtener evidencia y reducir incertidumbre.

                ## 7.3 — REFERENCIA Y MÉTRICAS

                Compara los resultados con referencias disponibles en los datos históricos, como:

                * mediana o media histórica;
                * engagement histórico;
                * publicaciones comparables;
                * distribución histórica;
                * otros valores calculados por Python.

                No inventes objetivos numéricos ni umbrales de éxito.

                Selecciona las métricas según la pregunta del experimento y distingue siempre entre:

                * ALCANCE = impresiones;
                * VOLUMEN = interacciones absolutas;
                * EFICIENCIA = engagement.

                No utilices una dimensión como sustituta de otra.

                ## 7.4 — CANTIDAD Y PRIORIDAD

                No existe un número obligatorio de experimentos.

                Es preferible una pequeña cantidad de experimentos sólidos frente a una lista extensa de pruebas genéricas.

                Cuando existan varios, priorízalos por:

                1. relevancia de la incertidumbre;
                2. evidencia disponible;
                3. facilidad de ejecución;
                4. capacidad de aprendizaje;
                5. utilidad de la decisión posterior.

                La prioridad representa **valor potencial de aprendizaje**, no probabilidad de éxito.

                ## 7.5 — EVALUACIÓN Y APRENDIZAJE

                El criterio de evaluación debe responder directamente a la pregunta planteada y compararse con una referencia concreta.

                El resultado debe distinguir:

                * resultado observado;
                * diferencia respecto a la referencia;
                * posible interpretación;
                * incertidumbre restante;
                * aprendizaje obtenido.

                No conviertas automáticamente un resultado favorable en una regla general.

                La pregunta final del experimento debe ser:

                **¿QUÉ HEMOS APRENDIDO Y QUÉ CAMBIA AHORA EN NUESTRA DECISIÓN?**

                ## 7.6 — DECISIÓN Y LIMITACIONES

                Siempre que sea posible, el experimento debe desembocar en una decisión potencial:

                * mantener;
                * repetir;
                * ampliar la muestra;
                * investigar otra variable;
                * descartar la hipótesis;
                * reformularla;
                * recopilar datos adicionales.

                La decisión debe depender del resultado observado, no estar predeterminada.

                Si no existe evidencia suficiente para diseñar un experimento sólido, no generes uno para completar la sección. Indica qué información falta, qué debería registrarse y qué pregunta permitiría responder.

                ## 7.7 — REGLA FINAL

                Todo experimento válido debe poder seguir esta cadena:

                **HALLAZGO → HIPÓTESIS → PREGUNTA → PRUEBA → MÉTRICA → COMPARACIÓN → APRENDIZAJE → DECISIÓN**

                Si la cadena no puede construirse con la información disponible, no inventes el experimento.

                El objetivo de este bloque no es producir más recomendaciones, sino transformar las incertidumbres relevantes de la cuenta en **oportunidades concretas de aprendizaje y mejora de su trayectoria**.


                # ======================================================

                # BLOQUE 8 — AUDITORÍA FINAL DE LA RESPUESTA

                # ======================================================

                Antes de entregar el informe, realiza una **auditoría de calidad de la respuesta generada**.

                Esta fase NO debe volver a analizar la cuenta ni generar nuevas conclusiones. Su función es comprobar que el análisis ya realizado cumple las reglas del prompt y que la respuesta final es fiel a los datos y a la evidencia disponible.

                ## 8.1 — INTEGRIDAD DE DATOS

                Comprueba que:

                * las métricas coinciden con los valores proporcionados por Python;
                * no existen métricas inventadas o alteradas;
                * no se han introducido datos no disponibles;
                * rankings, porcentajes, medias y comparaciones son coherentes con los datos originales.

                Si detectas un error, corrígelo antes de entregar el informe.

                ## 8.2 — ESTRUCTURA

                Comprueba que el informe contiene **exactamente las 14 secciones establecidas**, en el orden establecido y con sus nombres correspondientes.

                No añadas, elimines, combines ni dividas secciones principales.

                ## 8.3 — CONSISTENCIA ANALÍTICA

                Comprueba que las conclusiones:

                * son compatibles con los datos;
                * no se contradicen entre sí;
                * respetan el flujo analítico del informe;
                * no presentan como conclusión algo que posteriormente el propio informe contradice.

                Cada sección debe cumplir su función específica y evitar repetir innecesariamente conclusiones ya desarrolladas.

                ## 8.4 — NIVEL DE CERTEZA

                Comprueba que el lenguaje utilizado corresponde al nivel real de evidencia.

                No deben aparecer como hechos:

                * hipótesis;
                * correlaciones;
                * posibles causas;
                * interpretaciones no demostradas.

                Cuando exista incertidumbre relevante, debe quedar expresada.

                ## 8.5 — NO INVENCIÓN

                Comprueba que no se hayan inventado:

                * temas;
                * títulos;
                * formatos;
                * horarios;
                * hashtags;
                * imágenes;
                * vídeos;
                * CTA;
                * audiencias;
                * intenciones;
                * causas;
                * calidad;
                * relevancia;
                * características de publicaciones no disponibles.

                Una URL no debe utilizarse como evidencia suficiente de características del contenido cuando estas no estén disponibles.

                ## 8.6 — NO REPETICIÓN

                Comprueba que el informe no repite mecánicamente:

                * métricas;
                * conclusiones;
                * diagnósticos;
                * recomendaciones.

                Una misma evidencia puede aparecer cuando sea necesaria para contextualizar otra sección, pero cada sección debe aportar una función diferente.

                ## 8.7 — ESPECIFICIDAD Y UTILIDAD

                Comprueba que las conclusiones y recomendaciones están vinculadas a hallazgos concretos de esta cuenta.

                Elimina consejos genéricos que podrían aplicarse literalmente a cualquier perfil.

                Comprueba además que las recomendaciones aportan valor para la trayectoria profesional del analizado y no se limitan a optimizar métricas por sí mismas.

                ## 8.8 — CORRECCIÓN FINAL

                Comprueba que:

                * no existen contradicciones numéricas;
                * no quedan afirmaciones excesivas;
                * no se confunde actividad con experiencia;
                * no se confunden alcance, interacciones y engagement;
                * las recomendaciones proceden de hallazgos previamente justificados;
                * los experimentos planteados sirven para comprobar hipótesis o reducir incertidumbres reales.

                Si una conclusión no supera esta auditoría, debe eliminarse o reformularse antes de entregar el informe.

                ## 8.9 — CRITERIO DE APROBACIÓN

                La respuesta solo está preparada para entregarse cuando cumple simultáneamente:

                **DATOS CORRECTOS + ESTRUCTURA CORRECTA + EVIDENCIA SUFICIENTE + COHERENCIA + ESPECIFICIDAD + UTILIDAD PROFESIONAL**

                La auditoría no debe generar un nuevo diagnóstico.

                Su única función es garantizar que el diagnóstico ya construido sea **fiel, verificable, coherente y útil**.


                # ======================================================

                # BLOQUE 9 — PREPARACIÓN DEL CONTENIDO PARA MAQUETACIÓN

                # ======================================================

                ## 9.1 — FUNCIÓN, FUENTE DE VERDAD Y ALCANCE

                Este bloque recibe exclusivamente el análisis auditado y validado por el BLOQUE 8 y lo transforma en contenido estructurado para su posterior maquetación por Python.

                FLUJO:

                MÓDULOS 0–7 → ANÁLISIS
                BLOQUE 8 → AUDITORÍA
                BLOQUE 9 → CONTENIDO ESTRUCTURADO
                PYTHON → MAQUETACIÓN HTML + CSS → PDF

                El BLOQUE 9 NO debe:

                * reinterpretar el análisis;
                * añadir hallazgos, conclusiones, recomendaciones o experimentos;
                * introducir causalidad nueva;
                * inventar, completar, estimar o modificar datos;
                * generar HTML o CSS;
                * incluir instrucciones de diseño.

                El análisis auditado del BLOQUE 8 es la FUENTE DE VERDAD.

                La presentación visual corresponde exclusivamente a Python.

                ---

                ## 9.2 — INTEGRIDAD Y FIDELIDAD

                Conservar sin alteración:

                * cifras y métricas;
                * fechas y posiciones;
                * impresiones e interacciones;
                * engagement;
                * URLs;
                * conclusiones y diagnóstico;
                * recomendaciones;
                * hipótesis y experimentos;
                * nivel de certeza;
                * metadatos oficiales proporcionados por Python.

                No introducir información, interpretación, recomendación, experimento o causalidad que no esté respaldada por el análisis auditado.

                Si una información no está disponible o no puede verificarse, no inventarla ni completarla.

                ---

                ## 9.3 — ESTRUCTURA OBLIGATORIA

                Conservar exactamente estas 14 secciones, en este orden, sin añadir, eliminar, combinar ni dividir:

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

                Si una sección está limitada por falta de datos, debe conservarse y expresar la limitación correspondiente.

                ---

                ## 9.4 — CONTRATO JSON

                La salida debe ser exclusivamente JSON válido.

                No incluir Markdown, bloques de código, explicaciones externas, HTML ni CSS.

                Las únicas claves principales permitidas son:

                * `metadata`
                * `sections`

                `metadata` debe contener únicamente metadatos oficiales proporcionados por Python.

                `sections` debe contener exactamente 14 elementos, uno por cada sección y en el orden establecido.

                Cada sección debe tener:

                * `number`
                * `title`
                * `content`

                `number` debe corresponder al número real.

                `title` debe coincidir exactamente con el nombre oficial.

                `content` contiene únicamente los elementos analíticos necesarios para esa sección.

                No crear elementos visuales ni instrucciones de diseño dentro del JSON.

                ---

                ## 9.5 — TIPOS DE CONTENIDO PERMITIDOS

                Utilizar únicamente estos tipos:

                * `text`
                * `metric`
                * `table`
                * `insight`
                * `diagnosis`
                * `recommendation`
                * `experiment`
                * `limitation`

                Cada elemento debe indicar su `type`.

                ### `text`

                Campos:

                * `type`
                * `text`

                ### `metric`

                Campos:

                * `type`
                * `label`
                * `value`

                ### `table`

                Campos:

                * `type`
                * `columns`
                * `rows`

                ### `insight`

                Campos:

                * `type`
                * `label`
                * `text`

                ### `diagnosis`

                Campos:

                * `type`
                * categoría correspondiente
                * contenido del diagnóstico

                ### `recommendation`

                Campos disponibles:

                * `type`
                * `priority`
                * `finding`
                * `evidence`
                * `interpretation`
                * `action`
                * `verification`

                ### `experiment`

                Campos disponibles:

                * `type`
                * `hypothesis`
                * `variable`
                * `change`
                * `metric`
                * `reference`
                * `success_criterion`
                * `subsequent_decision`

                ### `limitation`

                Campos:

                * `type`
                * `text`

                Utilizar únicamente los campos que correspondan al contenido real. No crear campos vacíos para completar estructuras.

                ---

                ## 9.6 — PUBLICACIONES, TABLAS Y METADATOS

                Las secciones 8, 9 y 10 deben conservar TODOS los registros proporcionados por Python.

                Reglas:

                * no eliminar publicaciones;
                * no resumir tablas;
                * no utilizar `etc.`, `más publicaciones` ni placeholders;
                * no modificar, redondear ni sustituir valores;
                * conservar las columnas y datos reales disponibles;
                * conservar las URLs exactamente.

                Los metadatos proporcionados por Python deben conservarse sin modificación.

                Pueden incluir, cuando existan:

                * usuario;
                * periodo;
                * fecha de inicio;
                * fecha de fin;
                * fecha de generación;
                * estado;
                * versión.

                No inventar metadatos ausentes.

                ---

                ## 9.7 — RESPONSABILIDAD DE PYTHON

                Python controla exclusivamente la presentación posterior:

                * HTML/CSS;
                * colores;
                * tipografías;
                * tamaños;
                * márgenes;
                * espaciados;
                * tablas y bloques visuales;
                * jerarquía visual;
                * saltos de página;
                * adaptación al PDF.

                La IA debe entregar únicamente contenido estructurado y no incluir instrucciones visuales o de diseño.

                ---

                ## 9.8 — VALIDACIÓN FINAL

                Antes de devolver la respuesta, comprobar:

                1. El resultado es JSON válido.
                2. Las únicas claves principales son `metadata` y `sections`.
                3. Existen exactamente 14 secciones.
                4. Están en el orden establecido.
                5. Sus nombres son exactos.
                6. Cada sección contiene `number`, `title` y `content`.
                7. Los tipos utilizados están permitidos.
                8. Los datos coinciden con el análisis auditado.
                9. Las tablas contienen todos los registros disponibles.
                10. Las URLs no han sido modificadas.
                11. No existen datos, interpretaciones o causalidades inventadas.
                12. No existen recomendaciones ni experimentos nuevos.
                13. No existe HTML, CSS ni información de diseño.

                # ======================================================

                # FIN DEL BLOQUE 9

                # ======================================================


                """
                    
                # ======================================================
                # CONTROL DE TAMAÑO DEL PROMPT
                # ======================================================

                total_caracteres_prompt = (
                    len(system_prompt)
                    + len(analytics_text)
                    + len(ssi_text)
                    + len(sector_real)
                    + len(intereses_real)
                )

                total_tokens_aprox = total_caracteres_prompt // 4

                print("===== CONTROL DE TAMAÑO DEL PROMPT =====")
                print("Caracteres aproximados:", total_caracteres_prompt)
                print("Tokens aproximados:", total_tokens_aprox)
                print("===== FIN CONTROL =====")
                               
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

                    analysis_json = json.loads(analysis_json_text)

                except json.JSONDecodeError as e:

                    st.error(
                        f"❌ El Módulo 9 no devolvió un JSON válido: {e}"
                    )

                    st.code(
                        analysis_json_text[:5000]
                    )

                    st.stop()


                # --------------------------------------------------
                # VALIDACIÓN DEL JSON DEL MÓDULO 9
                # --------------------------------------------------

                if not isinstance(analysis_json, dict):

                    st.error(
                        "❌ El Módulo 9 no ha devuelto un objeto JSON."
                    )

                    st.stop()


                # --------------------------------------------------
                # COMPROBAR ESTRUCTURA PRINCIPAL
                # --------------------------------------------------

                if "metadata" not in analysis_json:

                    st.error(
                        "❌ El JSON no contiene la clave 'metadata'."
                    )

                    st.stop()


                if "sections" not in analysis_json:

                    st.error(
                        "❌ El JSON no contiene la clave 'sections'."
                    )

                    st.stop()


                # --------------------------------------------------
                # COMPROBAR LAS 14 SECCIONES
                # --------------------------------------------------

                sections = analysis_json["sections"]

                if not isinstance(sections, list):

                    st.error(
                        "❌ La clave 'sections' no contiene una lista."
                    )

                    st.stop()


                if len(sections) != 14:

                    st.error(
                        f"❌ El Módulo 9 ha devuelto {len(sections)} "
                        f"secciones en lugar de 14."
                    )

                    st.stop()


                # --------------------------------------------------
                # VALIDACIÓN DE LOS TIPOS DE CONTENIDO
                # --------------------------------------------------

                TIPOS_PERMITIDOS = {
                    "text",
                    "metric",
                    "table",
                    "insight",
                    "diagnosis",
                    "recommendation",
                    "experiment",
                    "limitation"
                }
                # --------------------------------------------------
                # VALIDACIÓN ESPECÍFICA DE DIAGNOSIS
                # --------------------------------------------------

                CATEGORIAS_DIAGNOSIS = {
                    "FORTALEZA",
                    "LIMITACIÓN",
                    "OPORTUNIDAD",
                    "ANOMALÍA",
                    "INCERTIDUMBRE",
                    "PRIORIDAD ESTRATÉGICA"
                }

                # ==================================================
                # VALIDACIÓN ESTRUCTURAL DE CADA ELEMENTO
                # ==================================================

                def validar_item_contenido(item):

                    if not isinstance(item, dict):
                        return False, "El elemento no es un objeto JSON."

                    item_type = item.get("type")

                    if item_type not in TIPOS_PERMITIDOS:
                        return False, (
                            f"Tipo de contenido no permitido: {item_type}"
                        )


                    # --------------------------------------------------
                    # TEXT
                    # --------------------------------------------------

                    if item_type == "text":

                        if "text" not in item:
                            return False, (
                                "Un elemento text debe contener 'text'."
                            )

                        if not isinstance(item["text"], str):
                            return False, (
                                "El campo 'text' debe ser texto."
                            )


                    # --------------------------------------------------
                    # METRIC
                    # --------------------------------------------------

                    elif item_type == "metric":

                        campos = {
                            "type",
                            "label",
                            "value"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento metric está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )

                        if not isinstance(item["label"], str):
                            return False, (
                                "El campo 'label' de metric debe ser texto."
                            )

                        if item["value"] is None:
                            return False, (
                                "El campo 'value' de metric "
                                "no puede ser None."
                            )


                    # --------------------------------------------------
                    # INSIGHT
                    # --------------------------------------------------

                    elif item_type == "insight":

                        campos = {
                            "type",
                            "label",
                            "text"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento insight está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )

                        if not isinstance(item["label"], str):
                            return False, (
                                "El campo 'label' de insight debe ser texto."
                            )

                        if not isinstance(item["text"], str):
                            return False, (
                                "El campo 'text' de insight debe ser texto."
                            )


                    # --------------------------------------------------
                    # DIAGNOSIS
                    # --------------------------------------------------

                    elif item_type == "diagnosis":

                        campos = {
                            "type",
                            "category",
                            "content"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento diagnosis está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )

                        if item["category"] not in CATEGORIAS_DIAGNOSIS:
                            return False, (
                                f"Categoría diagnosis no válida: "
                                f"{item['category']}"
                            )

                        if not isinstance(item["content"], str):
                            return False, (
                                "El campo 'content' de diagnosis "
                                "debe ser texto."
                            )


                    # --------------------------------------------------
                    # LIMITATION
                    # --------------------------------------------------

                    elif item_type == "limitation":

                        campos = {
                            "type",
                            "text"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento limitation está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )

                        if not isinstance(item["text"], str):
                            return False, (
                                "El campo 'text' de limitation "
                                "debe ser texto."
                            )


                    # --------------------------------------------------
                    # RECOMMENDATION
                    # --------------------------------------------------

                    elif item_type == "recommendation":

                        campos = {
                            "type",
                            "priority",
                            "finding",
                            "evidence",
                            "interpretation",
                            "action",
                            "verification"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento recommendation está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )


                    # --------------------------------------------------
                    # EXPERIMENT
                    # --------------------------------------------------

                    elif item_type == "experiment":

                        campos = {
                            "type",
                            "hypothesis",
                            "variable",
                            "change",
                            "metric",
                            "reference",
                            "success_criterion",
                            "subsequent_decision"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento experiment está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )


                    # --------------------------------------------------
                    # TABLE
                    # --------------------------------------------------

                    elif item_type == "table":

                        campos = {
                            "type",
                            "columns",
                            "rows"
                        }

                        faltantes = campos - set(item.keys())

                        if faltantes:
                            return False, (
                                f"Un elemento table está incompleto. "
                                f"Faltan: {sorted(faltantes)}"
                            )

                        if not isinstance(item["columns"], list):
                            return False, (
                                "'columns' de table debe ser una lista."
                            )

                        if not isinstance(item["rows"], list):
                            return False, (
                                "'rows' de table debe ser una lista."
                            )


                    return True, None


                # ==================================================
                # EJECUTAR VALIDACIÓN ESTRUCTURAL
                # ==================================================

                errores_estructura = []


                for section_index, section in enumerate(sections):

                    # --------------------------------------------------
                    # VALIDAR SECCIÓN
                    # --------------------------------------------------

                    if not isinstance(section, dict):

                        errores_estructura.append(
                            f"Sección {section_index + 1}: "
                            "no es un objeto JSON."
                        )

                        continue


                    # --------------------------------------------------
                    # VALIDAR CONTENT
                    # --------------------------------------------------

                    contenido = section.get("content", [])


                    if not isinstance(contenido, list):

                        errores_estructura.append(
                            f"Sección {section_index + 1}: "
                            "'content' no contiene una lista."
                        )

                        continue


                    # --------------------------------------------------
                    # VALIDAR CADA ELEMENTO
                    # --------------------------------------------------

                    for item_index, item in enumerate(contenido):

                        valido, error = validar_item_contenido(item)


                        if not valido:

                            errores_estructura.append(
                                f"Sección {section_index + 1}, "
                                f"elemento {item_index + 1}: "
                                f"{error}"
                            )


                # ==================================================
                # DETENER SI EXISTEN ERRORES ESTRUCTURALES
                # ==================================================

                if errores_estructura:

                    st.error(
                        "❌ La respuesta de la IA presenta "
                        "anomalías estructurales y no puede "
                        "continuar hacia la maquetación."
                    )


                    st.error(
                        f"Se han detectado "
                        f"{len(errores_estructura)} "
                        "errores estructurales."
                    )


                    with st.expander(
                        "🔎 Ver errores estructurales detectados"
                    ):

                        for error in errores_estructura:

                            st.write(
                                f"• {error}"
                            )


                    with st.expander(
                        "🧠 Ver JSON recibido"
                    ):

                        st.json(
                            analysis_json
                        )


                    st.stop()


                # ==================================================
                # JSON VALIDADO
                # ==================================================

                st.success(
                    "✅ JSON recibido y validado correctamente: "
                    "metadata + 14 secciones + estructura "
                    "de contenidos válida."
                )

                # ======================================================
                # GENERACIÓN DEL HTML
                # ======================================================

                html_content = generar_html(analysis_json)

                st.success(
                    "✅ HTML generado correctamente."
                )

                st.markdown(
                    "### Vista Previa del Informe Ejecutivo"
                )

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
                # GENERACIÓN DEL PDF — GOOGLE CHROME / CHROMIUM
                # ======================================================

                pdf_buffer = io.BytesIO()

                try:

                    # --------------------------------------------------
                    # LOCAL WINDOWS / STREAMLIT CLOUD LINUX
                    # --------------------------------------------------

                    chrome_candidates = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        "/usr/bin/chromium",
                        "/usr/bin/chromium-browser",
                        "/usr/bin/google-chrome",
                    ]

                    chrome_path = next(
                        (
                            path
                            for path in chrome_candidates
                            if os.path.exists(path)
                        ),
                        None
                    )

                    if not chrome_path:

                        raise FileNotFoundError(
                            "No se encontró Google Chrome/Chromium "
                            "en el entorno de ejecución."
                        )

                    # --------------------------------------------------
                    # ARCHIVOS TEMPORALES
                    # --------------------------------------------------

                    with tempfile.TemporaryDirectory() as temp_dir:

                        html_path = os.path.join(
                            temp_dir,
                            "auditoria.html"
                        )

                        pdf_path = os.path.join(
                            temp_dir,
                            "auditoria.pdf"
                        )

                        # --------------------------------------------------
                        # GUARDAR HTML
                        # --------------------------------------------------

                        with open(
                            html_path,
                            "w",
                            encoding="utf-8"
                        ) as f:

                            f.write(html_content)

                        # --------------------------------------------------
                        # EJECUTAR CHROME / CHROMIUM HEADLESS
                        # --------------------------------------------------

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

                        # --------------------------------------------------
                        # LEER PDF
                        # --------------------------------------------------

                        with open(
                            pdf_path,
                            "rb"
                        ) as f:

                            pdf_buffer.write(
                                f.read()
                            )

                    pdf_buffer.seek(0)

                    st.success(
                        "✅ PDF generado correctamente con Chrome/Chromium."
                    )

                    st.download_button(
                        label="📥 Descargar Auditoría Estratégica en PDF",
                        data=pdf_buffer,
                        file_name="Auditoria_LinkedIn_Premium.pdf",
                        mime="application/pdf",
                        key="descargar_auditoria_pdf"
                    )

                except Exception as e:
                
                    import traceback

                    st.error(
                        f"Error crítico en el motor de análisis: {e}"
                    )

                    st.code(
                        traceback.format_exc(),
                        language="text"
                    )

                    st.stop()
        # ======================================================
        # FIN DEL TRY PRINCIPAL DE LA AUDITORÍA
        # ======================================================

            except Exception as e:

                import traceback

                st.error(
                    f"Error crítico en el motor de análisis: {e}"
                )

                st.code(
                    traceback.format_exc(),
                    language="text"
                )

                st.stop()
