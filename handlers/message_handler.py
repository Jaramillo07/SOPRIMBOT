"""
Manejador de mensajes para SOPRIM BOT.
Orquesta la interacción entre los diferentes servicios.
VERSIÓN SIMPLIFICADA PARA SOLUCIÓN DE PROBLEMAS
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
        logger.info("Inicializando MessageHandler")
        self.gemini_service = GeminiService()
        self.whatsapp_service = WhatsAppService()
        self.scraping_service = ScrapingService()
        logger.info("MessageHandler inicializado correctamente")
    
    async def procesar_mensaje(self, mensaje, phone_number):
        """
        Procesa un mensaje entrante y genera una respuesta.
        IMPLEMENTACIÓN SIMPLIFICADA PARA PRUEBAS
        
        Args:
            mensaje (str): Mensaje entrante del usuario
            phone_number (str): Número de teléfono del remitente
            
        Returns:
            dict: Resultado de la operación
        """
        logger.info(f"procesar_mensaje: '{mensaje}' de {phone_number}")
        
        # Esta implementación es simplificada para pruebas
        # Solo genera una respuesta genérica sin scraping ni comprobaciones
        
        respuesta = f"Gracias por tu mensaje: '{mensaje}'. Estamos procesándolo."
        
        try:
            # Intentar enviar mensaje (solo para pruebas)
            resultado = self.whatsapp_service.send_text_message(phone_number, respuesta)
            logger.info(f"Resultado del envío: {resultado}")
            
            return {
                "success": True,
                "message_type": "test",
                "respuesta": respuesta
            }
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
            return {
                "success": False,
                "message_type": "error",
                "error": str(e),
                "respuesta": respuesta
            }
