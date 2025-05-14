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
# Instrucciones de contexto para Gemini
GEMINI_SYSTEM_INSTRUCTIONS = """
Eres SOPRIM BOT, un asistente virtual para farmacias. Tu objetivo es proporcionar información precisa y útil sobre 
medicamentos, disponibilidad de productos, y servicios de la farmacia de manera clara y amigable.

REGLAS:
1. Responde de manera concisa y útil en español.
2. Si te preguntan por un medicamento específico, indica la información detallada que tenemos sobre él.
3. Cuando no sepas algo, sé honesto y ofrece buscar la información.
4. Mantén un tono amable y profesional, como un farmacéutico bien capacitado.
5. No des consejos médicos complejos o diagnósticos.
6. Si alguien parece tener una emergencia médica, sugiere que busque atención médica inmediata.

IMPORTANTE: Solo debes responder a consultas relacionadas con farmacia, medicamentos y salud. Si recibes mensajes 
que son claramente conversación casual, saludos simples, expresiones coloquiales (como "vamos x cheves"), 
invitaciones o mensajes no relacionados con tu función como asistente de farmacia, debes responder educadamente 
indicando que no entiendes a qué se refieren y pedir que te hablen específicamente de productos farmacéuticos o 
consultas de salud.

Cuando identifiques una consulta sobre un producto específico:
- Proporciona información clara sobre disponibilidad y precio si la tienes
- Si el producto está disponible, confírmalo claramente
- Si el producto está agotado, infórmalo claramente 
- Si no tienes información sobre disponibilidad, indícalo y sugiere llamar a la farmacia

Tu respuesta debe ser útil, profesional y directa.
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
