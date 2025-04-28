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
    
    def es_mensaje_a_ignorar(self, mensaje):
        """
        Determina si un mensaje debe ser ignorado por no estar relacionado con farmacia.
        Usa un enfoque más estricto que ignora mensajes personales y no relacionados.
        
        Args:
            mensaje (str): Mensaje a analizar
            
        Returns:
            bool: True si el mensaje debe ignorarse, False si debe procesarse
        """
        mensaje_lower = mensaje.lower().strip()
        
        # Si el mensaje es muy corto (1-3 caracteres), ignorarlo
        if len(mensaje_lower) <= 3:
            logger.info(f"Mensaje ignorado por ser demasiado corto: {mensaje_lower}")
            return True
        
        # Lista de palabras clave relacionadas con farmacia/medicamentos
        palabras_relevantes = [
            "farmacia", "medicamento", "medicina", "pastilla", "remedio", 
            "tableta", "jarabe", "inyección", "precio", "dosis", "receta",
            "tienen", "venden", "hay", "disponible", "horario", "abren",
            "cierran", "envío", "domicilio", "entrega", "mg", "ml", "doctor",
            "médico", "síntoma", "dolor", "fiebre", "presión", "genérico",
            "marca", "laboratorio", "cápsula", "ampolla", "ungüento", "crema", 
            "pomada", "gel", "parche", "consulta", "salud"
        ]
        
        # Verificar si el mensaje contiene al menos una palabra relevante
        tiene_palabra_relevante = any(palabra in mensaje_lower for palabra in palabras_relevantes)
        
        # Si no tiene palabras relevantes, probablemente debamos ignorarlo
        if not tiene_palabra_relevante:
            # Patrones de mensajes personales o no relacionados con farmacia
            patrones_no_relevantes = [
                r"(?:hola|buenos días|buenas tardes|buenas noches).*(?:nos vemos|quedamos|vernos|hablamos|te llamo)",
                r"(?:a qué hora|cuando|dónde|donde|cómo|como).*(?:nos vemos|quedamos|vernos|llego|llegas)",
                r"(?:qué|que).*(?:haces|estás haciendo|planes|te parece)",
                r"(?:vamos|iremos|me acompañas|te acompaño|salimos)",
                r"(?:te extraño|te quiero|te amo|me gustas)",
                r"oye+", "amigo", "amiga", "carnal", "compadre", "hermano",
                r"(?:fiesta|película|cine|restaurante|bar|café|plaza|concierto)",
                r"(?:cita|vernos|salir)",
                r"(?:ya llegaste|ya estoy|estoy en|llego en)",
                r"(?:te llamé|te marqué|no contestas|contesta)"
            ]
            
            # Verificar si el mensaje coincide con algún patrón no relevante
            for patron in patrones_no_relevantes:
                if re.search(patron, mensaje_lower):
                    logger.info(f"Mensaje ignorado por coincidir con patrón no relevante: {patron}")
                    return True
            
            # Lista de saludos básicos que no tienen contexto adicional relevante
            saludos_simples = [
                "hola", "hey", "hi", "hello", "qué tal", "que tal", "cómo estás", "como estas",
                "buenas", "buenos días", "buenas tardes", "buenas noches", 
                "qué haces", "que haces", "qué cuentas", "que cuentas"
            ]
            
            # Si el mensaje solo contiene un saludo simple, ignorarlo
            for saludo in saludos_simples:
                # Verificar si el mensaje es exactamente el saludo o el saludo con signos de puntuación
                if re.match(f"^{saludo}[\\s,.!?]*$", mensaje_lower):
                    logger.info(f"Mensaje ignorado por ser un saludo simple: {mensaje_lower}")
                    return True
            
            # Si llegamos hasta aquí y no hay palabras relevantes, es probable que sea un mensaje no relacionado
            logger.info(f"Mensaje ignorado por no contener palabras relevantes a farmacia: {mensaje_lower}")
            return True
            
        # Si tiene palabras relevantes, procesarlo
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
        
        # Patrones para detectar consultas sobre productos
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
        
        # Detectar si es una consulta sobre medicamento/farmacia que no pide producto específico
        palabras_farmacia = ["medicamento", "farmacia", "medicina", "droga", "pastilla", "remedio", "medicinas", "medicamentos"]
        for palabra in palabras_farmacia:
            if palabra in mensaje_lower:
                return "consulta_general", None
        
        # Por defecto, considerar como consulta general
        return "consulta_general", None
    
    async def procesar_mensaje(self, mensaje, phone_number):
        """
        Procesa un mensaje entrante y genera una respuesta.
        
        Args:
            mensaje (str): Mensaje entrante del usuario
            phone_number (str): Número de teléfono del remitente
            
        Returns:
            dict: Resultado de la operación
        """
        logger.info(f"Procesando mensaje: '{mensaje}' de {phone_number}")
        
        # Verificar si el mensaje debe ser ignorado
        if self.es_mensaje_a_ignorar(mensaje):
            logger.info(f"Mensaje ignorado: '{mensaje}'")
            return {
                "success": True,
                "message_type": "ignorado",
                "respuesta": None  # No hay respuesta
            }
        
        # Detectar el tipo de mensaje
        tipo_mensaje, producto_detectado = self.detectar_tipo_mensaje(mensaje)
        logger.info(f"Tipo de mensaje detectado: {tipo_mensaje}")
        
        # Procesar según el tipo de mensaje
        if tipo_mensaje == "consulta_producto" and producto_detectado:
            logger.info(f"Buscando información sobre el producto: {producto_detectado}")
            
            # Buscar información del producto mediante scraping
            product_info = self.scraping_service.buscar_producto(producto_detectado)
            
            if product_info:
                logger.info(f"Información encontrada para {producto_detectado}")
                # Generar respuesta con la información del producto
                respuesta = self.gemini_service.generate_product_response(mensaje, product_info)
                
                # Enviar respuesta por WhatsApp
                resultado = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
                logger.info("Respuesta con información de producto enviada")
                return {
                    "success": True,
                    "message_type": "producto",
                    "producto": producto_detectado,
                    "tiene_imagen": product_info.get("imagen") is not None,
                    "respuesta": respuesta
                }
            else:
                logger.info(f"No se encontró información específica para {producto_detectado}")
                # Generar respuesta genérica si no se encuentra información
                respuesta = self.gemini_service.generate_response(
                    f"Un cliente pregunta sobre {producto_detectado}, pero no tengo información específica. "
                    f"El mensaje original es: {mensaje}"
                )
                
                # Enviar respuesta por WhatsApp
                resultado = self.whatsapp_service.send_text_message(phone_number, respuesta)
                logger.info("Respuesta genérica enviada (producto no encontrado)")
                return {
                    "success": True,
                    "message_type": "producto_no_encontrado",
                    "producto": producto_detectado,
                    "respuesta": respuesta
                }
        else:
            # Para cualquier otro tipo de mensaje, generar respuesta general con Gemini
            logger.info("Generando respuesta general con Gemini")
            respuesta = self.gemini_service.generate_response(mensaje)
            
            # Enviar respuesta por WhatsApp
            resultado = self.whatsapp_service.send_text_message(phone_number, respuesta)
            logger.info("Respuesta general enviada")
            return {
                "success": True,
                "message_type": "general",
                "respuesta": respuesta
            }
    
    def extract_product_from_message(self, mensaje):
        """
        Extrae el nombre del producto de un mensaje.
        Útil para análisis o para expansiones futuras.
        
        Args:
            mensaje (str): Mensaje a analizar
            
        Returns:
            str: Nombre del producto detectado o None
        """
        _, producto = self.detectar_tipo_mensaje(mensaje)
        return producto
    
    async def simular_respuesta(self, mensaje, phone_number):
        """
        Simula el procesamiento de un mensaje para pruebas.
        No realiza scraping real, solo genera una respuesta de Gemini.
        
        Args:
            mensaje (str): Mensaje entrante simulado
            phone_number (str): Número de teléfono del destinatario
            
        Returns:
            dict: Resultado de la operación
        """
        logger.info(f"Simulando respuesta para: '{mensaje}' a {phone_number}")
        
        # Verificar si el mensaje debe ser ignorado
        if self.es_mensaje_a_ignorar(mensaje):
            logger.info(f"Mensaje ignorado: '{mensaje}'")
            return {
                "success": True,
                "message_type": "ignorado",
                "respuesta": None  # No hay respuesta
            }
        
        # Detectar si es una consulta de producto
        tipo_mensaje, producto_detectado = self.detectar_tipo_mensaje(mensaje)
        
        if tipo_mensaje == "consulta_producto" and producto_detectado:
            # Simulación de respuesta para producto
            respuesta = self.gemini_service.generate_response(
                f"Un cliente pregunta sobre {producto_detectado}. "
                f"El mensaje original es: {mensaje}"
            )
        else:
            # Respuesta general
            respuesta = self.gemini_service.generate_response(mensaje)
        
        # Enviar respuesta por WhatsApp
        resultado = self.whatsapp_service.send_text_message(phone_number, respuesta)
        
        return {
            "success": True,
            "message_type": tipo_mensaje,
            "producto": producto_detectado,
            "respuesta": respuesta,
            "resultado_whatsapp": resultado
        }