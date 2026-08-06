# 🧲 LinkedIn Creator & SSI Report Generator

Esta es una microaplicación inteligente desarrollada en Python y Streamlit diseñada para generar un **informe estratégico ejecutivo de 2 páginas en formato PDF** analizando el perfil de LinkedIn del usuario. 

El sistema utiliza el motor de Inteligencia Artificial de OpenAI (`GPT-4o`) combinado con capacidades de visión para procesar datos reales y gráficos sin necesidad de conectar con la restrictiva API oficial de LinkedIn.

---

### ⚠️ AVISO IMPORTANTE SOBRE COSTES Y PRIVACIDAD
Para garantizar la **máxima privacidad**, esta aplicación es de código abierto y **no almacena tus datos ni tus claves** en ninguna base de datos externa. Todo se procesa en tiempo real.

Por este motivo, **cada usuario debe aportar su propia OpenAI API Key** en la interfaz para poder utilizarla. Cada informe generado consume un coste ínfimo de aproximadamente **0,03€ (3 céntimos de euro)** del saldo de tu cuenta de OpenAI.

---

## 🛠️ Características Principales
- **Análisis de Visión Integrado**: El usuario solo necesita subir una captura de pantalla de su Social Selling Index (SSI) y la IA la interpretará de forma visual.
- **Procesamiento de Datos Estructurados**: Permite la carga directa del reporte Excel (`.xlsx`) o PDF exportado nativamente de las analíticas de creador de LinkedIn.
- **Filtro de Antigüedad Quirúrgico**: Evita falsos diagnósticos al permitir introducir la fecha exacta de alta en la plataforma, calculando los promedios de rendimiento basándose únicamente en los meses de actividad real.
- **Exportación Limpia**: Genera un archivo PDF maquetado y listo para descargar en formato A4.

## 📖 Instrucciones de Uso para el Visitante

1. **🔑 Consigue tu OpenAI API Key**: Regístrate o inicia sesión en [://openai.com](https://://openai.com/), ve a la sección *API Keys*, crea una nueva llave y copia el código que empieza por `sk-...`. *(Asegúrate de tener al menos el mínimo de 5$ de saldo cargado en la pestaña 'Billing' de tu cuenta de OpenAI)*.
2. **📊 Descarga tus Analíticas de LinkedIn**: Accede a tu sección de *Analíticas de Creador* en LinkedIn, haz clic en el botón **Exportar** (arriba a la derecha) y descarga el archivo **Excel (.xlsx)** o **PDF**.
3. **🎯 Captura tu SSI**: Visita [://linkedin.com](https://www.linkedin.com/sales/ssi/) y haz una captura de pantalla de tus gráficas (Recomiendo usar el zoom de la web al 65-50% y efectuar captura con Herramienta de recorte, pj.) . Guárdala como **imagen (PNG o JPG)**.
4. **🚀 Ejecuta la aplicación**: Introduce tus archivos y tu clave en la interfaz web para obtener tu plan de acción en 3 fases de inmediato.


Para que la IA genere el informe, se requiere introducir una \*\*OpenAI API Key\*\* válida en la barra lateral con saldo de crédito disponible, adjuntar el Excel de analíticas descargado de LinkedIn y la captura de pantalla del SSI en formato de imagen (PNG/JPG).



