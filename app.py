from xhtml2pdf import pisa
import io
import streamlit as st
import pandas as pd
import openai
import base64
import requests
from pypdf import PdfReader
from datetime import date

# Configuración visual premium
st.set_page_config(page_title="Auditoría de Reputación LinkedIn AI", layout="centered", page_icon="🧲")

st.markdown("""
    <style>
    .report-title { font-size:28px !important; font-weight: bold; color: #1e3d59; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("🧲 LinkedIn Analytics Executive Auditor")
st.write("Transforma tus datos crudos en una auditoría de marca de alto impacto en PDF.")

# --- SECCIÓN DE GUÍA DE USO ---
with st.expander("📖 Manual de Operación y Transparencia de Costes", expanded=True):
    st.markdown("""
    ### 🛡️ Privacidad Absoluta y Costes de Operación
    Esta aplicación funciona bajo una arquitectura de código abierto. Tus datos se procesan en tiempo real en la memoria del servidor y se transmiten mediante cifrado SSL directo a la API de OpenAI. Nada se almacena en servidores externos. Cada auditoría consume unos **0,03€** del saldo de tu OpenAI API Key.
    
    ---
    
    ### 🚀 Requisitos para la ejecución:
    
    1. **🔑 OpenAI API Key**: Introduce tu clave `sk-...` en el menú lateral izquierdo. *(Requiere saldo mínimo cargado en OpenAI)*.
    2. **📊 Histórico de Contenido**: Sube el archivo **Excel (.xlsx)** o **PDF** de tus analíticas de creador de LinkedIn.
    3. **🎯 Captura de SSI (¡MUY IMPORTANTE!)**:
       - Haz clic en el botón de abajo o visita directamente: https://linkedin.com
       - Usa la herramienta de recortes (`Win + Shift + S`).
       - **⚠️ ATENCIÓN:** Al hacer la captura de pantalla, **recorta solo la zona de los gráficos y las puntuaciones numéricas. Deja fuera de la imagen tu foto de perfil (avatar)**. Esto evita que los sistemas de censura biométrica de OpenAI bloqueen el análisis por motivos de privacidad facial. Guárdala en tu ordenador como **PNG o JPG** y súbela al casillero inferior.
    4. **📅 Fecha de Alta**: Indica el día real en que activaste tu perfil para ajustar los promedios temporales con precisión.
    """)
    
    # Botón directo para el usuario
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
                    df = pd.read_excel(analytics_file)
                    analytics_text = df.to_string()

                base64_image = encode_image(ssi_image)
                client = openai.OpenAI(api_key=api_key)

                sector_real = sector if sector else "Ciberseguridad y Formación Profesional"
                intereses_real = intereses if intereses else "FP, Empleo, Redes, SMR, ASIR, DAM, DAW"

                # Forzamos a la IA a devolver exclusivamente código HTML estructurado y premium
                system_prompt = f"""
                Actúas como un Consultor Senior de Reputación Corporativa. Genera una auditoría ejecutiva profunda estructurada en código HTML limpio y elegante para ser impreso en formato A4 (dos páginas). Usa estilos CSS incrustados (<style>) con colores corporativos elegantes (azul oscuro #1e3d59, gris claro #f5f7fa, verde ejecutivo #17b978), márgenes limpios de 20px, fuentes sans-serif profesionales, tablas estructuradas para los datos y tarjetas visuales para los planes de acción.
                
                REGLA DE CONTEXTO TEMPORAL: El usuario activó su cuenta el {fecha_alta}. Hoy es {hoy}. Lleva {dias_activos} días activo ({meses_activos} meses). 
                Sus promedios mensuales deben calcularse dividiendo únicamente por estos {meses_activos} meses de vida real.
                
                Sector: {sector_real}. Intereses: {intereses_real}.
                
                El documento HTML debe contener estrictamente:
                - Un encabezado corporativo imponente titulado 'AUDITORÍA DE REPUTACIÓN CORPORATIVA DIGITAL'.
                - Sección 1: RESUMEN EJECUTIVO Y ANÁLISIS DE TRACCIÓN REAL (con datos formateados en cajas estéticas).
                - Sección 2: DESGLOSE CRÍTICO DE LOS 4 PILARES DEL SSI (representado en una tabla limpia con columnas de pilar, puntuación y diagnóstico).
                - Sección 3: AUDITORÍA DE CONTENIDOS Y ARQUITECTURA DEMOGRÁFICA: Identifica y extrae dinámicamente las principales empresas, cargos y sectores que aparecen en los datos demográficos aportados por el usuario. Cruza esta audiencia real con sus líneas de contenido actuales para determinar con precisión si está impactando en los tomadores de decisiones de su nicho o en perfiles junior, ofreciendo recomendaciones de reorientación.
                - Sección 4: PLAN ESTRATÉGICO DE ACELERACIÓN EN 3 FASES (Mes 1, Meses 2-3, Meses 4-12 presentados en tarjetas visuales de color de fondo diferenciado).
                
                ENTREGA EXCLUSIVAMENTE EL CÓDIGO HTML COMPLETO comenzando directamente con <html> y terminando con </html>. No incluyas introducciones ni bloques de código markdown como ```html.
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Datos de rendimiento del contenido:\n{analytics_text}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=3000
                )
                
                html_content = response.choices[0].message.content
                
                # Renderizado visual directo en la pantalla del usuario en formato web premium
                st.success("¡Auditoría corporativa ejecutada con éxito!")
                st.markdown("### Vista Previa del Informe Ejecutivo")
                st.components.v1.html(html_content, height=600, scroller=True)
                
                # --- CONVERSIÓN PDF ---
                pdf_buffer = io.BytesIO()

resultado = pisa.CreatePDF(
    src=html_content,
    dest=pdf_buffer
)

if resultado.err:
    st.error("No se ha podido generar el PDF.")
else:
    pdf_buffer.seek(0)

    st.download_button(
        label="📥 Descargar Auditoría Estratégica en PDF Profesional",
        data=pdf_buffer,
        file_name="Auditoria_LinkedIn_Premium.pdf",
        mime="application/pdf"
    )
            except Exception as e: 
                st.error(f"Error crítico en el motor de análisis: {e}")
