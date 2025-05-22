"""
Archivo de configuración para SOPRIM BOT.
Centraliza todas las claves API y parámetros de configuración.
Ahora adaptado para incluir Google Cloud Vision para OCR.
"""
import os
from dotenv import load_dotenv
# Cargar variables de entorno desde archivo .env si existe
load_dotenv()
# --------------------------------------------------
# Configuración de Gemini (IA)
# --------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro-latest")

# ✅ Instrucciones de contexto para Gemini - SIN REFERENCIAS MÉDICAS
GEMINI_SYSTEM_INSTRUCTIONS = """
Eres SOPRIM BOT, un asistente virtual para una farmacia. Tu objetivo es proporcionar información comercial sobre 
productos, disponibilidad, precios y servicios de entrega de manera clara y amigable.

REGLAS CRÍTICAS:
1. Responde de manera concisa y útil en español.
2. NUNCA des información médica, efectos secundarios, indicaciones o contraindicaciones.
3. NO menciones que algo es un "medicamento" - solo llámalo "producto".
4. NO ofrezcas consultas médicas o farmacéuticas.
5. NO menciones "receta médica" - si algo requiere receta, solo di "requiere presentar receta".
6. SOLO enfócate en información comercial: precio, disponibilidad, entrega, datos del pedido.
7. Mantén un tono comercial amigable, no médico.
8. Si alguien pregunta sobre efectos o uso médico, deriva a "consulte con su médico".
9. Si el usuario envía una imagen con texto, como una receta o una fotografía de un producto, procesa esa información como si fuera texto.
10. Para emergencias médicas, sugiere buscar atención médica inmediata.

ENFOQUE: Eres un asistente de ventas farmacéuticas, no un consejero médico.
"""

# --------------------------------------------------
# Configuración de Twilio WhatsApp Sandbox
# --------------------------------------------------
# Estas tres variables debes definirlas en tu entorno (Cloud Run o .env):
TWILIO_ACCOUNT_SID             = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN              = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_SANDBOX_NUMBER = os.getenv(
    "TWILIO_WHATSAPP_SANDBOX_NUMBER",
    "whatsapp:+14155238886"
)
# --------------------------------------------------
# Configuración de Google Cloud Vision (OCR)
# --------------------------------------------------
# Si usas GOOGLE_APPLICATION_CREDENTIALS, no necesitas la API_KEY
GOOGLE_CLOUD_VISION_API_KEY = os.getenv("GOOGLE_CLOUD_VISION_API_KEY", "")
# Ruta al archivo de credenciales de Google Cloud (alternativa a la API_KEY)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
# --------------------------------------------------
# Números permitidos (opcional)
# --------------------------------------------------
# Si quieres mantener un whitelist de pruebas, ponlos sin el prefijo "whatsapp:"
ALLOWED_TEST_NUMBERS = [
    "+5214778150806",
    # otros números de prueba...
]
# --------------------------------------------------
# Configuración de scraping (si aplica)
# --------------------------------------------------
HEADLESS_BROWSER = os.getenv("HEADLESS_BROWSER", "True").lower() in ("true", "1", "t")
# --------------------------------------------------
# Modo de desarrollo y verificación de webhook
# --------------------------------------------------
DEBUG         = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
VERIFY_TOKEN  = os.getenv("VERIFY_TOKEN", "soprim123")
