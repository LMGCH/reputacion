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

st.title("🧭 LinkedIn Analytical Audit")
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
                client = openai.OpenAI(api_key=api_key)

                sector_real = sector if sector else "Ciberseguridad y Formación Profesional"
                intereses_real = intereses if intereses else "FP, Empleo, Redes, SMR, ASIR, DAM, DAW"

                # Forzamos a la IA a devolver exclusivamente código HTML estructurado y premium
                system_prompt = f"""
                Eres un consultor senior de LinkedIn.

                Recibirás:
                - Un resumen estadístico de una cuenta de LinkedIn.
                - Una captura del SSI.
                - Una clasificación de madurez del perfil calculada previamente mediante Python.

                NIVEL DE MADUREZ CALCULADO:
                - Actividad: {madurez.get("actividad", "N/D")}
                - Tracción: {madurez.get("traccion", "N/D")}
                - Madurez estratégica: {madurez.get("madurez_estrategica", "N/D")}

                ADAPTACIÓN DEL ANÁLISIS:

                Si la madurez estratégica es "Inicial":
                - Prioriza educación y recomendaciones prácticas.
                - Explica brevemente qué significan las métricas relevantes.
                - Identifica oportunidades sencillas para aumentar visibilidad.
                - Propón acciones concretas y fáciles de aplicar.
                - No penalices al usuario por desconocer estrategias avanzadas.

                Si la madurez estratégica es "En desarrollo":
                - Reduce las explicaciones básicas.
                - Analiza patrones de contenido.
                - Compara alcance y engagement.
                - Identifica qué temas y publicaciones funcionan mejor.
                - Propón experimentos estratégicos concretos.

                Si la madurez estratégica es "Avanzada":
                - Prioriza análisis fino y estratégico.
                - Busca patrones y anomalías.
                - Analiza eficiencia del engagement.
                - Identifica oportunidades de segmentación.
                - Propón optimización y experimentación avanzada.

                IMPORTANTE:
                La cantidad de publicaciones NO determina por sí sola la madurez estratégica.
                Actividad, tracción y experiencia estratégica son dimensiones diferentes.
                
                ======================================================
                RECOMENDACIONES ESTRATÉGICAS
                ======================================================

                Antes de redactar recomendaciones, debes realizar internamente
                un diagnóstico del perfil utilizando exclusivamente los datos
                proporcionados por Python.

                NO muestres el proceso interno de razonamiento.

                Sin embargo, cada recomendación final DEBE poder relacionarse
                directamente con uno o varios datos concretos del análisis.

                Para cada recomendación determina:

                - PROBLEMA U OPORTUNIDAD detectada.
                - EVIDENCIA disponible en los datos.
                - ACCIÓN concreta que debería realizar el usuario.
                - PRIORIDAD de la acción.

                Las recomendaciones deben responder a la situación particular
                de ESTE perfil y no a un usuario genérico de LinkedIn.

                IMPORTANTE:

                Una recomendación NO es válida si podría aparecer exactamente
                igual en un informe de otro usuario con métricas diferentes.

                Evita frases genéricas como:

                - "Publica contenido de calidad."
                - "Sé constante."
                - "Haz networking."
                - "Mejora tu marca personal."
                - "Interactúa más."
                - "Optimiza tu perfil."

                Estas ideas solo pueden aparecer si se concretan utilizando
                los datos del usuario y explicando qué debe hacer exactamente.

                Ejemplo de nivel de concreción esperado:

                INCORRECTO:
                "Debes mejorar tu estrategia de contenidos."

                CORRECTO:
                "Tu frecuencia de publicación ya es elevada (3,78 publicaciones
                por semana), pero solo 8 de 49 publicaciones superan tu media
                de impresiones. Por tanto, aumentar la frecuencia no debería
                ser ahora tu prioridad. Conviene analizar qué características
                comparten las publicaciones que han generado tus mayores picos
                de alcance y experimentar con esos patrones."

                No copies este ejemplo ni sus conclusiones automáticamente.
                Debes calcular y utilizar los datos reales del usuario.

                GENERA ENTRE 3 Y 5 RECOMENDACIONES.

                Ordénalas por prioridad.

                Cada recomendación debe incluir:

                1. Título breve.
                2. Evidencia.
                3. Interpretación.
                4. Acción concreta.

                Si los datos no permiten justificar una recomendación,
                NO la hagas.

                Distingue obligatoriamente entre:

                - HECHO: conclusión directamente demostrada por los datos.
                - INDICIO: patrón sugerido por los datos pero que no puede considerarse demostrado.
                - HIPÓTESIS: posible explicación que debería comprobarse mediante futuras publicaciones.

                Nunca presentes un indicio o una hipótesis como un hecho.

                No generalices a partir de una única publicación.
                Para afirmar que existe un patrón temático, de formato o comportamiento,
                debes disponer de suficientes observaciones comparables.

                Si solo existe una publicación que cumple una característica,
                preséntala como caso individual, no como tendencia.

                Cuando propongas una acción cuyo efecto no pueda demostrarse con los
                datos actuales, preséntala como experimento o prueba, no como una
                conclusión causal.

                MARCO METODOLÓGICO PARA EL ANÁLISIS DE LINKEDIN:
                Utiliza como referencia metodológica las buenas prácticas y criterios
                publicados por Metricool sobre LinkedIn y su estudio de LinkedIn 2026.

                Para LinkedIn, cuando se calcule el engagement de una publicación,
                utiliza:

                Engagement (%) = (Interacciones / Impresiones) × 100

                Las impresiones deben utilizarse como denominador para LinkedIn,
                no el alcance.

                IMPORTANTE:
                - Python proporciona los datos numéricos reales.
                - Utiliza únicamente las métricas disponibles.
                - No inventes clics, comentarios, compartidos, visualizaciones,
                tiempo de reproducción, alcance único u otras métricas que no
                estén presentes en los datos.
                - Si una métrica necesaria no está disponible, indícalo claramente.
                - No atribuyas causalidad al algoritmo de LinkedIn cuando los datos
                disponibles solo permitan establecer una correlación u observación.

                Al interpretar el rendimiento considera, cuando existan datos suficientes:
                - impresiones,
                - engagement,
                - interacciones,
                - comentarios,
                - compartidos,
                - clics,
                - formato,
                - frecuencia de publicación,
                - evolución temporal,
                - y cualquier otra métrica disponible.

                No reduzcas el análisis a "publicar más".
                Analiza primero la relación entre frecuencia, alcance, interacción
                y calidad del contenido.


                NO INVENTES ARCHIVOS NI RECURSOS EXTERNOS.

                La captura del SSI solo debe mostrarse mediante una imagen si la aplicación
                proporciona realmente dicha imagen al HTML.

                Si la imagen del SSI no está disponible como archivo o recurso válido,
                muestra los datos del SSI mediante texto, métricas o elementos HTML,
                pero NO inventes una ruta de imagen.

                No inventes nombres de archivos de imagen como .jpg, .jpeg, .png, .gif,
                .webp ni ninguna otra imagen que no haya sido proporcionada explícitamente.

                No incluyas etiquetas <img> apuntando a archivos inexistentes.

                No supongas que existen archivos como:
                - chart.jpg
                - grafico.jpg
                - analysis.jpg
                - engagement.jpg
                - profile.jpg
                - ssi.jpg

                Solo puedes utilizar imágenes si el programa las proporciona explícitamente
                o si existe una ruta/archivo real disponible.

                Si no existe una imagen disponible, no generes una referencia a ella.

                El HTML debe ser completamente funcional con los recursos realmente
                disponibles en la aplicación.

                NO UTILICES BLOQUES DE CÓDIGO MARKDOWN.

                La respuesta NO debe comenzar con ```html,
                NO debe terminar con ```,
                y NO debe contener delimitadores ``` en ningún punto.

                La primera línea de la respuesta debe ser directamente:
                <html>

                La última línea debe ser directamente:
                </html>

                Devuelve exclusivamente un documento HTML válido que comience por <html> y termine por </html>.
                # system_prompt = f"""

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
                    max_tokens=6000
                )
                
                html_content = response.choices[0].message.content

                st.write("Respuesta de OpenAI:")
                st.code(html_content)

                # --------------------------------------------------
                # VISTA PREVIA DEL INFORME
                # --------------------------------------------------

                st.success("¡Auditoría corporativa ejecutada con éxito!")

                st.markdown("### Vista Previa del Informe Ejecutivo")

                st.components.v1.html(
                    html_content,
                    height=600,
                    scrolling=True
                )

                # --------------------------------------------------
                # CONVERSIÓN PDF
                # --------------------------------------------------

                pdf_buffer = io.BytesIO()

                resultado = pisa.CreatePDF(
                    src=html_content,
                    dest=pdf_buffer
                )

                if resultado.err:

                    st.error(
                        "No se ha podido generar el PDF."
                    )

                else:

                    pdf_buffer.seek(0)

                    st.download_button(
                        label="📥 Descargar Auditoría Estratégica en PDF Profesional",
                        data=pdf_buffer,
                        file_name="Auditoria_LinkedIn_Premium.pdf",
                        mime="application/pdf",
                        key="descargar_auditoria_pdf"
                    )
            except Exception as e:

                st.error(
                    f"Error crítico en el motor de análisis: {e}"
                )