import streamlit as st
import pandas as pd
import openai
import base64
from pypdf import PdfReader
from datetime import date

# Configuración visual premium de la aplicación web
st.set_page_config(page_title="Auditoría de Reputación LinkedIn AI", layout="centered", page_icon="🧲")

st.markdown("""
    <style>
    .report-title { font-size:28px !important; font-weight: bold; color: #1e3d59; text-align: center; margin-bottom: 20px; }
    .executive-card { background-color: #f5f7fa; border-left: 5px solid #17b978; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    .metric-box { background-color: #ffffff; border: 1px solid #e1e8ed; padding: 10px; border-radius: 6px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

st.title("🧲 LinkedIn Analytics Executive Auditor")
st.write("Transforma tus datos crudos en una auditoría de marca personal de alto impacto y dos páginas.")

# --- SECCIÓN DE GUÍA DE USO ---
with st.expander("📖 Manual de Operación y Transparencia de Costes", expanded=False):
    st.markdown("""
    ### 🛡️ Privacidad Absoluta y Costes de Operación
    Esta aplicación funciona bajo una arquitectura descentralizada de código abierto. Tus datos, capturas y métricas se procesan en tiempo real en la memoria del servidor y se transmiten mediante cifrado SSL directo a la API de OpenAI. Nada se almacena en servidores externos.
    
    Cada auditoría consume un coste aproximado de **0,03€** del saldo de tu OpenAI API Key.
    
    ### 🚀 Requisitos para la ejecución:
    1. **🔑 OpenAI API Key**: Introduce tu clave `sk-...` en el menú lateral izquierdo, obtenla de [://platform.openai.com](https://platform.openai.com/).
    2. **📊 Histórico de Contenido**: Sube el archivo **Excel (.xlsx)** o **PDF** de tus analíticas de creador de LinkedIn.
    3. **🎯 Captura de SSI**: Sube una captura en formato **imagen (PNG/JPG)** de tus gráficas de Social Selling Index desde [://linkedin.com](https://www.linkedin.com/sales/ssi/).
    """)

# 1. Credenciales de Seguridad
with st.sidebar:
    st.header("⚙️ Seguridad de la API")
    api_key = st.text_input("OpenAI API Key", type="password")
    st.info("🔓 Tus credenciales no se almacenan y viajan encriptadas hacia los servidores oficiales de OpenAI.")

# 2. Captura de Variables
st.subheader("1. Parámetros Estratégicos")
col1, col2 = st.columns(2)
with col1:
    sector = st.text_input("Ecosistema / Sector Profesional", "Ej. Ciberseguridad y Formación Profesional Informática")
with col2:
    intereses = st.text_input("Núcleos de Contenido Target", "Ej. FP, Empleo, Redes, SMR, ASIR, DAM, DAW")

fecha_alta = st.date_input("Fecha de Activación Real del Perfil", date(2026, 3, 1))

st.subheader("2. Input de Datos (LinkedIn Nativos)")
ssi_image = st.file_uploader("Captura del Social Selling Index (Imagen PNG/JPG obligatoria)", type=["png", "jpg", "jpeg"])
analytics_file = st.file_uploader("Histórico Analítico de Creador (Excel .xlsx o PDF)", type=["xlsx", "pdf"])

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# 3. Procesamiento y Renderizado del Informe Ejecutivo
if st.button("🚀 Ejecutar Auditoría Estratégica Completa"):
    if not api_key:
        st.error("Error de autenticación: Introduce tu OpenAI API Key en la barra lateral.")
    elif not ssi_image or not analytics_file:
        st.error("Error de datos: Es obligatorio adjuntar tanto la captura visual del SSI como el registro analítico.")
    else:
        with st.spinner("Ejecutando algoritmos de visión y análisis demográfico..."):
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

                # Prompt Ultra-Cuidadoso e Industrial para forzar el formato de Élite
                system_prompt = f"""
                Actúas como un Consultor Senior de Reputación Corporativa y Estratega de Marca Personal en LinkedIn.
                Vas a generar una auditoría ejecutiva de exactamente DOS páginas A4 virtuales. El tono debe ser directo, de alta dirección, crítico pero constructivo.
                
                REGLA DE CONTEXTO TEMPORAL: El usuario activó su cuenta el {fecha_alta}. Hoy es {hoy}. Lleva {dias_activos} días activo ({meses_activos} meses). 
                Ignora los ceros de los meses previos a su registro en los cálculos. Sus promedios mensuales deben calcularse dividiendo únicamente por estos {meses_activos} meses de vida real.
                
                Sector de posicionamiento: {sector}.
                Temas clave de interés: {intereses}.
                
                Estructura el informe estrictamente en las siguientes 4 secciones de alta densidad informativa, utilizando un diseño visual ordenado con títulos claros:

                PÁGINA 1: DIAGNÓSTICO ESTRUCTURAL Y AUDIENCIA DE ALTO VALOR
                1. RESUMEN EJECUTIVO Y ANÁLISIS DE TRACCIÓN REAL: Entrega un análisis de rendimiento real (Impresiones totales, miembros únicos alcanzados y tasa de crecimiento calculada según sus {meses_activos} meses de vida). Contrasta la velocidad de despegue de la cuenta.
                2. DESGLOSE CRÍTICO DE LOS 4 PILARES DEL SSI: Analiza la imagen del SSI. Detalla la puntuación de cada pilar (Marca, Personas correctas, Información, Relaciones). Explica el desequilibrio técnico entre su capacidad de atracción y su pilar de interacción ofreciendo información. Compáralo con el índice medio de su sector e industria.

                PÁGINA 2: INGENIERÍA DE CONTENIDOS Y HOJA DE RUTA TRIPLE
                3. AUDITORÍA DE CONTENIDOS Y ARQUITECTURA DEMOGRÁFICA: Evalúa las temáticas más exitosas según los datos (como Formación Profesional, Ciberseguridad y empleo). Cruza estos datos con la demografía corporativa de su audiencia (Junta de Andalucía, Agencia Digital de Andalucía, perfiles técnicos en Sevilla/Málaga). Determina si el contenido está atrayendo a tomadores de decisiones o perfiles junior.
                4. PLAN ESTRATÉGICO DE ACELERACIÓN EN 3 FASES:
                   - Fase 1 (Mes 1 - Optimización del Algoritmo): Acciones diarias y semanales de micro-interacción para subir el SSI.
                   - Fase 2 (Meses 2-3 - Autoridad de Nicho): Formatos específicos de alto rendimiento (ej. Carruseles PDF, artículos técnicos).
                   - Fase 3 (Meses 4-12 - Consolidación institucional): Estrategia de networking relacional con directivos del sector público y tecnológico andaluz.
                
                RESTRICCIÓN DE SALIDA: Entrega el reporte directamente usando un formato limpio y elegante. Evita introducciones genéricas. No uses asteriscos redundantes.
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Datos de rendimiento del contenido:\n{analytics_text}"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=3000
                )
                
                reporte = response.choices[0].message.content
                st.success("Auditoría corporativa ejecutada con éxito.")
                
                # Renderizado visual premium en la propia interfaz web
                st.markdown("---")
                st.markdown(f"<div class='report-title'>INFORME DE AUDITORÍA ESTRATÉGICA</div>", unsafe_allow_html=True)
                st.markdown(reporte)
                st.markdown("---")
                
                # Permitir la descarga directa del texto estratégico estructurado
                st.download_button(
                    label="📥 Exportar Informe Estratégico (.txt)",
                    data=reporte,
                    file_name="Auditoria_Reputacion_LinkedIn.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error crítico en el motor de análisis: {e}")
