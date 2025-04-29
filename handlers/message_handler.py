"""
Manejador de mensajes para SOPRIM BOT.
Orquesta la interacción entre los diferentes servicios.
"""
import logging
import re
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService
from config.settings import ALLOWED_TEST_NUMBERS

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
        logger.info("MessageHandler inicializado correctamente")
        logger.info(f"Números permitidos para pruebas: {ALLOWED_TEST_NUMBERS}")
    
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
        
        # Palabras clave que podrían indicar que se está hablando de un medicamento
        palabras_medicamento = ["paracetamol", "ibuprofeno", "aspirina", "omeprazol", "loratadina", "antibiotico"]
        for palabra in palabras_medicamento:
            if palabra in mensaje_lower:
                logger.info
