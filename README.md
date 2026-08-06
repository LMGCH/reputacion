\# 🧲 LinkedIn Creator \& SSI Report Generator



Esta es una microaplicación inteligente desarrollada en Python y Streamlit diseñada para generar un \*\*informe estratégico ejecutivo de 2 páginas en formato PDF\*\* analizando el perfil de LinkedIn del usuario. 



El sistema utiliza el motor de Inteligencia Artificial de OpenAI (`GPT-4o`) combinado con capacidades de visión para procesar datos reales y gráficos sin necesidad de conectar con la restrictiva API oficial de LinkedIn.



\## 🛠️ Características Principales

\- \*\*Análisis de Visión Integrado\*\*: El usuario solo necesita subir una captura de pantalla de su Social Selling Index (SSI) y la IA la interpretará de forma visual.

\- \*\*Procesamiento de Datos Estructurados\*\*: Permite la carga directa del reporte Excel (`.xlsx`) o PDF exportado nativamente de las analíticas de creador de LinkedIn.

\- \*\*Filtro de Antigüedad Quirúrgico\*\*: Evita falsos diagnósticos al permitir introducir la fecha exacta de alta en la plataforma, calculando los promedios de rendimiento basándose únicamente en los meses de actividad real.

\- \*\*Exportación Limpia\*\*: Genera un archivo PDF maquetado y listo para imprimir en formato A4.



\## 🚀 Cómo ponerlo en marcha en local



1\. \*\*Clona o descarga este repositorio\*\* en tu ordenador.

2\. Abre tu terminal de comandos en la carpeta del proyecto e \*\*instala las dependencias necesarias\*\*:

&#x20;  ```bash

&#x20;  pip install streamlit openai pandas openpyxl pypdf fpdf2

&#x20;  ```

3\. \*\*Arranca el servidor local\*\* ejecutando:

&#x20;  ```bash

&#x20;  python -m streamlit run app.py

&#x20;  ```



\## 📖 Requisitos de Uso para el Usuario

Para que la IA genere el informe, se requiere introducir una \*\*OpenAI API Key\*\* válida en la barra lateral con saldo de crédito disponible, adjuntar el Excel de analíticas descargado de LinkedIn y la captura de pantalla del SSI en formato de imagen (PNG/JPG).



