"""
Servicio para interactuar con la API de Gemini.
Encapsula toda la lógica relacionada con la generación de respuestas de IA.
Actualizado para manejar información de la fuente del producto e historial de conversación.
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
    
    def _format_conversation_history(self, history):
        """
        Formatea el historial de conversación para incluirlo en el prompt.
        
        Args:
            history (list): Lista de diccionarios con roles y contenido
            
        Returns:
            str: Historial formateado
        """
        if not history:
            return ""
        
        formatted_history = ""
        for turn in history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role and content:
                formatted_history += f"{role}: {content} "
        
        return formatted_history.strip()
    
    def generate_response(self, user_message, conversation_history=None):
        """
        Genera una respuesta basada en el mensaje del usuario utilizando Gemini.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            conversation_history (list, optional): Historial de conversación
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            # Formatear el historial de conversación si está disponible
            context = ""
            if conversation_history:
                context = self._format_conversation_history(conversation_history)
                logger.info(f"Incluyendo historial de conversación ({len(conversation_history)} turnos)")
                
                # Añadir el mensaje actual al contexto
                final_message = f"{context} user: {user_message}"
            else:
                final_message = user_message
            
            prompt = f"{GEMINI_SYSTEM_INSTRUCTIONS}\n\nContexto de conversación: {context}\n\nMensaje del cliente: {user_message}"
            logger.info(f"Enviando prompt a Gemini para respuesta general. Mensaje: '{user_message[:50]}...'")
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"Respuesta recibida de Gemini ({len(response_text)} caracteres)")
            logger.debug(f"Respuesta: {response_text[:100]}...")
            
            return response_text
        except Exception as e:
            logger.error(f"Error en generate_response: {e}")
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"
    
    def generate_product_response(self, user_message, product_info, additional_context="", conversation_history=None):
        """
        Genera una respuesta basada en el mensaje del usuario y la información del producto.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            product_info (dict): Información del producto obtenida mediante scraping
            additional_context (str): Contexto adicional opcional
            conversation_history (list, optional): Historial de conversación
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            # Formatear el historial de conversación si está disponible
            context = ""
            if conversation_history:
                context = self._format_conversation_history(conversation_history)
                logger.info(f"Incluyendo historial de conversación ({len(conversation_history)} turnos)")
            
            # Formatear la información del producto
            if product_info:
                # Conversión de nombre de fuente a código interno
                fuente_mapping = {
                    "Sufarmed": "SF",
                    "Difarmer": "DF", 
                    "Fanasa": "FN",
                    "Nadro": "ND"
                }
                
                fuente_original = product_info.get('fuente', '')
                codigo_fuente = fuente_mapping.get(fuente_original, fuente_original.upper()[:2] if fuente_original else '')
                
                # Calcular precio con margen del 45%
                precio_original = product_info.get('precio', 'No disponible')
                precio_mostrar = "No disponible"
                
                if precio_original != 'No disponible':
                    try:
                        # Eliminar símbolos de moneda y convertir a float
                        precio_limpio = precio_original.replace('$', '').replace(',', '').strip()
                        precio_float = float(precio_limpio)
                        
                        # Aplicar margen del 45%
                        precio_con_margen = precio_float * 1.45
                        
                        # Formatear de vuelta a string con formato de moneda
                        precio_mostrar = f"${precio_con_margen:.2f}"
                    except ValueError:
                        logger.warning(f"No se pudo convertir el precio: {precio_original}")
                        precio_mostrar = precio_original
                
                # Determinar mensaje de entrega según el código de fuente
                if codigo_fuente == "SF":
                    mensaje_entrega = "La entrega sería el mismo día, siempre validando disponibilidad."
                else:
                    mensaje_entrega = "La entrega sería al día siguiente, sujeto a disponibilidad."
                
                # Información formateada del producto
                product_details = f"""
Información del producto:
- Nombre: {product_info.get('nombre', 'No disponible')}
- Laboratorio: {product_info.get('laboratorio', 'No disponible')}
- Código de barras: {product_info.get('codigo_barras', 'No disponible')}
- Registro sanitario: {product_info.get('registro_sanitario', 'No disponible')}
- URL del producto: {product_info.get('url', 'No disponible')}
- Precio: {precio_mostrar}
- Existencia: {product_info.get('existencia', 'No disponible')}
- Código fuente: {codigo_fuente}
- Información de entrega: {mensaje_entrega}
"""
            else:
                product_details = "No se encontró información específica sobre este producto en nuestra base de datos."
                precio_mostrar = "No disponible"
                codigo_fuente = ""
                mensaje_entrega = ""
            
            # Crear el prompt completo
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Contexto de conversación previa: {context}
Mensaje del cliente: {user_message}
{product_details}
{additional_context}
IMPORTANTE: Genera una respuesta EXTREMADAMENTE BREVE Y DIRECTA siguiendo estas reglas:
1. NO menciones el nombre del producto en tu respuesta
2. Informa SOLO el precio total
3. Indica claramente el tiempo de entrega (mismo día o día siguiente)
4. Sugiere contacto directo para confirmar stock o programar entrega
5. Si es necesario mencionar la fuente, colócala AL FINAL entre paréntesis como: (Origen: XX)

FORMATO OBLIGATORIO:
"El precio total sería de [PRECIO]. [INFO ENTREGA]. Para confirmar stock o programar la entrega, por favor contáctanos directamente. (Origen: [CÓDIGO])"

Tu respuesta debe tener MÁXIMO 3 FRASES, ser concisa y directa.
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
