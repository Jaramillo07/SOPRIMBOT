"""
Manejador de mensajes para SOPRIM BOT.
Orquesta la interacción entre los diferentes servicios.
"""
import logging
import re
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService
from config.settings import ALLOWED_TEST_NUMBERS, GEMINI_SYSTEM_INSTRUCTIONS

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
    
    def detectar_tipo_mensaje(self, mensaje):
        """
        Detecta el tipo de mensaje basado en su contenido.
        
        Args:
            mensaje (str): Mensaje a analizar
            
        Returns:
            tuple: (tipo_mensaje, producto_detectado)
        """
        mensaje_lower = mensaje.lower()
        producto_detectado = None
        
        # Patrones para detectar consultas sobre productos farmacéuticos
        patrones_producto = [
            r'(?:tienes|tienen|venden|hay|disponible|disponibles)\s+(.+?)(?:\?|$)',
            r'(?:busco|necesito|quiero)\s+(.+?)(?:\?|$)',
            r'(?:me pueden conseguir|consiguen)\s+(.+?)(?:\?|$)',
            r'(?:vende[ns]|tiene[ns])\s+(.+?)(?:\?|$)',
            r'(?:precio de|cuánto cuesta|costo de|valor de)\s+(.+?)(?:\?|$)'
        ]
        
        # Buscar coincidencias en los patrones
        for patron in patrones_producto:
            match = re.search(patron, mensaje_lower)
            if match:
                producto_detectado = match.group(1).strip()
                # Limpiar términos comunes que no son parte del producto
                terminos_eliminar = ["el", "la", "los", "las", "algún", "alguna", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas"]
                for termino in terminos_eliminar:
                    if producto_detectado.startswith(f"{termino} "):
                        producto_detectado = producto_detectado[len(termino)+1:]
                
                logger.info(f"Producto detectado: {producto_detectado}")
                return "consulta_producto", producto_detectado
        
        # Palabras clave que podrían indicar que se está hablando de un medicamento
        palabras_medicamento = ["paracetamol", "ibuprofeno", "aspirina", "omeprazol", "loratadina", "antibiotico", "ampicilina", "penicilina", "clindamicina"]
        for palabra in palabras_medicamento:
            if palabra in mensaje_lower:
                logger.info(f"Medicamento detectado por palabra clave: {palabra}")
                return "consulta_producto", palabra
        
        # Verificación adicional para medicamentos
        if "medicina" in mensaje_lower or "medicamento" in mensaje_lower or "pastilla" in mensaje_lower:
            # Buscar palabras largas que podrían ser nombres de medicamentos
            palabras = mensaje_lower.split()
            for palabra in palabras:
                if len(palabra) > 5 and palabra not in ["medicina", "medicamento", "pastilla", "farmacia", "necesito", "quiero", "busco", "tienen", "venden"]:
                    logger.info(f"Posible medicamento detectado: {palabra}")
                    return "consulta_producto", palabra
        
        # Por defecto, considerar como consulta general
        return "consulta_general", None
    
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
        
        # 0) Verificar si el número está en la lista de permitidos
        formatted_number = self.whatsapp_service.format_phone_number(phone_number)
        logger.info(f"Número formateado: {formatted_number}")
        if formatted_number not in ALLOWED_TEST_NUMBERS:
            logger.warning(f"Número {formatted_number} no está en la lista de permitidos: {ALLOWED_TEST_NUMBERS}")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": f"El número {formatted_number} no está en la lista de números permitidos para pruebas",
                "respuesta": None
            }
        else:
            logger.info(f"Número {formatted_number} está en la lista de permitidos")
        
        # 1) Ignorar saludos y mensajes personales
        if self.es_mensaje_a_ignorar(mensaje):
            logger.info(f"Mensaje ignorado: '{mensaje}'")
            return {
                "success": True,
                "message_type": "ignorado",
                "respuesta": None
            }
        
        # 2) Detectar tipo de mensaje localmente primero
        tipo_mensaje, producto_detectado = self.detectar_tipo_mensaje(mensaje)
        logger.info(f"Tipo de mensaje detectado localmente: {tipo_mensaje}, producto: {producto_detectado}")
        
        # Si no detectamos localmente, intentar con Gemini
        if tipo_mensaje != "consulta_producto" or not producto_detectado:
            try:
                tipo_mensaje_gemini, producto_detectado_gemini = self.gemini_service.detectar_producto(mensaje)
                if tipo_mensaje_gemini == "consulta_producto" and producto_detectado_gemini:
                    tipo_mensaje = tipo_mensaje_gemini
                    producto_detectado = producto_detectado_gemini
                    logger.info(f"Gemini detectó: {tipo_mensaje}, producto: {producto_detectado}")
            except Exception as e:
                logger.error(f"Error al detectar producto con Gemini: {e}")
                # Continuamos con la detección local en caso de error
        
        # 3) Si es consulta de producto, hacemos scraping
        if tipo_mensaje == "consulta_producto" and producto_detectado:
            logger.info(f"Iniciando búsqueda de información para: {producto_detectado}")
            try:
                # MODIFICADO: Ahora especificamos que queremos usar el scraper de Difarmer
                product_info = self.scraping_service.buscar_producto(producto_detectado, fuente="difarmer")
                
                if product_info:
                    logger.info(f"Información encontrada para {producto_detectado}: {product_info}")
                    respuesta = self.gemini_service.generate_product_response(mensaje, product_info)
                    
                    # Intentar enviar respuesta
                    result = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
                    
                    # Verificar si hubo error de sandbox
                    if result.get("text", {}).get("sandbox_restriction"):
                        logger.error("Error de sandbox al enviar respuesta de producto")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result["text"].get("error"),
                            "suggestion": result["text"].get("suggestion"),
                            "respuesta": respuesta
                        }
                    
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
                        f"No encontré información específica sobre {producto_detectado}. {mensaje}"
                    )
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    # Verificar si hubo error de sandbox
                    if result.get("sandbox_restriction"):
                        logger.error("Error de sandbox al enviar respuesta de producto no encontrado")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result.get("error"),
                            "suggestion": result.get("suggestion"),
                            "respuesta": respuesta
                        }
                    
                    return {
                        "success": True,
                        "message_type": "producto_no_encontrado",
                        "producto": producto_detectado,
                        "respuesta": respuesta
                    }
            except Exception as e:
                logger.error(f"Error durante el scraping: {e}")
                # En caso de error, caer en respuesta general
        
        # 4) En cualquier otro caso, respuesta general
        logger.info("Generando respuesta general con Gemini")
        respuesta = self.gemini_service.generate_response(mensaje)
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        
        # Verificar si hubo error de sandbox
        if result.get("sandbox_restriction"):
            logger.error("Error de sandbox al enviar respuesta general")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": result.get("error"),
                "suggestion": result.get("suggestion"),
                "respuesta": respuesta
            }
        
        return {
            "success": True,
            "message_type": "general",
            "respuesta": respuesta
        }
