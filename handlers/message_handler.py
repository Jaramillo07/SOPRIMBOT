"""
Manejador de mensajes para SOPRIM BOT.
Orquesta la interacción entre los diferentes servicios.
"""
import logging
import re
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageHandler:
    """
    Clase que maneja los mensajes entrantes y coordina las respuestas.
    """
    
    def __init__(self):
        """
        Inicializa el manejador de mensajes con sus servicios asociados.
        """
        self.gemini_service = GeminiService()
        self.whatsapp_service = WhatsAppService()
        self.scraping_service = ScrapingService()
    
    def format_whatsapp_number(self, phone_number):
        """
        Asegura que el número de teléfono tenga el formato correcto para WhatsApp API.
        Añade el signo "+" si no está presente.
        """
        # Eliminar cualquier espacio, guion u otro carácter no numérico excepto el "+"
        cleaned_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Asegurarse de que tiene el signo "+"
        if not cleaned_number.startswith('+'):
            cleaned_number = '+' + cleaned_number
            
        logger.info(f"Número original: {phone_number} -> Formateado: {cleaned_number}")
        return cleaned_number
    
    def es_mensaje_a_ignorar(self, mensaje: str) -> bool:
        """
        Determina si un mensaje debe ser ignorado por ser saludo o conversación personal.
        
        Args:
            mensaje (str): Mensaje a analizar
            
        Returns:
            bool: True si el mensaje debe ignorarse, False si debe procesarse
        """
        m = mensaje.lower().strip()
        # Ignorar mensajes muy cortos
        if len(m) <= 3:
            return True
        
        # Patrones de conversación personal o saludos
        patrones_no_relevantes = [
            r"(?:hola|buenos días|buenas tardes|buenas noches)\b",
            r"(?:nos vemos|quedamos|vernos|hablamos|te llamo)",
            r"(?:a qué hora|cuando|dónde|donde|cómo|como).*?",
            r"(?:qué|que).*(?:haces|planes|te parece)",
            r"(?:te extraño|te quiero|te amo|me gustas)",
            r"\b(amigo|amiga|carnal|compadre|hermano)\b",
            r"(?:fiesta|película|cine|restaurante|bar|café|plaza|concierto)",
            r"(?:cita|vernos|salir)",
            r"(?:ya llegaste|ya estoy|estoy en|llego en)",
            r"(?:te llamé|te marqué|no contestas|contesta)"
        ]
        for patron in patrones_no_relevantes:
            if re.search(patron, m):
                logger.info(f"Ignorado por patrón personal: {patron}")
                return True
        
        # Saludos simples exactos
        saludos_simples = [
            r"^hola[\s,.!?]*$",
            r"^hey[\s,.!?]*$",
            r"^hi[\s,.!?]*$",
            r"^buenas[\s,.!?]*$"
        ]
        for saludo in saludos_simples:
            if re.match(saludo, m):
                logger.info(f"Ignorado por saludo simple: {m}")
                return True
        
        return False
    
    async def procesar_mensaje(self, mensaje: str, phone_number: str) -> dict:
        """
        Procesa un mensaje entrante y genera una respuesta.
        
        Args:
            mensaje (str): Mensaje entrante del usuario
            phone_number (str): Número de teléfono del remitente
            
        Returns:
            dict: Resultado de la operación
        """
        logger.info(f"Procesando mensaje: '{mensaje}' de {phone_number}")
        
        # Formatear el número de teléfono para asegurar que tiene el signo "+"
        formatted_phone = self.format_whatsapp_number(phone_number)
        
        # 1) Ignorar saludos y mensajes personales
        if self.es_mensaje_a_ignorar(mensaje):
            logger.info(f"Mensaje ignorado: '{mensaje}'")
            return {
                "success": True,
                "message_type": "ignorado",
                "respuesta": None
            }
        
        # 2) Delegar a Gemini la detección de consulta de producto
        tipo_mensaje, producto_detectado = self.gemini_service.detectar_producto(mensaje)
        logger.info(f"Tipo de mensaje detectado: {tipo_mensaje}, producto: {producto_detectado}")
        
        # 3) Si es consulta de producto, hacemos scraping
        if tipo_mensaje == "consulta_producto" and producto_detectado:
            product_info = self.scraping_service.buscar_producto(producto_detectado)
            
            if product_info:
                logger.info(f"Información encontrada para {producto_detectado}")
                respuesta = self.gemini_service.generate_product_response(mensaje, product_info)
                self.whatsapp_service.send_product_response(formatted_phone, respuesta, product_info)
                return {
                    "success": True,
                    "message_type": "producto",
                    "producto": producto_detectado,
                    "tiene_imagen": bool(product_info.get("imagen")),
                    "respuesta": respuesta
                }
            else:
                logger.info(f"No se encontró información para {producto_detectado}")
                respuesta = self.gemini_service.generate_response(
                    f"No encontré información específica sobre {producto_detectado}."
                )
                self.whatsapp_service.send_text_message(formatted_phone, respuesta)
                return {
                    "success": True,
                    "message_type": "producto_no_encontrado",
                    "producto": producto_detectado,
                    "respuesta": respuesta
                }
        
        # 4) En cualquier otro caso, respuesta general
        logger.info("Generando respuesta general con Gemini")
        respuesta = self.gemini_service.generate_response(mensaje)
        self.whatsapp_service.send_text_message(formatted_phone, respuesta)
        return {
            "success": True,
            "message_type": "general",
            "respuesta": respuesta
        }
