"""
Manejador de mensajes para SOPRIM BOT.
Adaptado para trabajar con múltiples scrapers y procesar imágenes.
"""
import logging
import re
import traceback
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService
from services.ocr_service import OCRService  # Importar el servicio OCR
from services.firestore_service import obtener_historial, guardar_interaccion
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
    Adaptada para trabajar con múltiples scrapers, almacenar historial y procesar imágenes.
    """
    
    def __init__(self):
        """
        Inicializa el manejador de mensajes con sus servicios asociados.
        """
        logger.info("Inicializando MessageHandler con soporte para múltiples scrapers, Firestore y procesamiento de imágenes")
        self.gemini_service = GeminiService()
        self.whatsapp_service = WhatsAppService()
        self.scraping_service = ScrapingService()
        self.ocr_service = OCRService()  # Inicializar el servicio OCR
        logger.info("MessageHandler inicializado correctamente")
    
    def es_mensaje_a_ignorar(self, mensaje: str) -> bool:
        """
        Determina si un mensaje debe ser ignorado por ser saludo o conversación personal.
        
        Args:
            mensaje (str): Mensaje a analizar
            
        Returns:
            bool: True si el mensaje debe ignorarse, False si debe procesarse
        """
        # Si el mensaje está vacío, no ignoramos porque podría ser solo una imagen
        if not mensaje or mensaje.strip() == "":
            return False
            
        m = mensaje.lower().strip()
        # Ignorar mensajes muy cortos
        if len(m) <= 3:
            return True
        
        # Patrones de conversación personal o saludos
        patrones_no_relevantes = [
            r"(?:nos vemos|quedamos|vernos|hablamos|te llamo)",
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
            if re.fullmatch(saludo, m):  # solo si el saludo es TODO el mensaje
                logger.info(f"Ignorado por saludo simple aislado: {m}")
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
        palabras_medicamento = ["paracetamol", "ibuprofeno", "aspirina", "omeprazol", "loratadina", "antibiotico", "ampicilina", "penicilina", "clindamicina", "rapamune", "sirolimus"]
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
    
    async def procesar_mensaje(self, mensaje: str, phone_number: str, media_urls: list = None):
        """
        Procesa un mensaje entrante y genera una respuesta.
        Adaptado para trabajar con múltiples scrapers, mantener historial y procesar imágenes.
        
        Args:
            mensaje (str): Mensaje entrante del usuario
            phone_number (str): Número de teléfono del remitente
            media_urls (list, optional): Lista de URLs de imágenes adjuntas
            
        Returns:
            dict: Resultado de la operación
        """
        logger.info(f"Procesando mensaje: '{mensaje}' de {phone_number}")
        if media_urls:
            logger.info(f"El mensaje incluye {len(media_urls)} imágenes: {media_urls}")
        
        # Limpiar el número de teléfono para Firestore
        clean_phone = phone_number.replace("whatsapp:", "")
        
        # Verificar si el número está en la lista de permitidos (solo en pruebas)
        formatted_number = self.whatsapp_service.format_phone_number(phone_number)
        logger.info(f"Número formateado: {formatted_number}")
        if ALLOWED_TEST_NUMBERS and formatted_number not in ALLOWED_TEST_NUMBERS:
            logger.warning(f"Número {formatted_number} no está en la lista de permitidos: {ALLOWED_TEST_NUMBERS}")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": f"El número {formatted_number} no está en la lista de números permitidos para pruebas",
                "respuesta": None
            }
        else:
            logger.info(f"Número {formatted_number} está permitido para interacción")
        
        # NUEVO: Procesar imágenes si hay alguna con mejor manejo de errores
        texto_extraido = ""
        if media_urls:
            logger.info(f"Procesando {len(media_urls)} imágenes con OCR...")
            try:
                texto_extraido = await self.ocr_service.process_images(media_urls)
                logger.info(f"Resultado del procesamiento OCR: {texto_extraido[:200] if texto_extraido else 'No hay texto'}")
                
                if texto_extraido and not texto_extraido.startswith("No se pudo"):
                    logger.info(f"Texto extraído con éxito: {texto_extraido[:100]}...")
                    # Si no hay mensaje de texto, usamos solo el texto extraído
                    if not mensaje or mensaje.strip() == "":
                        mensaje = texto_extraido
                    else:
                        # Si hay ambos, los combinamos
                        mensaje = f"{mensaje}\n\n[Texto de la imagen: {texto_extraido}]"
                    
                    logger.info(f"Mensaje combinado: {mensaje[:100]}...")
                else:
                    logger.warning("No se pudo extraer texto de las imágenes")
                    if not mensaje or mensaje.strip() == "":
                        # Si solo recibimos una imagen sin texto y no pudimos extraer texto
                        respuesta = "He recibido tu imagen pero no he podido extraer texto de ella. ¿Podrías enviar el mensaje en formato texto o una imagen más clara?"
                        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                        return {
                            "success": True,
                            "message_type": "error_ocr",
                            "respuesta": respuesta
                        }
            except Exception as e:
                logger.error(f"Error al procesar imágenes: {e}")
                logger.error(traceback.format_exc())
                # Si solo tenemos imagen y falló el procesamiento, informar al usuario
                if not mensaje or mensaje.strip() == "":
                    respuesta = "Lo siento, hubo un problema técnico al procesar tu imagen. ¿Podrías enviar tu consulta en formato texto?"
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    return {
                        "success": False,
                        "message_type": "error_imagen",
                        "error": str(e),
                        "respuesta": respuesta
                    }
        
        # 1) Ignorar saludos y mensajes personales
        if self.es_mensaje_a_ignorar(mensaje):
            logger.info(f"Mensaje ignorado: '{mensaje}'")
            return {
                "success": True,
                "message_type": "ignorado",
                "respuesta": None
            }
        
        # Obtener historial de conversación de Firestore (10 turnos por defecto)
        historial = obtener_historial(clean_phone)
        logger.info(f"Recuperado historial para {clean_phone}: {len(historial)} turnos")
        
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
        
        # 3) Si es consulta de producto, hacemos scraping con los scrapers disponibles
        if tipo_mensaje == "consulta_producto" and producto_detectado:
            logger.info(f"Iniciando búsqueda para: {producto_detectado}")
            try:
                # Llamar al servicio de scraping integrado
                product_info = self.scraping_service.buscar_producto(producto_detectado)
                
                if product_info:
                    logger.info(f"Información encontrada para {producto_detectado} en {product_info.get('fuente', 'farmacia')}")
                    
                    # Añadir información sobre la farmacia para inclusión en la respuesta
                    farmacia_nombre = product_info.get('nombre_farmacia', product_info.get('fuente', 'farmacia'))
                    additional_context = f"Esta información proviene de {farmacia_nombre}."
                    
                    # Generar respuesta con Gemini incluyendo el historial
                    respuesta = self.gemini_service.generate_product_response(
                        mensaje, 
                        product_info,
                        additional_context=additional_context,
                        conversation_history=historial
                    )
                    
                    # Guardar la interacción en Firestore
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"Guardada interacción en Firestore para {clean_phone}")
                    
                    # Intentar enviar respuesta
                    result = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
                    
                    # Verificar si hubo error de sandbox
                    if result.get("text", {}).get("status") == "error":
                        logger.error("Error al enviar respuesta de producto")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result["text"].get("message", "Error al enviar mensaje"),
                            "respuesta": respuesta
                        }
                    
                    return {
                        "success": True,
                        "message_type": "producto",
                        "producto": producto_detectado,
                        "fuente": product_info.get('fuente', 'farmacia'),
                        "tiene_imagen": bool(product_info.get("imagen")),
                        "respuesta": respuesta
                    }
                else:
                    logger.info(f"No se encontró información para {producto_detectado} en ninguna farmacia")
                    
                    # Generar respuesta con Gemini incluyendo el historial
                    respuesta = self.gemini_service.generate_response(
                        f"No encontré información específica sobre {producto_detectado} en ninguna de nuestras farmacias asociadas. {mensaje}",
                        conversation_history=historial
                    )
                    
                    # Guardar la interacción en Firestore
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"Guardada interacción en Firestore para {clean_phone}")
                    
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    # Verificar si hubo error de sandbox
                    if result.get("status") == "error":
                        logger.error("Error al enviar respuesta de producto no encontrado")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result.get("message", "Error al enviar mensaje"),
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
                logger.error(traceback.format_exc())
                # En caso de error, caer en respuesta general
        
        # 4) En cualquier otro caso, respuesta general
        logger.info("Generando respuesta general con Gemini")
        
        # NUEVO: Verificar si el mensaje incluía una imagen procesada con OCR
        contexto_imagen = ""
        if texto_extraido and media_urls and not texto_extraido.startswith("No se pudo"):
            contexto_imagen = f"El usuario envió una imagen que contiene el siguiente texto: {texto_extraido}"
            logger.info("Añadiendo contexto de imagen procesada")
        
        # Generar respuesta con Gemini incluyendo el historial y contexto de imagen
        mensaje_para_gemini = mensaje
        if contexto_imagen:
            mensaje_para_gemini = f"{mensaje}\n\n[CONTEXTO: {contexto_imagen}]"
            
        respuesta = self.gemini_service.generate_response(
            mensaje_para_gemini,
            conversation_history=historial
        )
        
        # Guardar la interacción en Firestore
        guardar_interaccion(clean_phone, mensaje, respuesta)
        logger.info(f"Guardada interacción en Firestore para {clean_phone}")
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        
        # Verificar si hubo error de sandbox
        if result.get("status") == "error":
            logger.error("Error al enviar respuesta general")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": result.get("message", "Error al enviar mensaje"),
                "respuesta": respuesta
            }
        
        return {
            "success": True,
            "message_type": "general",
            "respuesta": respuesta
        }
