"""
Servicio para interactuar con la API de Gemini.
Encapsula toda la lógica relacionada con la generación de respuestas de IA.
Actualizado para incluir información sobre la fuente del producto.
"""
import logging
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_SYSTEM_INSTRUCTIONS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
        
        # Log de información básica (sin exponer la clave completa)
        api_key_preview = self.api_key[:4] + "..." if self.api_key and len(self.api_key) > 8 else "No disponible"
        logger.info(f"Inicializando GeminiService con modelo: {self.model_name}")
        logger.info(f"API Key (primeros caracteres): {api_key_preview}")
        
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
            logger.info(f"Enviando prompt a Gemini para respuesta general. Mensaje: '{user_message[:50]}...'")
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"Respuesta recibida de Gemini ({len(response_text)} caracteres)")
            logger.debug(f"Respuesta: {response_text[:100]}...")
            
            return response_text
        except Exception as e:
            logger.error(f"Error en generate_response: {e}")
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"
    
    def generate_product_response(self, user_message, product_info, additional_context=""):
        """
        Genera una respuesta basada en el mensaje del usuario y la información del producto.
        Ahora incluye información sobre la fuente del producto.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            product_info (dict): Información del producto obtenida mediante scraping
            additional_context (str): Contexto adicional para el prompt
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            # Formatear la información del producto
            if product_info:
                # Identificar la fuente del producto
                fuente = product_info.get('fuente', 'No especificada')
                precio_campo = "precio" if "precio" in product_info else "precio_publico" if "precio_publico" in product_info else "mi_precio"
                precio = product_info.get(precio_campo, 'No disponible')
                
                product_details = f"""
Información del producto encontrado en {fuente}:
- Nombre: {product_info.get('nombre', 'No disponible')}
- Laboratorio: {product_info.get('laboratorio', 'No disponible')}
- Código de barras: {product_info.get('codigo_barras', 'No disponible')}
- Registro sanitario: {product_info.get('registro_sanitario', 'No disponible')}
- URL del producto: {product_info.get('url', 'No disponible')}
- Precio: {precio}
- Existencia: {product_info.get('existencia', 'No disponible')}
"""
            else:
                product_details = "No se encontró información específica sobre este producto en nuestra base de datos."
            
            # Crear el prompt completo con contexto adicional
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Mensaje del cliente: {user_message}
{product_details}
{additional_context}
Basándote en esta información, proporciona una respuesta útil y profesional al cliente sobre el producto solicitado.
Incluye siempre el precio en tu respuesta cuando esté disponible.
Si el precio está disponible, menciónalo claramente al cliente e indícale que puede confirmar la disponibilidad llamando a la farmacia o visitando la tienda.
Si el precio no está disponible, indícale al cliente que puede consultar el precio y disponibilidad llamando a la farmacia o visitando la tienda.
Si el producto tiene información de existencia, menciona si está disponible o no.
"""
            logger.info(f"Enviando prompt a Gemini para respuesta de producto. Mensaje: '{user_message[:50]}...'")
            logger.debug(f"Información del producto: {product_info}")
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"Respuesta de producto recibida de Gemini ({len(response_text)} caracteres)")
            logger.debug(f"Respuesta: {response_text[:100]}...")
            
            return response_text
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
            logger.info(f"Enviando prompt a Gemini para detectar producto. Mensaje: '{user_message}'")
            
            # MODIFICACIÓN TEMPORAL: Para pruebas, puedes descomentar esta línea para forzar la detección
            # Si el mensaje contiene "paracetamol", "ibuprofeno" u otros medicamentos comunes
            medicamentos_comunes = ["paracetamol", "ibuprofeno", "aspirina", "omeprazol", "loratadina", "antibiotico"]
            mensaje_lower = user_message.lower()
            for med in medicamentos_comunes:
                if med in mensaje_lower:
                    logger.info(f"Producto detectado localmente: {med}")
                    return "consulta_producto", med
            
            # Si no se detectó localmente, consultar a Gemini
            response = self.model.generate_content(prompt)
            resp = response.text.strip()
            
            logger.info(f"Respuesta de Gemini para detección de producto: '{resp}'")
            
            # Procesar la respuesta
            if resp.upper() == "GENERAL":
                logger.info("Detectado como consulta general")
                return "consulta_general", None
            else:
                # Limpiar la respuesta para obtener solo el nombre del medicamento
                producto = resp.strip()
                logger.info(f"Detectado como consulta de producto: '{producto}'")
                return "consulta_producto", producto
        except Exception as e:
            logger.error(f"Error en detectar_producto: {e}")
            # En caso de error, usar detección local básica (palabras clave) como respaldo
            mensaje_lower = user_message.lower()
            if "tienes" in mensaje_lower or "tienen" in mensaje_lower or "hay" in mensaje_lower:
                for palabra in mensaje_lower.split():
                    if len(palabra) > 4 and palabra not in ["tienes", "tienen", "ustedes", "algún", "alguna", "donde", "cuánto", "cuanto"]:
                        logger.info(f"Respaldo: Producto detectado: {palabra}")
                        return "consulta_producto", palabra
            
            logger.info("Respaldo: Consulta general")
            return "consulta_general", None
