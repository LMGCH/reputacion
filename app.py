import streamlit as st
import pandas as pd
import openai
import base64
from pypdf import PdfReader
from datetime import date
from fpdf import FPDF

# Configuración visual de la página web
st.set_page_config(page_title="LinkedIn Micro-Analytics AI", layout="centered", page_icon="🧲")
st.title("🧲 LinkedIn Creator & SSI Report Generator")
st.write("Genera tu informe estratégico A4 de 2 páginas adaptado a tu antigüedad real en la plataforma.")

# --- SECCIÓN DE GUÍA DE USO PARA EL USUARIO EXTERNO ---
with st.expander("📖 ¿Cómo usar esta aplicación? (Manual paso a paso)", expanded=True):
    st.markdown("""
    ### 🚀 Instrucciones para generar tu informe con éxito:
    
    1. **🔑 Consigue tu OpenAI API Key**: Regístrate en [://openai.com](https://://openai.com/), ve a la sección *API Keys*, crea una nueva llave y pégala en la barra lateral izquierda de esta app. Necesitarás tener un saldo mínimo de $5 de crédito cargado en OpenAI.
    2. **📊 Descarga tus Analíticas de LinkedIn**: 
       - Entra en tu panel de LinkedIn.
       - Accede a la sección de *Analíticas de Creador* (Análisis de contenido).
       - Haz clic en el botón **Exportar** arriba a la derecha y descarga el archivo en formato **Excel (.xlsx)** o **PDF**.
    3. **🎯 Captura tu Social Selling Index (SSI)**:
       - Visita el enlace oficial: [://linkedin.com](https://www.://linkedin.com/).
       - Usa la herramienta de recortes de tu ordenador (`Win + Shift + S` en Windows) y haz una captura de pantalla donde se vean tus gráficas y puntuación. **Guárdala como imagen (PNG o JPG)**. No la imprimas en PDF, arrastra la imagen directa para que la IA la analice visualmente.
    4. **📅 Introduce tu Fecha de Alta**: Indica el día exacto en el que te registraste en LinkedIn para que la IA calcule tus promedios reales y no penalice tu puntuación con los meses de inactividad previos.
    """)

# 1. Configuración de Credenciales en la Barra Lateral
with st.sidebar:
    st.header("⚙️ Configuración de Seguridad")
    api_key = st.text_input("Introduce tu OpenAI API Key", type="password")
    st.info("🔓 Tus credenciales viajan de forma segura y directa a OpenAI sin guardarse en bases de datos.")

# 2. Entradas de datos del Usuario
st.subheader("1. Información de Contexto")
col1, col2 = st.columns(2)
with col1:
    sector = st.text_input("Tu Sector / Especialidad", "Ciberseguridad y FP Informática")
with col2:
    intereses = st.text_input("Tus Intereses de Contenido", "Formación Profesional, Redes, Empleo, SMR, ASIR, DAM, DAW")

# Campo obligatorio para evitar el problema de los meses en cero previos a tu registro
fecha_alta = st.date_input("¿Qué día te diste de alta en LinkedIn?", date(2026, 3, 1))

st.subheader("2. Archivos Exportados de LinkedIn")
ssi_image = st.file_uploader("Sube la captura de tu SSI (Debe ser IMAGEN: PNG, JPG)", type=["png", "jpg", "jpeg"])
analytics_file = st.file_uploader("Sube tus Analíticas de Creador (Excel .xlsx o PDF)", type=["xlsx", "pdf"])

# Función interna para convertir la imagen a un formato que entienda la IA
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# Clase interna para maquetar el PDF de forma limpia
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'INFORME DE RENDIMIENTO ESTRATÉGICO - REPUTACIÓN DIGITAL', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# 3. Procesamiento y ejecución al pulsar el botón
if st.button("🚀 Generar Informe Estratégico de 2 Páginas"):
    if not api_key:
        st.error("Por favor, introduce tu OpenAI API Key en la barra lateral izquierda.")
    elif not ssi_image or not analytics_file:
        st.error("Es obligatorio subir tanto la captura del SSI como el archivo de analíticas.")
    else:
        with st.spinner("Calculando métricas según tu antigüedad real... Por favor, espera."):
            try:
                # Calcular tiempo real en la plataforma
                hoy = date.today()
                dias_activos = (hoy - fecha_alta).days
                meses_activos = max(1, round(dias_activos / 30.4))
                
                # Leer el archivo de analíticas dependiendo de si es PDF o Excel
                analytics_text = ""
                if analytics_file.name.endswith('.pdf'):
                    reader = PdfReader(analytics_file)
                    for page in reader.pages:
                        analytics_text += page.extract_text() + "\n"
                else:
                    df = pd.read_excel(analytics_file)
                    analytics_text = df.to_string()

                # Codificar la imagen del SSI
                base64_image = encode_image(ssi_image)
                
                # Inicializar el cliente de OpenAI
                client = openai.OpenAI(api_key=api_key)

                # Definir las instrucciones exactas del sistema
                system_prompt = f"""
                Actúas como un Consultor de Marca Personal de Élite en LinkedIn.
                
                REGLA DE TIEMPO CRÍTICA: El usuario se incorporó a la plataforma el {fecha_alta}.
                A fecha de hoy ({hoy}), lleva exactamente {dias_activos} días activo (unos {meses_activos} meses).
                Ignora por completo todos los ceros previos en los históricos analíticos. Evalúa su crecimiento, 
                volumen de impresiones e interacciones dividiendo los totales ÚNICAMENTE por estos {meses_activos} meses.
                
                El sector del usuario es: {sector}. Sus intereses principales son: {intereses}.
                
                Analiza la imagen del SSI adjunta y los datos textuales del rendimiento de contenido.
                Genera un informe estratégico estructurado en exactamente DOS páginas A4 virtuales usando texto plano limpio (sin símbolos extraños de Markdown como asteriscos excesivos).
                El informe debe contener obligatoriamente: 
                1. Un resumen con datos clave ajustados a su tiempo real de vida en la red.
                2. Diagnóstico del SSI con perspectiva de cuenta nueva.
                3. Análisis de las temáticas y publicaciones con más éxito.
                4. Un plan de acción detallado en 3 fases (1 mes, 3 meses, 1 año) con tareas prácticas diarias.
                
                Sé directo, profesional y utiliza viñetas estándar (-). Evita introducciones corporativas irrelevantes.
                """

                # Enviar la solicitud a la API de OpenAI
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Aquí tienes los datos extraídos de las analíticas:\n{analytics_text}"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=2500
                )
                
                reporte = response.choices.message.content
                st.success("¡Informe adaptado y generado con éxito!")
                st.text(reporte)
                
                # Generación del archivo PDF real en caliente
                pdf = PDFReport()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                
                # Limpiar texto para evitar fallos de codificación en PDF estándar
                lineas = reporte.split('\n')
                for linea in lineas:
                    cleaned_line = linea.encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(0, 6, cleaned_line, 0, 1)
                
                pdf_output = pdf.output(dest='S')
                
                # Ofrecer la opción de descargar el resultado final en PDF
                st.download_button(
                    label="📥 Descargar Reporte en PDF Profesional",
                    data=bytes(pdf_output),
                    file_name="Informe_Estrategico_LinkedIn.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Ha ocurrido un error durante el procesamiento: {e}")
