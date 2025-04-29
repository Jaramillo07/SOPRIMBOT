"""
Servicio para interactuar con la API de Gemini.
Encapsula toda la lógica relacionada con la generación de respuestas de IA.
"""
import logging
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_SYSTEM_INSTRUCTIONS

# Configurar logging
logger = logging.getLogger(__name__)

class GeminiService:
    """
    Clase que proporciona métodos para interactuar con la API de Gemini.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de Gemini configurando la API key.
        """
        self.api_key = GEMINI_API_KEY
        self.model_name = GEMINI_MODEL
        
        # Log de información de inicialización
        logger.info(f"Inicializando GeminiService con modelo: {self.model_name}")
        logger.info(f"API Key (primeros 4 caracteres): {self.api_key[:4] if self.api_key and len(self.api_key) > 4 else 'No disponible'}")
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info("Modelo Gemini inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar el modelo Gemini: {e}")
            raise
    
    def generate_response(self, user_message):
        """
        Genera una respuesta basada en el mensaje del usuario utilizando Gemini.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            prompt = f"{GEMINI_SYSTEM_INSTRUCTIONS}\n\nMensaje del cliente: {user_message}"
            logger.info(f"Enviando prompt a Gemini [generate_response]: {prompt[:100]}...")
            response = self.model.generate_content(prompt)
            
            logger.info(f"Respuesta recibida de Gemini [generate_response]: {response.text[:100]}...")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error en generate_response: {e}")
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"
    
    def generate_product_response(self, user_message, product_info):
        """
        Genera una respuesta basada en el mensaje del usuario y la información del producto.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            product_info (dict): Información del producto obtenida mediante scraping
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            if product_info:
                product_details = f"""
Información del producto encontrado:
- Nombre: {product_info.get('nombre', 'No disponible')}
- Laboratorio: {product_info.get('laboratorio', 'No disponible')}
- Código de barras: {product_info.get('codigo_barras', 'No disponible')}
- Registro sanitario: {product_info.get('registro_sanitario', 'No disponible')}
- URL del producto: {product_info.get('url', 'No disponible')}
"""
            else:
                product_details = "No se encontró información específica sobre este producto en nuestra base de datos."
            
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Mensaje del cliente: {user_message}
{product_details}
Basándote en esta información, proporciona una respuesta útil y profesional al cliente sobre el producto solicitado.
Si no tienes información específica sobre la disponibilidad actual, responde que verificarás si el producto está disponible
y que el cliente puede consultar llamando a la farmacia o visitando la tienda.
"""
            logger.info(f"Enviando prompt a Gemini [generate_product_response]: {prompt[:100]}...")
            response = self.model.generate_content(prompt)
            
            logger.info(f"Respuesta recibida de Gemini [generate_product_response]: {response.text[:100]}...")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error en generate_product_response: {e}")
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"
    
    def detectar_producto(self, user_message):
        """
        Usa Gemini para determinar si el mensaje pregunta por un medicamento específico.
        Si es así devuelve ('consulta_producto', '<nombre_del_medicamento>')
        Si no, devuelve ('consulta_general', None).
        """
        prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Determina SI el siguiente mensaje está preguntando por un medicamento específico.
- Si SÍ, responde SOLO con el nombre del medicamento (p. ej. "paracetamol", "ibuprofeno").
- Si NO, responde exactamente con la palabra GENERAL.
Mensaje: "{user_message}"
"""
        try:
            logger.info(f"Enviando prompt a Gemini [detectar_producto]: {prompt[:100]}...")
            response = self.model.generate_content(prompt)
            resp = response.text.strip()
            
            # Log completo de la respuesta de Gemini
            logger.info(f"Respuesta completa de Gemini [detectar_producto]: '{resp}'")
            
            # Verificación más específica
            if resp.upper() == "GENERAL":
                logger.info("Detectado como consulta general")
                return "consulta_general", None
            else:
                # Intentar limpiar la respuesta para asegurar que solo tenemos el nombre del medicamento
                producto = resp.strip()
                logger.info(f"Detectado como consulta de producto: '{producto}'")
                return "consulta_producto", producto
        except Exception as e:
            logger.error(f"Error en detectar_producto: {e}")
            # En caso de error, caemos en consulta general
            return "consulta_general", None

        # Solución temporal: Si queremos forzar la detección de productos para pruebas
        # Descomentar esta línea para pruebas:
        # return "consulta_producto", user_message
