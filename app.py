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
# CABECERA PRINCIPAL
# ======================================================

st.markdown("""
<style>

.app-header {
    background: linear-gradient(
        135deg,
        #123B5D 0%,
        #0A66C2 100%
    );
    color: white;
    padding: 34px 38px 32px;
    border-radius: 18px;
    margin-bottom: 26px;
    box-shadow: 0 8px 24px rgba(18, 59, 93, 0.14);
}

.app-kicker {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.6px;
    opacity: 0.78;
    margin-bottom: 9px;
}

.app-title {
    font-size: 32px;
    line-height: 1.15;
    font-weight: 750;
    margin: 0 0 10px 0;
}

.app-subtitle {
    font-size: 15px;
    line-height: 1.55;
    opacity: 0.92;
    margin: 0;
    max-width: 760px;
}

.app-badge {
    display: inline-block;
    margin-top: 17px;
    padding: 6px 11px;
    border-radius: 20px;
    background: rgba(255,255,255,0.11);
    border: 1px solid rgba(255,255,255,0.20);
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
}

</style>
""", unsafe_allow_html=True)

st.html("""
<div class="app-header">

    <div class="app-kicker">
        RUTA TI · HERRAMIENTA DE ANÁLISIS
    </div>

    <div class="app-title">
        Auditoría Estratégica de LinkedIn
    </div>

    <p class="app-subtitle">
        Convierte tus datos reales de LinkedIn en un diagnóstico claro:
        descubre qué está funcionando, qué necesita mejorar y qué deberías
        comprobar a continuación.
    </p>

    <div class="app-badge">
        Datos reales · Evidencia · Diagnóstico · Acción
    </div>

</div>
""")

with st.expander(
    "ℹ️ Cómo funciona · privacidad y transparencia",
    expanded=False
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
# FLUJO DE LA AUDITORÍA
# ======================================================

# ======================================================
# MAPA DEL PROCESO
# ======================================================

st.markdown("## Tu auditoría en 4 pasos")

st.markdown(
    "Tú aportas los datos. Nosotros los convertimos en análisis."
)

st.markdown("""
<style>

.audit-steps {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 18px 0 28px;
}

.audit-step {
    background: #F8FAFC;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 17px 16px 16px;
    min-height: 145px;
    position: relative;
}

.audit-step::before {
    content: "";
    display: block;
    width: 28px;
    height: 3px;
    border-radius: 4px;
    background: #0A66C2;
    margin-bottom: 14px;
}

.audit-step-number {
    color: #0A66C2;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    margin-bottom: 5px;
}

.audit-step-title {
    color: #123B5D;
    font-size: 14px;
    font-weight: 750;
    margin-bottom: 8px;
}

.audit-step-text {
    color: #5B6472;
    font-size: 12px;
    line-height: 1.5;
}

@media (max-width: 900px) {

    .audit-steps {
        grid-template-columns: repeat(2, 1fr);
    }

}

@media (max-width: 600px) {

    .audit-steps {
        grid-template-columns: 1fr;
    }

}

</style>
""", unsafe_allow_html=True)

st.html("""
<div class="audit-steps">

    <div class="audit-step">
        <div class="audit-step-number">01</div>
        <div class="audit-step-title">CONTEXTO</div>
        <div class="audit-step-text">
            Define tu ámbito profesional y los temas en los que quieres
            posicionarte.
        </div>
    </div>

    <div class="audit-step">
        <div class="audit-step-number">02</div>
        <div class="audit-step-title">DATOS</div>
        <div class="audit-step-text">
            Aporta tu SSI y el histórico real de actividad de LinkedIn.
        </div>
    </div>

    <div class="audit-step">
        <div class="audit-step-number">03</div>
        <div class="audit-step-title">PUBLICACIONES</div>
        <div class="audit-step-text">
            Añade el contenido real de las publicaciones seleccionadas.
        </div>
    </div>

    <div class="audit-step">
        <div class="audit-step-number">04</div>
        <div class="audit-step-title">AUDITORÍA</div>
        <div class="audit-step-text">
            Obtén diagnóstico, recomendaciones, experimentos y PDF.
        </div>
    </div>

</div>
""")

# ======================================================
# 1. CREDENCIALES DE SEGURIDAD
# ======================================================

with st.sidebar:

    with st.expander("⚙ Configuración avanzada", expanded=False):

        st.caption(
            "Configuración necesaria para ejecutar la auditoría."
        )

        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="Pega tu clave sk-..."
        )

        st.caption(
            "La clave se utiliza para ejecutar el análisis mediante la API."
        )

# ======================================================
# PASO 01 — CONTEXTO PROFESIONAL
# ======================================================

st.markdown("## 01 · Cuéntanos dónde quieres crecer")

st.markdown(
    "Este contexto ayuda a personalizar la interpretación y las "
    "recomendaciones. No modifica tus métricas ni crea evidencia."
)

col1, col2 = st.columns(2)

with col1:

    sector = st.text_input(
        "¿Cuál es tu ámbito profesional?",
        placeholder=(
            "Ej.: Formación Profesional Informática, "
            "Ciberseguridad, Redes..."
        )
    )

with col2:

    intereses = st.text_input(
        "¿Sobre qué temas quieres posicionarte?",
        placeholder=(
            "Ej.: SMR, ASIR, Redes, Empleo, "
            "Sistemas..."
        )
    )

fecha_alta = st.date_input(
    "¿Desde cuándo trabajas estratégicamente tu presencia en LinkedIn?",
    date(2026, 3, 1)
)

st.caption(
    "La fecha se utiliza como contexto temporal y no sustituye "
    "el periodo real disponible en tus datos."
)

st.divider()

# ======================================================
# PASO 02 — DATOS REALES DE LINKEDIN
# ======================================================

st.markdown("## 02 · Aporta tus datos reales de LinkedIn")

st.markdown(
    "Necesitamos dos fuentes distintas para construir una visión "
    "más completa de tu actividad."
)

col1, col2 = st.columns(2)

with col1:

    st.markdown("### 🎯 Tu SSI")

    st.caption(
        "Una fotografía de tu posicionamiento actual dentro de LinkedIn."
    )

    ssi_image = st.file_uploader(
        "Selecciona tu captura SSI",
        type=["png", "jpg", "jpeg"],
        key="ssi_image_uploader"
    )

    if ssi_image:
        st.success("✓ Captura SSI recibida")

    st.link_button(
        "Consultar mi SSI en LinkedIn ↗",
        "https://www.linkedin.com/sales/ssi/"
    )

with col2:

    st.markdown("### 📊 Tus analíticas")

    st.caption(
        "Datos de actividad, impresiones e interacciones de tus publicaciones."
    )

    analytics_file = st.file_uploader(
        "Selecciona tu archivo analítico",
        type=["xlsx", "pdf"],
        key="analytics_file_uploader"
    )

    if analytics_file:
        st.success("✓ Archivo analítico recibido")

    st.link_button(
        "Importar datos de LinkedIn ↗",
        "https://www.linkedin.com/analytics/creator/content/"
    )

st.divider()

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


    linkedin_name = metadata.get(
        "usuario",
        "Usuario LinkedIn"
    )

    report_generated_at = (
        metadata.get("fecha_generacion")
        or metadata.get("fecha_de_generacion")
        or metadata.get("fecha_generación")
        or metadata.get("fecha_de_generación")
        or "No disponible"
    )
 
    analysis_period = metadata.get(
        "periodo",
        "No disponible"
    )

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
            content = item.get("content", "")

            return f"""
            <div class="diagnosis">

                <div class="diagnosis-label">
                    {escapar(category)}
                </div>

                <div class="diagnosis-text">
                    {escapar(content)}
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

        print("DEBUG USUARIO:", linkedin_name)
        print("DEBUG FECHA:", report_generated_at)
        print("DEBUG PERIODO:", analysis_period)



        return ""

    # ======================================================
    # METADATOS
    # ======================================================

    usuario = escapar(
        metadata.get("usuario", "")
    )

    periodo = escapar(
        metadata.get("periodo", "")
    )

    fecha_inicio = escapar(
        metadata.get("fecha_inicio")
        or metadata.get("fecha_de_inicio", "")
    )

    fecha_fin = escapar(
        metadata.get("fecha_fin")
        or metadata.get("fecha_de_fin", "")
    )

    fecha_generacion = escapar(
        metadata.get("fecha_generacion")
        or metadata.get("fecha_de_generacion")
        or metadata.get("fecha_generación")
        or metadata.get("fecha_de_generación", "")
    )

    estado = escapar(
        metadata.get("estado", "")
    )

    version = escapar(
        metadata.get("version", "")
    )

    # ======================================================
    # DOCUMENTO HTML
    # ======================================================
    print("🔥 ANTES DE CONSTRUIR HTML")
    print("🔥 report_generated_at =", repr(report_generated_at))
    print("🔥 analysis_period =", repr(analysis_period))
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


# ======================================================
# ESTADO PERSISTENTE DE LA AUDITORÍA
# ======================================================

if "auditoria_activa" not in st.session_state:
    st.session_state.auditoria_activa = False


# ======================================================
# BOTÓN DE INICIO DE LA AUDITORÍA
# ======================================================

if st.button("➡️ Continuar y preparar mis publicaciones"):

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

        st.session_state.auditoria_activa = True


# ======================================================
# EJECUCIÓN PERSISTENTE DE LA AUDITORÍA
# ======================================================

if st.session_state.auditoria_activa:

    with st.spinner(
        "Generando auditoría corporativa y maquetando PDF ejecutivo... "
        "Por favor, espera."
    ):

        try:

            hoy = date.today()
            dias_activos = (hoy - fecha_alta).days
            meses_activos = max(1, round(dias_activos / 30.4))

            # ======================================================
            # IDENTIDAD DEL USUARIO
            # ======================================================

            linkedin_name = "Usuario LinkedIn"

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

                # ======================================================
                # ANALIZADOR
                # ======================================================

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

                publicaciones_contexto = destacadas.get(
                    "Top 5 Engagement Maduras",
                    []
                )

                # ==================================================
                # INICIALIZAR PUBLICACIONES EN SESSION STATE
                # ==================================================

                if "contenidos_publicaciones" not in st.session_state:

                    st.session_state.contenidos_publicaciones = []

                    for publicacion in publicaciones_contexto:

                        st.session_state.contenidos_publicaciones.append({
                            "URL": publicacion.get("URL", ""),
                            "Fecha": publicacion.get("Fecha"),
                            "Impresiones": publicacion.get("Impresiones"),
                            "Interacciones": publicacion.get("Interacciones"),
                            "Engagement": publicacion.get("Engagement"),
                            "Madurez": publicacion.get("Madurez"),
                            "Contenido": ""
                        })

                # ======================================================
                # PASO 03 — CONTEXTO DE PUBLICACIONES DESTACADAS
                # ======================================================

                st.markdown("## 03 · Dale contexto a tus publicaciones")

                st.info(
                    "**Las métricas nos dicen qué ocurrió.**\n\n"
                    "El contenido nos ayuda a entender qué estaba ocurriendo en esas "
                    "publicaciones. Copia el texto real de cada publicación para que la "
                    "auditoría pueda observar características presentes en ellas y "
                    "relacionarlas con sus resultados."
                )

                st.caption(
                    "No necesitas resumir ni editar el contenido. "
                    "Cópialo tal como fue publicado."
                )

                # ======================================================
                # ESTILOS DE LAS TARJETAS
                # ======================================================

                st.markdown("""
                <style>

                .publication-card {
                    background: #FFFFFF;
                    border: 1px solid #E5E7EB;
                    border-radius: 14px;
                    padding: 20px 22px 18px;
                    margin: 0 0 18px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.025);
                }

                .publication-card-header {
                    display:flex;
                    align-items:flex-start;
                    justify-content:space-between;
                    gap:18px;
                    margin-bottom:14px;
                }

                .publication-card-number {
                    color:#0A66C2;
                    font-size:10px;
                    font-weight:800;
                    text-transform:uppercase;
                    letter-spacing:0.8px;
                    margin-bottom:5px;
                }

                .publication-card-title {
                    color:#123B5D;
                    font-size:16px;
                    font-weight:750;
                    line-height:1.3;
                }

                .publication-status {
                    font-size:10px;
                    font-weight:700;
                    padding:5px 9px;
                    border-radius:18px;
                    white-space:nowrap;
                }

                .publication-status-ready {
                    background:#EAF7F0;
                    color:#198754;
                }

                .publication-status-pending {
                    background:#F3F4F6;
                    color:#6B7280;
                }

                .publication-metrics {
                    display:flex;
                    flex-wrap:wrap;
                    gap:8px;
                    margin:0 0 14px;
                }

                .publication-metric {
                    display:inline-block;
                    background:#F8FAFC;
                    border:1px solid #E5E7EB;
                    border-radius:7px;
                    padding:6px 9px;
                    color:#4B5563;
                    font-size:11px;
                }

                .publication-metric strong {
                    color:#123B5D;
                }

                .publication-content-label {
                    color:#6B7280;
                    font-size:10px;
                    font-weight:750;
                    text-transform:uppercase;
                    letter-spacing:0.05em;
                    margin:12px 0 6px;
                }

                </style>
                """, unsafe_allow_html=True)


                # ======================================================
                # MOSTRAR PUBLICACIONES
                # ======================================================

                for i, publicacion in enumerate(
                    st.session_state.contenidos_publicaciones,
                    1
                ):
                    url = publicacion.get("URL", "")

                    fecha = publicacion.get(
                        "Fecha",
                        "No disponible"
                    )

                    impresiones = publicacion.get(
                        "Impresiones",
                        "No disponible"
                    )

                    interacciones = publicacion.get(
                        "Interacciones",
                        "No disponible"
                    )

                    engagement = publicacion.get(
                        "Engagement",
                        "No disponible"
                    )

                    contenido_actual = publicacion.get(
                        "Contenido",
                        ""
                    ).strip()

                    completada = bool(contenido_actual)

                    estado_clase = (
                        "publication-status-ready"
                        if completada
                        else "publication-status-pending"
                    )

                    estado_texto = (
                        "✓ Contenido recibido"
                        if completada
                        else "Pendiente"
                    )

                    st.html(f"""
                    <div class="publication-card">

                        <div class="publication-card-header">

                            <div>

                                <div class="publication-card-number">
                                    PUBLICACIÓN DESTACADA · {i:02d}
                                </div>

                                <div class="publication-card-title">
                                    {fecha}
                                </div>

                            </div>

                            <div class="publication-status {estado_clase}">
                                {estado_texto}
                            </div>

                        </div>

                        <div class="publication-metrics">

                            <span class="publication-metric">
                                <strong>{impresiones}</strong> impresiones
                            </span>

                            <span class="publication-metric">
                                <strong>{interacciones}</strong> interacciones
                            </span>

                            <span class="publication-metric">
                                <strong>{engagement}%</strong> engagement
                            </span>

                        </div>

                    </div>
                    """)

                    if url:

                        st.link_button(
                            "Ver publicación en LinkedIn ↗",
                            url,
                            use_container_width=False
                        )

                    st.markdown(
                        '<div class="publication-content-label">'
                        '¿Qué publicaste?'
                        '</div>',
                        unsafe_allow_html=True
                    )

                    contenido = st.text_area(
                        "Contenido de la publicación",
                        value=contenido_actual,
                        key=f"contenido_publicacion_{i}",
                        height=180,
                        placeholder=(
                            "Copia y pega aquí el contenido tal como fue publicado..."
                        ),
                        label_visibility="collapsed"
                    )

                    st.session_state.contenidos_publicaciones[
                        i - 1
                    ]["Contenido"] = contenido

                    # ------------------------------------------------------
                    # PROGRESO
                    # ------------------------------------------------------

                    publicaciones_totales = len(
                        st.session_state.contenidos_publicaciones
                    )

                    publicaciones_completadas = sum(
                        1
                        for publicacion in st.session_state.contenidos_publicaciones
                        if publicacion.get("Contenido", "").strip()
                    )

                    st.markdown(
                        f"**Contenido aportado: "
                        f"{publicaciones_completadas} / {publicaciones_totales}**"
                    )

                    progreso = (
                        publicaciones_completadas / publicaciones_totales
                        if publicaciones_totales
                        else 0
                    )

                    st.progress(progreso)

                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown(
                        "<div style='height:4px'></div>",
                        unsafe_allow_html=True
                    )


                # ======================================================
                # RESUMEN DEL PROGRESO
                # ======================================================

                publicaciones_completadas = sum(
                    1
                    for publicacion in st.session_state.contenidos_publicaciones
                    if publicacion.get("Contenido", "").strip()
                )

                if publicaciones_completadas == publicaciones_totales:

                    st.success(
                        f"✓ Has completado las {publicaciones_totales} "
                        "publicaciones destacadas."
                    )

                elif publicaciones_completadas > 0:

                    st.info(
                        f"Has añadido contenido a {publicaciones_completadas} "
                        f"de {publicaciones_totales} publicaciones. "
                        "Puedes continuar cuando estés preparado."
                    )

                else:

                    st.info(
                        "Abre las publicaciones en nuevas pestañas, copia su contenido "
                        "y vuelve aquí. Los textos introducidos se conservarán."
                    )

                # ======================================================
                # QUÉ RECIBIRÁS
                # ======================================================

                st.markdown("## ¿Qué vas a recibir?")

                st.markdown(
                    "La auditoría combina tus datos, tus publicaciones y tu contexto "
                    "profesional para construir un informe estratégico personalizado."
                )

                resultado_col1, resultado_col2, resultado_col3 = st.columns(3)

                with resultado_col1:

                    st.markdown("### 📊 Radiografía")

                    st.caption(
                        "Tus principales métricas, distribución, alcance y engagement."
                    )

                with resultado_col2:

                    st.markdown("### 🧠 Diagnóstico")

                    st.caption(
                        "Fortaleza, limitación, oportunidad, anomalía, incertidumbre "
                        "y prioridad estratégica."
                    )

                with resultado_col3:

                    st.markdown("### 🎯 Acción")

                    st.caption(
                        "Recomendaciones y experimentos derivados de los hallazgos."
                    )

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

                resultado_col4, resultado_col5, resultado_col6 = st.columns(3)

                with resultado_col4:

                    st.markdown("### 🔎 Publicaciones")

                    st.caption(
                        "Análisis de los casos destacados y cruce entre alcance "
                        "y engagement."
                    )

                with resultado_col5:

                    st.markdown("### 🧪 Experimentos")

                    st.caption(
                        "Hipótesis que podrás comprobar con nuevos datos."
                    )

                with resultado_col6:

                    st.markdown("### 📄 Informe PDF")

                    st.caption(
                        "Un informe ejecutivo completo listo para consultar y descargar."
                    )

                st.divider()
                
                # ======================================================
                # CTA FINAL — GENERAR AUDITORÍA
                # ======================================================

                st.markdown("""
                <style>

                /* ==================================================
                BOTÓN PRINCIPAL DE LA AUDITORÍA
                ================================================== */

                .stButton > button[kind="primary"] {

                    width: 100% !important;

                    min-height: 58px !important;

                    border-radius: 12px !important;

                    border: 1px solid #0A66C2 !important;

                    background: linear-gradient(
                        135deg,
                        #123B5D 0%,
                        #0A66C2 100%
                    ) !important;

                    color: #FFFFFF !important;

                    font-size: 16px !important;

                    font-weight: 750 !important;

                    letter-spacing: 0.1px !important;

                    box-shadow:
                        0 6px 16px rgba(10, 102, 194, 0.18) !important;

                    transition:
                        transform 0.15s ease,
                        box-shadow 0.15s ease !important;

                }

                /* Hover */

                .stButton > button[kind="primary"]:hover {

                    transform: translateY(-1px);

                    box-shadow:
                        0 9px 22px rgba(10, 102, 194, 0.24) !important;

                    border-color: #0A66C2 !important;

                }

                /* Click */

                .stButton > button[kind="primary"]:active {

                    transform: translateY(0);

                    box-shadow:
                        0 4px 10px rgba(10, 102, 194, 0.18) !important;

                }

                </style>
                """, unsafe_allow_html=True)


                st.markdown("## ¿Todo preparado?")

                st.markdown(
                    """
                    <div style="
                        color:#5B6472;
                        font-size:13px;
                        line-height:1.55;
                        margin-bottom:14px;
                    ">
                        Tu contexto, tus datos y tus publicaciones ya están preparados.
                        Ahora puedes generar la auditoría estratégica completa.
                    </div>
                    """,
                    unsafe_allow_html=True
                )


                continuar_analisis = st.button(
                    "🚀  Generar mi auditoría",
                    key="continuar_analisis",
                    type="primary",
                    use_container_width=True
                )


                if continuar_analisis:
                    st.session_state.auditoria_activa = True
                else:
                    st.stop()

                # ==================================================
                # CONSTRUIR CONTEXTO CUALITATIVO PARA LA IA
                # ==================================================

                contexto_publicaciones = ""

                for i, publicacion in enumerate(
                    st.session_state.contenidos_publicaciones,
                    1
                ):

                    contenido = publicacion.get("Contenido", "").strip()

                    if not contenido:
                        continue

                    contexto_publicaciones += f"""
--- PUBLICACIÓN DESTACADA {i} ---

Fecha:
{publicacion.get("Fecha", "No disponible")}

Impresiones:
{publicacion.get("Impresiones", "No disponible")}

Interacciones:
{publicacion.get("Interacciones", "No disponible")}

Engagement:
{publicacion.get("Engagement", "No disponible")}%

Madurez:
{publicacion.get("Madurez", "No disponible")}

URL:
{publicacion.get("URL", "No disponible")}

CONTENIDO PROPORCIONADO POR EL USUARIO:
{contenido}

--- FIN PUBLICACIÓN {i} ---
"""

                # --------------------------------------------------
                # FALLBACK SI NO SE INTRODUJO NINGÚN CONTENIDO
                # --------------------------------------------------

                if not contexto_publicaciones:

                    contexto_publicaciones = (
                        "No se ha proporcionado contenido textual de publicaciones "
                        "destacadas para realizar análisis cualitativo."
                    )

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
# LINKEDIN ANALYTICAL AUDIT — SYSTEM PROMPT V2
# ======================================================

## 0. ROL Y PRINCIPIOS

Actúas como ANALISTA ESTRATÉGICO Y MENTOR especializado en analítica profesional de LinkedIn.

Tu misión es transformar los datos disponibles de ESTA CUENTA en conocimiento específico, riguroso y útil.

Flujo obligatorio:

DATOS → EVIDENCIA → INTERPRETACIÓN → DIAGNÓSTICO → DECISIÓN → APRENDIZAJE

Python es la fuente de verdad cuantitativa.

Reglas maestras:

* No inventes, alteres, sustituyas ni completes datos ausentes.
* No inventes publicaciones, métricas, características de contenido, causas, tendencias, audiencias o resultados.
* Distingue siempre HECHO, INDICIO e HIPÓTESIS.
* Los datos descriptivos muestran asociaciones o patrones; no demuestran causalidad.
* No atribuyas a una métrica consecuencias externas que no estén demostradas por los datos.
* Si una explicación requiere asumir una causa no observada, exprésala como hipótesis o indica que no puede determinarse.
* No confundas actividad con experiencia, autoridad, madurez estratégica o eficacia.
* No confundas alcance, interacciones y engagement.
* Una métrica alta no es automáticamente una fortaleza.
* Una métrica baja no es automáticamente una debilidad.
* Un caso excepcional no representa necesariamente el comportamiento habitual.
* Si faltan datos, expresa la limitación.
* Las recomendaciones deben derivarse de hallazgos concretos.
* Los experimentos deben comprobar hipótesis o reducir incertidumbre.
* No generes recomendaciones ni experimentos simplemente para completar la sección.

## REGLAS DE BLOQUEO

- Solo los DATOS OFICIALES proporcionados por Python constituyen evidencia.
  No inventar, completar ni introducir comparaciones externas no proporcionadas.

- No convertir directamente un dato en una acción. Toda recomendación debe
  derivarse de un hallazgo e interpretación sustentados. Si la causa no puede
  determinarse, expresarlo como incertidumbre o proponer únicamente una acción
  de observación, medición o registro.

- El CONTEXTO PROFESIONAL no crea evidencia. No atribuir a temas, formatos,
  horarios, CTA, audiencias, viralidad u otras características del contenido
  efectos que no hayan sido observados o analizados.

- Las interpretaciones excepcionales pueden describirse como tales cuando los
  datos las sustenten, pero no atribuirles una causa no demostrada.

Lenguaje proporcional:## REGLAS DE BLOQUEO

- Solo los DATOS OFICIALES proporcionados por Python constituyen evidencia.
  No inventar, completar ni introducir comparaciones externas no proporcionadas.

- No convertir directamente un dato en una acción. Toda recomendación debe
  derivarse de un hallazgo e interpretación sustentados. Si la causa no puede
  determinarse, expresarlo como incertidumbre o proponer únicamente una acción
  de observación, medición o registro.

- El CONTEXTO PROFESIONAL no crea evidencia. No atribuir a temas, formatos,
  horarios, CTA, audiencias, viralidad u otras características del contenido
  efectos que no hayan sido observados o analizados.

- Las interpretaciones excepcionales pueden describirse como tales cuando los
  datos las sustenten, pero no atribuirles una causa no demostrada.

HECHO:
"los datos muestran..."
"se observa..."

INDICIO:
"aparece un patrón..."
"esto podría indicar..."

HIPÓTESIS:
"una posible explicación es..."
"debería comprobarse..."

Cuando no pueda determinarse:
"no puede determinarse con los datos disponibles."

## 1. ARQUITECTURA FIJA

El informe debe contener EXACTAMENTE estas 14 secciones y en este orden:

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

No añadir, eliminar, combinar, dividir ni renombrar secciones.

Secuencia analítica:

DATOS → DISTRIBUCIÓN → ALCANCE → ENGAGEMENT → CRUCE → DIAGNÓSTICO → RECOMENDACIONES → EXPERIMENTOS

No adelantes conclusiones propias de secciones posteriores.

## 2. CONTENIDO

### 1. RESUMEN EJECUTIVO

Sintetiza únicamente:

* situación actual;
* principal fortaleza, si existe;
* principal limitación, si existe;
* principal oportunidad, si existe;
* principal incertidumbre;
* prioridad estratégica.

No enumeres métricas innecesarias ni introduzcas acciones nuevas.

### 2. ESTADO ACTUAL DEL PERFIL

Integra actividad, resultados, tracción y madurez estratégica cuando Python la proporcione.

Distingue siempre:
ACTIVIDAD ≠ RESULTADO ≠ EFICACIA ≠ EXPERIENCIA.

### 3. RADIOGRAFÍA CUANTITATIVA

Presenta las principales métricas proporcionadas por Python y explica conjuntamente qué muestran.

No inventes ni recalcules métricas que Python no proporcione.

### 4. DISTRIBUCIÓN DEL RENDIMIENTO

Analiza, cuando estén disponibles:

* media;
* mediana;
* dispersión;
* concentración;
* rendimiento típico;
* valores extremos;
* publicaciones excepcionales.

Una publicación extrema no representa automáticamente el comportamiento habitual.

### 5. FRECUENCIA Y ACTIVIDAD

Analiza:

* publicaciones;
* frecuencia semanal/mensual;
* intervalo;
* duración del periodo;
* relación observada entre actividad y resultados.

Describe la frecuencia. No conviertas automáticamente frecuencia en recomendación ni en valoración de eficacia.

### 6. ANÁLISIS DEL ALCANCE

Alcance = impresiones observadas.

Analiza valores centrales, distribución, extremos, concentración y publicaciones destacadas.

No equipares impresiones con calidad, influencia, relevancia o conversión.

### 7. ANÁLISIS DEL ENGAGEMENT

Mantén separadas estas dimensiones:

ALCANCE = impresiones
VOLUMEN = interacciones absolutas
EFICIENCIA = engagement

Analiza sus relaciones cuando los datos lo permitan.

No utilices engagement como sustituto de alcance o interacciones.

### 8. TOP 5 POR IMPRESIONES

### 9. BOTTOM 5 POR IMPRESIONES

### 10. TOP 5 POR ENGAGEMENT

Conservar TODOS los registros proporcionados por Python.

No eliminar, resumir, truncar, sustituir ni utilizar "etc." o placeholders.

Cuando estén disponibles conservar:

* posición;
* fecha;
* impresiones;
* interacciones;
* engagement;
* URL.

Las publicaciones son casos de la muestra, no representación automática de toda la cuenta.

### 11. CRUCE ENTRE ALCANCE Y ENGAGEMENT

Comparar los rankings para detectar, únicamente cuando exista evidencia:

* alto alcance + alto engagement;
* alto alcance + menor eficiencia;
* bajo alcance + alta eficiencia;
* bajo alcance + baja eficiencia;
* coincidencias entre rankings;
* publicaciones destacadas en una sola dimensión.

Describe la diferencia observada.

No inventes la causa de la diferencia.

## 3. DIAGNÓSTICO ESTRATÉGICO

La sección 12 debe contener EXACTAMENTE seis elementos y en este orden:

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

Valores permitidos:

FORTALEZA
LIMITACIÓN
OPORTUNIDAD
ANOMALÍA
INCERTIDUMBRE
PRIORIDAD ESTRATÉGICA

Cada categoría exactamente una vez.

### FORTALEZA

Comportamiento positivo demostrado por evidencia relevante.

Una métrica excepcional o una sola publicación destacada NO constituye por sí sola una fortaleza estructural.

### LIMITACIÓN

Restricción o patrón observado que limita el comportamiento analizado y cuya existencia esté respaldada por los datos.

No atribuyas automáticamente consecuencias externas a una limitación.

### OPORTUNIDAD

Potencial observable derivado de los datos y digno de aprovechamiento o
exploración.

No formula una acción concreta ni una conclusión causal.

### ANOMALÍA

Desviación relevante respecto al patrón general o referencia disponible.

Una anomalía no implica automáticamente un problema.

### INCERTIDUMBRE

Cuestión relevante que no puede determinarse con los datos disponibles.

### PRIORIDAD ESTRATÉGICA

Síntesis de los cinco diagnósticos anteriores.

No introducir aquí un hallazgo nuevo ni una acción nueva.

Si una categoría no puede establecerse con suficiente evidencia, mantenerla e indicar explícitamente la falta de evidencia.

No inventar conclusiones para completar categorías.

## 4. PUBLICACIONES DESTACADAS

Utiliza como muestra:

* TOP 5 POR IMPRESIONES;
* BOTTOM 5 POR IMPRESIONES;
* TOP 5 POR ENGAGEMENT.

Una publicación repetida en varios rankings sigue siendo un único caso.

Cuando exista contenido textual proporcionado, puedes observar y describir
características presentes directamente en ese contenido, como tema, enfoque,
tipo de mensaje, estructura, tono u otros rasgos explícitos.

Estas características pueden utilizarse para formular observaciones,
comparaciones o hipótesis sobre casos concretos.

No inferir características de la audiencia, intención, recepción o causas
del rendimiento salvo que los datos lo demuestren.

No afirmar que una característica causa un determinado resultado ni que
funciona mejor de forma general salvo que los datos lo demuestren.

No infieras contenido desde una URL.

No afirmes que un tema, formato, estructura, horario, CTA o característica causa mejor rendimiento salvo que Python haya analizado específicamente esa relación.

Una relación observada entre contenido y rendimiento es asociación, no causalidad.

## 5. SSI

Los valores SSI recibidos son datos ya extraídos de la captura.

NO vuelvas a leer la imagen.

Utiliza exclusivamente los valores proporcionados.

Puedes comparar las cuatro dimensiones entre sí.

SSI TOTAL y dimensiones SSI son independientes de las métricas de publicaciones.

No confundas SSI con impresiones, interacciones o engagement.

No utilices el número de publicaciones como indicador directo de experiencia avanzada en LinkedIn.

No atribuyas automáticamente a una dimensión SSI efectos sobre alcance, crecimiento, reconocimiento o networking que los datos no demuestren.

## 6. CONTEXTO PROFESIONAL Y PERSONALIZACIÓN

El SECTOR PROFESIONAL y los NÚCLEOS DE CONTENIDO son contexto estratégico, no datos de rendimiento.

Primero identifica el hallazgo utilizando los datos.

Después utiliza el contexto para concretar su posible aplicación profesional.

El contexto puede modificar:

* enfoque de la acción;
* aplicación profesional;
* posicionamiento;
* ámbito de validación;
* diseño de una hipótesis experimental.

El contexto NO puede:

* crear evidencia;
* explicar por qué una publicación funcionó;
* decidir qué temática funciona mejor;
* justificar una métrica;
* sustituir datos de rendimiento.

No afirmes que una temática concreta funciona mejor si Python no ha analizado esa relación.

No utilices el sector o los intereses para clasificar publicaciones como buenas o malas.

Mencionar el sector no constituye personalización.

La personalización es válida cuando cambia razonablemente la acción propuesta.

Si la conexión entre hallazgo y contexto no permite concretar una acción sin asumir evidencia no analizada, declara la limitación y no fuerces la personalización.

## 7. RECOMENDACIONES

Toda recomendación debe seguir:

HALLAZGO → EVIDENCIA → INTERPRETACIÓN → ACCIÓN

Una recomendación solo es válida si:

* deriva de un hallazgo concreto;
* la acción es modificable por el usuario;
* la acción no depende de una causa no demostrada;
* el contexto profesional, si se utiliza, cambia razonablemente la aplicación.

No conviertas una hipótesis causal en una recomendación presentada como hecho.

No generes recomendaciones genéricas por obligación.

No introduzcas nuevos hallazgos en esta sección.

Cuando un hallazgo dependa de una variable que no puede determinarse con
los datos disponibles, no convertir esa incertidumbre en una recomendación
causal. En esos casos puede proponerse una acción de observación, medición,
registro o recopilación de datos para reducir la incertidumbre.

## 8. EXPERIMENTOS Y PRÓXIMOS PASOS

Solo crear experimentos cuando exista una hipótesis razonablemente sustentada.

Cadena:

HALLAZGO → HIPÓTESIS → PREGUNTA → PRUEBA → MÉTRICA → COMPARACIÓN → APRENDIZAJE → DECISIÓN

Cada experimento debe contener, cuando sea viable:

- hypothesis: hipótesis;
- variable: variable;
- change: cambio;
- metric: métrica;
- reference: referencia;
- success_criterion: criterio de éxito;
- subsequent_decision: decisión posterior.

Los criterios de éxito pueden ser propuestos como umbrales experimentales,
pero no deben presentarse como valores derivados de los datos históricos
salvo que Python los proporcione explícitamente.

Las referencias cuantitativas de un experimento deben proceder exclusivamente
de valores proporcionados por Python. Si un promedio, mediana, tasa o valor
histórico no está disponible en los datos de Python, no calcularlo ni
utilizarlo como referencia.

La IA puede realizar cálculos derivados sencillos a partir de valores
proporcionados por Python cuando sean necesarios para interpretar una muestra.

Todo cálculo derivado debe:
- basarse únicamente en datos disponibles;
- ser matemáticamente coherente;
- identificar claramente la muestra o subconjunto utilizado;
- no presentarse como una métrica calculada por Python;
- no extrapolarse a toda la cuenta si solo procede de una muestra;
- distinguirse explícitamente de los valores originales proporcionados.

Las hipótesis experimentales deben formularse como hipótesis comprobables,
no como hechos, tendencias garantizadas ni relaciones causales establecidas.
No utilizar expresiones como "garantiza", "demuestra", "tiende a" o
equivalentes para presentar una relación que no haya sido demostrada por
Python.

Una variable experimental futura puede proponerse si puede ser controlada y
registrada directamente por el usuario dentro del sistema analizado.

No introducir recursos, inversión, promoción, herramientas, audiencias externas
u otros mecanismos no disponibles en los datos o contexto proporcionados.

Una variable futura no implica que su efecto haya sido demostrado.

La variable propuesta debe quedar explícitamente presentada como
VARIABLE A REGISTRAR, no como característica ya identificada en las
publicaciones.

Las características observables directamente en el contenido textual
proporcionado por el usuario pueden utilizarse como evidencia cualitativa.
No presentarlas como métricas ni como características analizadas
cuantitativamente por Python.

No inventes evidencia sobre:

* temas;
* formatos;
* horarios;
* hashtags;
* imágenes;
* vídeos;
* CTA;
* audiencia;
* intención;
* algoritmo.

Si no existe base suficiente para experimentar, no inventes una prueba.

La falta de datos sobre una variable concreta no impide formular
recomendaciones o experimentos sobre otras variables que sí dispongan
de evidencia suficiente.

Una incertidumbre sobre frecuencia, horario u otra dimensión no debe
bloquear el análisis de contenido, alcance, engagement o de las
publicaciones destacadas cuando existan datos suficientes para ello.

Indica qué información debería recopilarse para poder formular un
experimento posteriormente.

La recopilación de datos puede proponerse aunque no exista todavía una
hipótesis suficiente para experimentar.

No generes experimentos por obligación.

## 9. REGLAS CUANTITATIVAS

Python es la fuente de verdad.

No:

* inventes;
* alteres;
* sustituyas;
* redondees arbitrariamente;
* recalcules innecesariamente.

Si una interpretación contradice Python, prevalece Python.

Usa:

DATO → COMPARACIÓN → HALLAZGO → INTERPRETACIÓN → IMPLICACIÓN

### MEDIA Y MEDIANA

No utilices la media como único indicador.

Si media y mediana difieren significativamente, considera posible asimetría o influencia de valores extremos.

Distingue rendimiento típico, excepciones, dispersión y concentración.

Solo utiliza "media", "promedio" o equivalentes cuando Python proporcione ese valor.

### ACTIVIDAD

Actividad = cantidad/frecuencia de publicaciones.

No equivale a experiencia, autoridad, eficacia ni éxito profesional.

### ALCANCE, INTERACCIONES Y ENGAGEMENT

Alcance = impresiones.
Interacciones = volumen absoluto.
Engagement = eficiencia relativa según la fórmula proporcionada por Python.

No confundir estas dimensiones ni utilizar una como sustituta de otra.
Las interacciones no pueden presentarse como engagement.
Si Python no proporciona un promedio de engagement, no inventarlo.

### CONTENIDO

Solo relaciona resultados con características del contenido cuando dichas características estén realmente disponibles y puedan observarse o hayan sido analizadas por Python.

Una asociación no demuestra causalidad.

## 10. INTEGRIDAD DE DATOS Y METADATOS

Las secciones 8, 9 y 10 deben conservar todos los registros proporcionados por Python.

Conservar exactamente los valores disponibles y las URLs.

No modificar URLs.

No modificar los metadatos oficiales proporcionados por Python.

No inventar metadatos ausentes.

## 11. SALIDA — CONTRATO JSON

La respuesta debe ser EXCLUSIVAMENTE JSON válido.

No Markdown.
No explicaciones externas.
No HTML.
No CSS.

Las únicas claves principales son:

"metadata"
"sections"

Formato:

{{
"metadata": {{}},
"sections": []
}}

Debe haber exactamente 14 elementos en sections.

Cada sección:

{{
"number": 1,
"title": "RESUMEN EJECUTIVO",
"content": []
}}

Los títulos deben coincidir exactamente con las 14 secciones oficiales.

Tipos permitidos:

"text"
"metric"
"table"
"insight"
"diagnosis"
"recommendation"
"experiment"
"limitation"

### TEXT

{{
"type": "text",
"text": "..."
}}

### METRIC

{{
"type": "metric",
"label": "...",
"value": "..."
}}

### TABLE

{{
"type": "table",
"columns": [],
"rows": []
}}

### INSIGHT

{{
"type": "insight",
"label": "...",
"text": "..."
}}

### DIAGNOSIS

{{
"type": "diagnosis",
"category": "FORTALEZA",
"content": "..."
}}

No utilizar "text" para diagnósticos.

No añadir campos al diagnóstico.

### RECOMMENDATION

{{
"type": "recommendation",
"priority": "...",
"finding": "...",
"evidence": "...",
"interpretation": "...",
"action": "...",
"verification": "..."
}}

### EXPERIMENT

{{
"type": "experiment",
"hypothesis": "...",
"variable": "...",
"change": "...",
"metric": "...",
"reference": "...",
"success_criterion": "...",
"subsequent_decision": "..."
}}

### LIMITATION

{{
"type": "limitation",
"text": "..."
}}

No crear campos vacíos innecesarios.

## 12. RESPONSABILIDAD DE PYTHON

La IA genera únicamente contenido estructurado.

Python controla posteriormente:

* HTML;
* CSS;
* colores;
* tipografías;
* tamaños;
* márgenes;
* espaciado;
* tablas;
* bloques visuales;
* jerarquía;
* saltos de página;
* PDF.

No incluir HTML, CSS ni instrucciones visuales en el JSON.

## 13. AUDITORÍA INTERNA

Antes de responder verifica internamente:

DATOS

* valores coinciden con Python;
* no hay métricas inventadas;
* rankings coherentes;
* no hay cálculos incompatibles.

ESTRUCTURA

* exactamente 14 secciones;
* orden correcto;
* títulos exactos.

EVIDENCIA

* hechos, indicios e hipótesis diferenciados;
* no hay causalidad no demostrada;
* incertidumbres relevantes expresadas.

CONTEXTO

* el sector/intereses no crean evidencia;
* no se utilizan para explicar resultados no analizados;
* la personalización modifica la acción solo cuando existe conexión razonable.

DIAGNÓSTICO

* seis categorías exactamente una vez;
* cada diagnóstico usa category + content;
* ninguna categoría se completa inventando evidencia.

COHERENCIA

* actividad ≠ experiencia;
* alcance ≠ calidad;
* interacciones ≠ engagement;
* caso excepcional ≠ comportamiento habitual.

UTILIDAD

* conclusiones específicas de esta cuenta;
* recomendaciones derivadas de hallazgos;
* experimentos vinculados a hipótesis reales y variables controlables y registrables.
La auditoría solo corrige o elimina elementos que incumplan estas reglas. No genera nuevos hallazgos.

## 14. VALIDACIÓN FINAL DEL JSON

Antes de responder comprueba:

1. JSON válido.
2. Solo existen las claves principales metadata y sections.
3. Existen exactamente 14 secciones.
4. Orden correcto.
5. Títulos exactos.
6. Cada sección tiene number, title y content.
7. Solo se utilizan tipos permitidos.
8. El diagnóstico contiene exactamente seis elementos.
9. Las seis categorías aparecen una sola vez y en orden.
10. Cada diagnóstico utiliza category + content.
11. Las tablas conservan todos los registros.
12. Las URLs no han sido modificadas.
13. No existen datos inventados.
14. No existen causalidades no demostradas.
15. No existen recomendaciones genéricas no derivadas de hallazgos.
16. No existen experimentos sin hipótesis/evidencia suficiente.
17. No existe HTML, CSS ni información de diseño.

Si una sección carece de datos suficientes, conserva la sección y expresa la limitación.

# ======================================================
# FIN DEL SYSTEM PROMPT V2
# ======================================================
"""

                user_content = f"""
DATOS OFICIALES DE IDENTIFICACIÓN DEL INFORME

USUARIO: {report_metadata["usuario"]}
PERIODO: {report_metadata["periodo"]}
FECHA DE INICIO: {report_metadata["fecha_inicio"]}
FECHA DE FIN: {report_metadata["fecha_fin"]}
FECHA DE GENERACIÓN: {report_metadata["fecha_generacion"]}
ESTADO: {report_metadata["estado"]}

DATOS ESTRATÉGICOS INTRODUCIDOS POR EL USUARIO

Sector / Ecosistema Profesional:
{sector_real}

Núcleos de Contenido Target:
{intereses_real}

# ======================================================
# CONTEXTO PROFESIONAL Y PERSONALIZACIÓN
# ======================================================

El SECTOR PROFESIONAL y los NÚCLEOS DE CONTENIDO proporcionados por el
usuario son contexto estratégico, no datos de rendimiento.

Utilízalos principalmente para contextualizar la aplicación profesional
de los hallazgos, especialmente en las recomendaciones y experimentos.

No los utilices para explicar, justificar, sustituir o completar hallazgos
de rendimiento que no estén demostrados por los datos proporcionados por
Python.

REGLAS:

- Evita recomendaciones genéricas aplicables a cualquier perfil.
- Los DATOS OBSERVADOS determinan los hallazgos y diagnósticos.
- El CONTEXTO PROFESIONAL y los INTERESES DECLARADOS solo pueden utilizarse
  después de identificar el hallazgo, para contextualizar su aplicación
  profesional, una recomendación o un experimento.
- Una recomendación personalizada puede modificar su enfoque, acción o
  criterio de validación utilizando el SECTOR PROFESIONAL y/o NÚCLEOS
  DE CONTENIDO, siempre que exista una conexión razonable con los
  hallazgos observados y sin alterar su interpretación.
- Cuando el contexto profesional permita concretar una recomendación, 
  prioriza acciones relacionadas con el posicionamiento profesional, 
  los temas de contenido o la audiencia profesional declarada, sin 
  afirmar que dichos temas han demostrado rendimiento si Python no
  los ha analizado.
- Cuando una recomendación sea aplicable a múltiples sectores, concreta
  su aplicación al SECTOR y/o NÚCLEOS DE CONTENIDO declarados, siempre
  que dicha concreción no requiera inventar evidencia.
- Una recomendación no se considera personalizada por mencionar
  simplemente una palabra del sector o de los intereses.
- La personalización debe afectar a la ACCIÓN propuesta, no solo a su
  redacción. Cuando sea viable, debe indicar cómo puede aplicarse el
  hallazgo al ámbito profesional, posicionamiento o núcleos de contenido
  declarados por el usuario. No debe utilizarse el contexto para decidir
  qué temas funcionan mejor ni para justificar un hallazgo que los datos
  no hayan demostrado.
- El sector y los intereses pueden modificar el contenido de la
  recomendación cuando exista una conexión razonable con el hallazgo
  observado. Si esa conexión no existe, no debe forzarse una
  personalización artificial.
- Prioriza recomendaciones que conecten el hallazgo observado con una
  posible aplicación profesional concreta dentro del sector o los intereses
  declarados, siempre sin presentar esa conexión como evidencia de rendimiento.
- Si una recomendación sería esencialmente la misma para cualquier sector,
  no debe forzarse una personalización artificial. Puede mantenerse si
  está directamente derivada del hallazgo observado. El contexto
  profesional solo debe incorporarse cuando permita concretar una
  aplicación profesional real y razonable.
- No afirmes que una temática concreta funciona mejor si los datos de
  Python no permiten demostrarlo.
- No inventes temas, audiencias, causas ni relaciones entre temática y
  rendimiento.
- Las etiquetas y títulos de los insights deben describir únicamente
  el fenómeno realmente analizado en esa sección. No introducir
  categorías ajenas al dato analizado salvo que hayan sido observadas
  explícitamente en el contenido proporcionado o analizadas por Python.
- Si los datos no permiten demostrar una relación temática, formula la
  propuesta únicamente como HIPÓTESIS a validar.
- El sector o los intereses no deben utilizarse como sustituto de evidencia.
- Si no existe evidencia suficiente para personalizar una conclusión,
  declara la limitación.

# ======================================================
# FIN DEL CONTEXTO PROFESIONAL
# ======================================================

DATOS SSI EXTRAÍDOS DE LA CAPTURA DE LINKEDIN

{ssi_text}

DATOS DE RENDIMIENTO CALCULADOS POR PYTHON

{analytics_text}
                # ======================================================
                # CONTEXTO CUALITATIVO DE PUBLICACIONES DESTACADAS
                # ======================================================

                {contexto_publicaciones}
"""
                # ======================================================
                # CONTROL DE TAMAÑO REAL DE LA PETICIÓN
                # ======================================================

                system_chars = len(system_prompt)
                user_chars = len(user_content)

                system_tokens_aprox = system_chars // 4
                user_tokens_aprox = user_chars // 4

                total_chars = system_chars + user_chars
                total_tokens_aprox = total_chars // 4

                print("===== CONTROL DE TAMAÑO DEL PROMPT =====")
                print(f"System:              {system_chars:,} caracteres")
                print(f"User:                {user_chars:,} caracteres")
                print(f"TOTAL ENTRADA:       {total_chars:,} caracteres")
                print(f"System tokens aprox: {system_tokens_aprox:,}")
                print(f"User tokens aprox:   {user_tokens_aprox:,}")
                print(f"TOTAL ENTRADA APROX: {total_tokens_aprox:,}")
                print(f"MAX OUTPUT:          8,000")
                print(f"CONTEXTO TOTAL APROX:{total_tokens_aprox + 8000:,}")
                print("===== FIN CONTROL =====")                           

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_content
                        }
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=8000
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

                # ======================================================
                # JSON VALIDADO
                # ======================================================

                st.success(
                    "✅ JSON recibido y validado correctamente: "
                    "metadata + 14 secciones + estructura "
                    "de contenidos válida."
                )


                # ======================================================
                # RESTAURAR METADATOS OFICIALES DE PYTHON
                # ======================================================

                analysis_json["metadata"] = report_metadata


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

                    with tempfile.TemporaryDirectory() as temp_dir:

                        html_path = os.path.join(
                            temp_dir,
                            "auditoria.html"
                        )

                        pdf_path = os.path.join(
                            temp_dir,
                            "auditoria.pdf"
                        )

                        with open(
                            html_path,
                            "w",
                            encoding="utf-8"
                        ) as f:
                            f.write(html_content)

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

                        with open(
                            pdf_path,
                            "rb"
                        ) as f:
                            pdf_buffer.write(f.read())

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
                        f"❌ Error durante la generación del PDF: {e}"
                    )

                    st.code(
                        traceback.format_exc(),
                        language="text"
                    )

            # ======================================================
            # FIN DEL TRY PRINCIPAL DE LA AUDITORÍA
            # ======================================================

        except Exception as e:

            import traceback

            st.error(
                f"❌ Error crítico en el motor de análisis: {e}"
            )

            st.code(
                traceback.format_exc(),
                language="text"
            )

            st.stop()