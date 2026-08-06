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

# --- SECCIÓN DE GUÍA DE USO ACTUALIZADA ---
with st.expander("📖 Manual de Operación y Transparencia de Costes", expanded=True):
    st.markdown("""
    ### 🛡️ Privacidad Absoluta y Costes de Operación
    Esta aplicación funciona bajo una arquitectura de código abierto. Tus datos se procesan en tiempo real en la memoria del servidor y se transmiten mediante cifrado SSL directo a la API de OpenAI. Nada se almacena en servidores externos. Cada auditoría consume unos **0,03€** del saldo de tu OpenAI API Key.
    
    ---
    
    ### 🚀 Requisitos para la ejecución:
    
    1. **🔑 OpenAI API Key**: Introduce tu clave `sk-...` en el menú lateral izquierdo. *(Require saldo): puedes obtenerlo de [://platform.openai.com](https://platform.openai.com/).*.
    2. **📊 Histórico de Contenido**: Sube el archivo **Excel (.xlsx)** o **PDF** de tus analíticas de creador de LinkedIn.
    3. **🎯 Captura de SSI (¡MUY IMPORTANTE!)**:
       - Visita [://linkedin.com](https://www.linkedin.com/sales/ssi/).
       - Usa la herramienta de recortes (`Win + Shift + S`).
       - **⚠️ ATENCIÓN:** Al hacer la captura de pantalla, **recorta solo la zona de los gráficos y las puntuaciones numéricas. Deja fuera de la imagen tu foto de perfil (avatar)**. Esto evita que los sistemas de censura biométrica de OpenAI bloqueen el análisis por motivos de privacidad facial. Guárdala como **PNG o JPG**.
    4. **📅 Fecha de Alta**: Indica el día real en que activaste tu perfil para ajustar los promedios temporales con precisión.
    """)

# 1. Credenciales de Seguridad (Cambiado a texto normal para burlar el gestor de contraseñas de Windows)
with st.sidebar:
    st.header("⚙️ Seguridad de la API")
    api_key = st.text_input("OpenAI API Key", type="default", placeholder="Pega tu clave sk-...")
    st.info("🔓 Tus credenciales no se almacenan en ningún sitio. Al usar el modo texto, Windows no te molestará sugiriendo contraseñas seguras.")

# 2. Captura de Variables (Implementación de marcadores en gris 'placeholder')
st.subheader("1. Parámetros Estratégicos")
col1, col2 = st.columns(2)
with col1:
    sector = st.text_input("Ecosistema / Sector Profesional", placeholder="Ej: Ciberseguridad y Formación Profesional Informática")
with col2:
    intereses = st.text_input("Núcleos de Contenido Target", placeholder="Ej: FP, Empleo, Redes, SMR, ASIR, DAM, DAW")

fecha_alta = st.date_input("Fecha de Activación Real del Perfil", date(2026, 3, 1))

st.subheader("2. Input de Datos (LinkedIn Nativos)")
ssi_image = st.file_uploader("Captura del Social Selling Index (Imagen PNG/JPG sin foto de perfil)", type=["png", "jpg", "jpeg"])
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
        with st.spinner("Ejecutando algoritmos de visión y análisis demográfico... Por favor, espera."):
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

                # Si el usuario no escribe nada en los inputs, asignamos los tuyos por defecto para la IA
                sector_real = sector if sector else "Ciberseguridad y Formación Profesional"
                intereses_real = intereses if intereses else "FP, Empleo, Redes, SMR, ASIR, DAM, DAW"

                system_prompt = f"""
                Actúas como un Consultor Senior de Reputación Corporativa y Estratega de Marca Personal en LinkedIn.
                Vas a generar una auditoría ejecutiva profunda de dos páginas A4 virtuales. El tono debe ser directo, ejecutivo, analítico, crítico pero constructivo.
                Concéntrate exclusivamente en los datos numéricos, textos corporativos y barras estadísticas de los gráficos de la imagen del SSI.
                
                REGLA DE CONTEXTO TEMPORAL: El usuario activó su cuenta el {fecha_alta}. Hoy es {hoy}. Lleva {dias_activos} días activo ({meses_activos} meses). 
                Ignora los ceros de los meses previos a su registro en los cálculos. Sus promedios mensuales deben calcularse dividiendo únicamente por estos {meses_activos} meses de vida real.
                
                Sector de posicionamiento: {sector_real}.
                Temas clave de interés: {intereses_real}.
                
                Estructura el informe estrictamente en las siguientes 4 secciones de alta densidad informativa, utilizando un diseño visual ordenado con títulos claros:

                PÁGINA 1: DIAGNÓSTICO ESTRUCTURAL Y AUDIENCIA DE ALTO VALOR
                1. RESUMEN EJECUTIVO Y ANÁLISIS DE TRACCIÓN REAL: Entrega un análisis de rendimiento real profundo (Impresiones totales, miembros únicos alcanzados y tasa de crecimiento calculada según sus {meses_activos} meses de vida). Contrasta la velocidad de despegue de la cuenta.
                2. DESGLOSE CRÍTICO DE LOS 4 PILARES DEL SSI: Analiza la imagen del SSI. Detalla la puntuación de cada pilar (Marca, Personas correctas, Información, Relaciones). Explica el desequilibrio técnico entre su capacidad de atracción y su pilar de interacción ofreciendo información. Compáralo con el índice medio de su sector e industria.

                PÁGINA 2: INGENIERÍA DE CONTENIDOS Y HOJA DE RUTA TRIPLE
                3. AUDITORÍA DE CONTENIDOS Y ARQUITECTURA DEMOGRÁFICA: Evalúa las temáticas más exitosas según los datos (como Formación Profesional, Ciberseguridad y empleo). Cruza estos datos con la demografía corporativa de su audiencia (Junta de Andalucía, Agencia Digital de Andalucía, perfiles técnicos en Sevilla/Málaga). Determina si el contenido está atrayendo a tomadores de decisiones o perfiles junior.
                4. PLAN ESTRATÉGICO DE ACELERACIÓN EN 3 FASES:
                   - Fase 1 (Mes 1 - Optimización del Algoritmo): Acciones diarias y semanales de micro-interacción para subir el SSI.
                   - Fase 2 (Meses 2-3 - Autoridad de Nicho): Formatos específicos de alto rendimiento (ej. Carruseles PDF, artículos técnicos).
                   - Fase 3 (Meses 4-12 - Consolidación institucional): Estrategia de networking relacional con directivos del sector público y tecnológico andaluz.
                
                RESTRICCIÓN DE SALIDA: Entrega el reporte directamente usando un formato limpio y elegante. Evita introducciones genéricas. No uses asteriscos redundantes. Ofrece un desarrollo muy extenso, detallado y rico en texto estratégico (mínimo 1000 palabras) para asegurar que el contenido cubra las dos páginas completas con un valor de consultoría premium.
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
                
                st.markdown("---")
                st.markdown(f"<div class='report-title'>INFORME DE AUDITORÍA ESTRATÉGICA</div>", unsafe_allow_html=True)
                st.markdown(reporte)
                st.markdown("---")
                
                st.download_button(
                    label="📥 Exportar Informe Estratégico (.txt)",
                    data=reporte,
                    file_name="Auditoria_Reputacion_LinkedIn.txt",
                    mime="text/plain"
                )
                
            except Exception as e:

