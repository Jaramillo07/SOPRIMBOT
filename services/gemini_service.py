"""
Servicio para interactuar con la API de Gemini.
Encapsula toda la lógica relacionada con la generación de respuestas de IA.
Actualizado para manejar información de la fuente del producto e historial de conversación.
"""
import logging
import re
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
    
    def _es_consulta_descuento(self, user_message):
        """
        Determina si el mensaje del usuario está relacionado con descuentos o promociones.
        
        Args:
            user_message (str): Mensaje del usuario
            
        Returns:
            bool: True si es una consulta de descuento, False si no
        """
        mensaje_lower = user_message.lower()
        
        # Palabras clave relacionadas con descuentos y promociones
        palabras_descuento = [
            'descuento', 'rebaja', 'promoción', 'promocion', 'oferta', 'más barato', 'mas barato',
            'mejor precio', 'precio especial', 'precio por volumen', 'mayoreo', 'por mayor',
            'varias cajas', 'comprar más', 'comprar mas', 'descuentos', 'rebajas', 'ofertas',
            'promociones', 'rebajado', 'económico', 'economico', 'ahorrar', 'ahorro'
        ]
        
        # Verificar si alguna palabra clave está en el mensaje
        for palabra in palabras_descuento:
            if palabra in mensaje_lower:
                return True
                
        # Patrones comunes de preguntas sobre descuentos
        patrones_descuento = [
            r'(?:hay|tienen|manejan|aplican?)\s+(?:algún|algun|alguna)?\s*(?:descuento|rebaja|promoción|promocion|oferta)',
            r'(?:cuánto|cuanto)\s+(?:si|por)\s+(?:compro|llevo)\s+(?:varias|más|mas|muchas)',
            r'(?:precio)\s+(?:por|de)\s+(?:mayoreo|volumen|cantidad)',
            r'(?:más|mas)\s+(?:barato|económico|economico)',
            r'(?:puedes?|podrías?|podrias?)\s+(?:mejorar|bajar|reducir)\s+(?:el|ese)?\s*precio'
        ]
        
        # Verificar si algún patrón coincide con el mensaje
        for patron in patrones_descuento:
            if re.search(patron, mensaje_lower):
                return True
                
        return False
    
    def _es_consulta_entrega_hoy(self, user_message):
        """
        Determina si el mensaje del usuario hace referencia a la entrega o disponibilidad inmediata (hoy).
        
        Args:
            user_message (str): Mensaje del usuario
            
        Returns:
            bool: True si es una consulta de entrega para hoy, False si no
        """
        mensaje_lower = user_message.lower()
        
        # Patrones para detectar consultas de entrega para hoy
        patrones_entrega_hoy = [
            r'entregan?\s+hoy',
            r'entrega\s+(?:para|de)?\s*hoy',
            r'disponibilidad\s+(?:para|de)?\s*hoy',
            r'recib(?:o|ir)\s+hoy',
            r'(?:nada|algo)\s+para\s+(?:el\s+)?(?:día\s+)?(?:de\s+)?hoy',
            r'tienen\s+(?:algo|nada)\s+(?:para|de)\s+hoy',
            r'puedo\s+recibir\s+hoy',
            r'para\s+(?:el\s+)?día\s+de\s+hoy',
            r'(?:hoy\s+(?:mismo|ya))',
            r'(?:ya|ahorita|inmediata(?:mente)?)\s+(?:mismo)?'
        ]
        
        # Verificar si algún patrón coincide con el mensaje
        for patron in patrones_entrega_hoy:
            if re.search(patron, mensaje_lower):
                logger.info(f"Detectada consulta de entrega para HOY con patrón: {patron}")
                return True
                
        return False
        
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
            # Verificar si es una consulta sobre entrega para hoy
            if self._es_consulta_entrega_hoy(user_message):
                logger.info("Detectada consulta sobre entrega para HOY - respuesta directa sin consultar a Gemini")
                return "La entrega normalmente se realiza al día siguiente, sujeta a disponibilidad. Para confirmar stock o programar la entrega, por favor contáctanos directamente. (Origen: DF)"
            
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
            # Verificar si es una consulta sobre entrega para hoy
            if self._es_consulta_entrega_hoy(user_message):
                logger.info("Detectada consulta sobre entrega para HOY - respuesta directa sin consultar a Gemini")
                return "La entrega normalmente se realiza al día siguiente, sujeta a disponibilidad. Para confirmar stock o programar la entrega, por favor contáctanos directamente. (Origen: DF)"
            
            # Verificar si es una consulta sobre descuentos o promociones
            if self._es_consulta_descuento(user_message):
                logger.info("Detectada consulta sobre descuentos o promociones")
                
                # Lista de respuestas posibles para consultas de descuentos
                respuestas_descuento = [
                    "Podemos ofrecer descuentos por volumen. Por favor, comunícate directamente para más detalles.",
                    "Los descuentos pueden aplicar dependiendo del producto o la cantidad. Llámanos para confirmarlo.",
                    "Sí manejamos promociones en algunas presentaciones. Contáctanos y te damos la información completa.",
                    "Contamos con descuentos especiales dependiendo del producto y cantidad. Comunícate directamente con nosotros para conocer las opciones disponibles.",
                    "Para información sobre descuentos y promociones, te invitamos a contactarnos directamente por teléfono o mensaje."
                ]
                
                # Seleccionar una respuesta basada en un hash simple del mensaje del usuario
                indice = hash(user_message) % len(respuestas_descuento)
                response_text = respuestas_descuento[indice]
                
                logger.info(f"Respuesta de descuento seleccionada: '{response_text}'")
                return response_text
            
            # Si no es consulta de descuento, proceder con la respuesta normal de producto
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
                
                # Detectar cantidad en el mensaje del usuario
                cantidad = 1  # Valor por defecto
                cantidad_match = re.search(r'(\d+)\s*(unidades|piezas|cajas|tabletas|paquetes|frascos|ampolletas|unidad|pieza|caja|tableta|paquete|frasco|ampolleta)?', user_message.lower())
                if cantidad_match:
                    cantidad = int(cantidad_match.group(1))
                    logger.info(f"Cantidad detectada en el mensaje: {cantidad}")
                
                # Calcular precio con margen del 45%
                precio_original = product_info.get('precio', 'No disponible')
                precio_unitario = "No disponible"
                precio_total = "No disponible"
                
                if precio_original != 'No disponible':
                    try:
                        # Eliminar símbolos de moneda y convertir a float
                        precio_limpio = precio_original.replace('$', '').replace(',', '').strip()
                        precio_float = float(precio_limpio)
                        
                        # Aplicar margen del 45%
                        precio_con_margen = precio_float * 1.45
                        
                        # Calcular precio total basado en la cantidad
                        precio_total_float = precio_con_margen * cantidad
                        
                        # Formatear de vuelta a string con formato de moneda
                        precio_unitario = f"${precio_con_margen:.2f}"
                        precio_total = f"${precio_total_float:.2f}"
                        
                        logger.info(f"Precio unitario con margen: {precio_unitario}, Cantidad: {cantidad}, Precio total: {precio_total}")
                    except ValueError:
                        logger.warning(f"No se pudo convertir el precio: {precio_original}")
                        precio_unitario = precio_original
                        precio_total = precio_original
                
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
- Precio unitario: {precio_unitario}
- Precio total (cantidad: {cantidad}): {precio_total}
- Existencia: {product_info.get('existencia', 'No disponible')}
- Código fuente: {codigo_fuente}
- Información de entrega: {mensaje_entrega}
"""
            else:
                product_details = "No se encontró información específica sobre este producto en nuestra base de datos."
                precio_total = "No disponible"
                codigo_fuente = ""
                mensaje_entrega = ""
                cantidad = 1
            
            # Crear el prompt completo para respuestas informativas (precio y entrega)
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Contexto de conversación previa: {context}
Mensaje del cliente: {user_message}
{product_details}
{additional_context}
IMPORTANTE: Genera una respuesta EXTREMADAMENTE BREVE Y DIRECTA siguiendo el formato exacto:
"El precio total sería de {precio_total}. La entrega normalmente se realiza {mensaje_entrega.lower().replace("La entrega sería ", "")} Para confirmar stock o programar la entrega, por favor contáctanos directamente. (Origen: {codigo_fuente})"

REGLAS IMPORTANTES:
1. NO menciones el nombre del producto en tu respuesta
2. SOLO incluye el precio total (ya calculado con la cantidad)
3. SIGUE EXACTAMENTE el formato solicitado
4. La respuesta debe ser concisa y directa
5. La parte "(Origen: XX)" solo debe usarse como referencia interna al final de la respuesta
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
