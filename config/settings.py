"""
Archivo de configuración para SOPRIM BOT.
Centraliza todas las claves API y parámetros de configuración.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

# Configuración de Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAdUgrPytizzW1O6N-dUFaBfTHahklE46c")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro-latest")

# Configuración de WhatsApp Business API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "EAA0Oho96A6kBO9weiEgaDaoTZCvtZCM6FlahHoZAbyYIpZBKpYt8wqLuN4Qazp7NRYZCfmHTwFrONQJymXNaxi5mWXLtHuMpz3SoU5ZAzNwgkhBYZByyKdZCxD6OhnZA9XDQpJI2luWGe50ZBebf6fe491r8Oel9EHpj5IZCGguEnfnTMSnGeZBSelkYPCUbBIxfFW9XrlxU5Ljm2h8ZAOqJd3nffnVM3ZB4kZD")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "637876229407517")
WHATSAPP_VERSION = os.getenv("WHATSAPP_VERSION", "v22.0")
WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_VERSION}/{WHATSAPP_PHONE_ID}/messages"

# Números de teléfono permitidos para pruebas
# Formato: lista de números en formato internacional completo con el signo "+"
ALLOWED_TEST_NUMBERS = [
    "+524778150806",
    "+5214777150806",
    "+5214778150806",
   
# Configuración del scraping
HEADLESS_BROWSER = os.getenv("HEADLESS_BROWSER", "True").lower() in ("true", "1", "t")

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
"""

# Modo de desarrollo
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

# Token de verificación para el webhook de WhatsApp
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "soprim123")
