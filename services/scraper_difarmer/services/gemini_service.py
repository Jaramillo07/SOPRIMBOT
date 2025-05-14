"""
Servicio para interactuar con la API de Gemini.
Encapsula toda la lógica relacionada con la generación de respuestas de IA.
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
    
    def detectar_mensaje_ignorable(self, user_message):
        """
        Usa Gemini para determinar si un mensaje debe ser ignorado por ser charla casual,
        expresión coloquial, o mensaje no relacionado con farmacia o medicamentos.
        
        Args:
            user_message (str): Mensaje del usuario para analizar
            
        Returns:
            bool: True si el mensaje debe ignorarse, False si debe procesarse
        """
        prompt = f"""Eres un asistente de farmacia que debe determinar si un mensaje debe ser ignorado o procesado.
    
INSTRUCCIONES PRECISAS:
Analiza el siguiente mensaje y determina si es:
1) Un saludo casual (como "hola", "qué tal", "buenos días")
2) Una expresión coloquial o de ocio (como "vamos por cheves", "a qué hora la fiesta", "nos vemos al rato")
3) Una invitación o comentario social (como "quedamos mañana", "qué planes tienes")
4) Un mensaje no relacionado con farmacia, medicamentos o salud

Si el mensaje cae en CUALQUIERA de estas categorías, responde EXACTAMENTE con la palabra "IGNORAR".
Si el mensaje parece ser una consulta sobre productos de farmacia, medicamentos, o temas de salud, responde EXACTAMENTE con la palabra "PROCESAR".

Ejemplos:
- "Hola qué tal" → "IGNORAR"
- "Vamos x cheves" → "IGNORAR"
- "A qué hora te veo" → "IGNORAR"
- "Tienes paracetamol" → "PROCESAR"
- "Cuánto cuesta el omeprazol" → "PROCESAR"
- "Me duele la cabeza, qué me recomiendas" → "PROCESAR"

Mensaje a analizar: "{user_message}"
"""
        try:
            logger.info(f"Enviando mensaje a Gemini para determinar si es ignorable: '{user_message}'")
            response = self.model.generate_content(prompt)
            result = response.text.strip().upper()
            
            logger.info(f"Respuesta de Gemini para detección de mensaje ignorable: '{result}'")
            
            # Si Gemini dice IGNORAR, devolvemos True
            if "IGNORAR" in result:
                logger.info(f"Gemini determina que el mensaje debe ser ignorado: '{user_message}'")
                return True
            else:
                logger.info(f"Gemini determina que el mensaje debe ser procesado: '{user_message}'")
                return False
        except Exception as e:
            logger.error(f"Error en detectar_mensaje_ignorable: {e}")
            # En caso de error, devolvemos False para procesar el mensaje de todas formas
            return False
    
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
            # Formatear la información del producto
            if product_info:
                product_details = f"""
Información del producto encontrado:
- Nombre: {product_info.get('nombre', 'No disponible')}
- Laboratorio: {product_info.get('laboratorio', 'No disponible')}
- Código de barras: {product_info.get('codigo_barras', 'No disponible')}
- Registro sanitario: {product_info.get('registro_sanitario', 'No disponible')}
- URL del producto: {product_info.get('url', 'No disponible')}
- Precio: {product_info.get('precio', 'No disponible')}
- Stock: {product_info.get('stock', 'No especificado')}
- Disponibilidad: {'Disponible' if product_info.get('disponible', False) else 'No disponible'}
"""
            else:
                product_details = "No se encontró información específica sobre este producto en nuestra base de datos."
            
            # Crear el prompt completo
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Mensaje del cliente: {user_message}
{product_details}
Basándote en esta información, proporciona una respuesta útil y profesional al cliente sobre el producto solicitado.
Incluye siempre el precio en tu respuesta cuando esté disponible.
Si el campo "Disponibilidad" está marcado como "No disponible", indica que el producto está agotado.
Si el campo "Disponibilidad" está marcado como "Disponible", confirma al cliente que el producto está disponible.
Si el precio está disponible, menciónalo claramente al cliente e indícale que puede confirmar la disponibilidad llamando a la farmacia o visitando la tienda.
Si el precio no está disponible, indícale al cliente que puede consultar el precio y disponibilidad llamando a la farmacia o visitando la tienda.
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
        # Primero, tratar de extraer el nombre completo del producto directamente del mensaje
        # Buscar patrones comunes de medicamentos con presentación
        mensaje_lower = user_message.lower()
        
        # Intenta encontrar un patrón de medicamento completo antes de consultar a Gemini
        # Esta es una verificación más avanzada que busca patrones como "Nombre 500mg" o "Nombre Caps 20"
        import re
        
        # Patrones para detectar nombres completos de medicamentos
        patrones = [
            # Patrón: NombreMedicamento Forma Dosis Cantidad
            r'(\w+(?:\s+\w+)*)\s+(caps|cápsulas|tabletas|tabs|comprimidos|amp|ampolla|jarabe|solución|gel|crema|polvo|gotas)\s+(\d+(?:\.\d+)?(?:mg|ml|mcg|g|mg/ml))\s+(?:c\/|c\s|caja\s+(?:con|de)|frasco\s+(?:con|de)|blister\s+(?:con|de))?\s*(\d+)',
            
            # Patrón: NombreMedicamento Dosis
            r'(\w+(?:\s+\w+)*)\s+(\d+(?:\.\d+)?(?:mg|ml|mcg|g)\/\d+(?:\.\d+)?(?:mg|ml|mcg|g))',
            
            # Patrón: NombreMedicamento Dosis
            r'(\w+(?:\s+\w+)*)\s+(\d+(?:\.\d+)?(?:mg|ml|mcg|g))'
        ]
        
        # Extraer medicamento completo con mejor patrón
        medicamento_completo = None
        for patron in patrones:
            matches = re.search(patron, mensaje_lower)
            if matches:
                grupos = matches.groups()
                if len(grupos) >= 2:  # Al menos nombre y alguna especificación
                    # Reconstruir el nombre completo del medicamento
                    medicamento_completo = mensaje_lower[matches.start():matches.end()]
                    logger.info(f"Medicamento completo detectado por patrón regex: '{medicamento_completo}'")
                    break
        
        # Si se encontró un patrón claro, usarlo directamente
        if medicamento_completo:
            return "consulta_producto", medicamento_completo
        
        # Si no se detectó con regex, usar Gemini para análisis más avanzado
        prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Determina SI el siguiente mensaje está preguntando por un medicamento específico.
- Si SÍ, responde EXACTAMENTE con el nombre completo del medicamento TAL COMO APARECE en el mensaje, incluyendo la presentación completa (dosis, cantidad, etc). No simplificar a solo el principio activo.
- Ejemplos correctos:
  * Mensaje: "¿Tienen Ampicilina Caps 500mg C/20?" → Respuesta: "Ampicilina Caps 500mg C/20"
  * Mensaje: "Busco Augmentin 600mg/42.9mg polvo" → Respuesta: "Augmentin 600mg/42.9mg polvo"
  * Mensaje: "Necesito Tafil 2mg tabletas" → Respuesta: "Tafil 2mg tabletas"
- Si NO hay un medicamento específico mencionado, responde exactamente con la palabra GENERAL.
Mensaje: "{user_message}"
"""
        try:
            logger.info(f"Enviando prompt a Gemini para detectar producto. Mensaje: '{user_message}'")
            
            # Eliminamos la detección local simple para evitar que interrumpa el flujo principal
            # y así siempre usar Gemini con los mensajes que tienen formatos complejos
            
            # Si no se detectó localmente, consultar a Gemini
            response = self.model.generate_content(prompt)
            resp = response.text.strip()
            
            logger.info(f"Respuesta de Gemini para detección de producto: '{resp}'")
            
            # Procesar la respuesta
            if resp.upper() == "GENERAL":
                logger.info("Detectado como consulta general")
                return "consulta_general", None
            else:
                # Usar la respuesta completa para mantener toda la información del medicamento
                producto = resp.strip()
                logger.info(f"Detectado como consulta de producto: '{producto}'")
                return "consulta_producto", producto
        except Exception as e:
            logger.error(f"Error en detectar_producto: {e}")
            # En caso de error, usar detección local básica (palabras clave) como respaldo
            # Este código solo se ejecutará si Gemini falla
            if "tienes" in mensaje_lower or "tienen" in mensaje_lower or "hay" in mensaje_lower:
                # Intentar extraer frases más largas en lugar de palabras sueltas
                palabras = mensaje_lower.split()
                for i in range(len(palabras)-1, 0, -1):  # Empezar con frases más largas
                    frase = " ".join(palabras[:i+1])
                    if any(med in frase for med in ["ampicilina", "paracetamol", "ibuprofeno"]):
                        logger.info(f"Respaldo: Producto detectado por frase: {frase}")
                        return "consulta_producto", frase
                        
                # Si no se encuentra por frase, buscar palabras individuales como último recurso
                for palabra in palabras:
                    if len(palabra) > 4 and palabra not in ["tienes", "tienen", "ustedes", "algún", "alguna", "donde", "cuánto", "cuanto", "información", "info", "este", "esta", "sobre"]:
                        logger.info(f"Respaldo: Producto detectado por palabra: {palabra}")
                        return "consulta_producto", palabra
            
            logger.info("Respaldo: Consulta general")
            return "consulta_general", None
