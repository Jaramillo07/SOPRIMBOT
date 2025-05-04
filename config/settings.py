"""
Archivo de configuración para SOPRIM BOT.
Centraliza todas las claves API y parámetros de configuración.
Ahora adaptado a Twilio Sandbox para WhatsApp.
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
