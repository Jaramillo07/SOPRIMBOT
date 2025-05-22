"""
Servicio para interactuar con la API de Gemini.
VERSIÓN: GEMINI GESTIONA CONTEXTOS COMPLETOS
Gemini entiende y maneja todo el contexto de la conversación inteligentemente.
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
    GEMINI gestiona contextos completos.
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
                if role == "user":
                    formatted_history += f"Usuario: {content}\n"
                elif role == "assistant":
                    formatted_history += f"Bot: {content}\n"
        
        return formatted_history.strip()
    
    def _es_consulta_descuento(self, user_message):
        """
        Determina si el mensaje del usuario está relacionado con descuentos o promociones.
        MANTIENE REGEX para consultas simples de descuento.
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
                
        return False
    
    def _es_consulta_entrega_hoy(self, user_message):
        """
        Determina si el mensaje del usuario hace referencia a la entrega inmediata.
        MANTIENE REGEX para consultas simples de entrega.
        """
        mensaje_lower = user_message.lower()
        
        # Patrones para detectar consultas de entrega para hoy
        patrones_entrega_hoy = [
            r'entregan?\s+hoy',
            r'entrega\s+(?:para|de)?\s*hoy',
            r'disponibilidad\s+(?:para|de)?\s*hoy',
            r'recib(?:o|ir)\s+hoy',
            r'(?:hoy\s+(?:mismo|ya))',
            r'(?:ya|ahorita|inmediata(?:mente)?)'
        ]
        
        # Verificar si algún patrón coincide con el mensaje
        for patron in patrones_entrega_hoy:
            if re.search(patron, mensaje_lower):
                logger.info(f"Detectada consulta de entrega para HOY con patrón: {patron}")
                return True
                
        return False
    
    def analizar_contexto_con_gemini(self, user_message, conversation_history):
        """
        ✅ PÚBLICO: Usa Gemini para analizar el contexto completo de la conversación.
        Determina si es consulta de cantidad y extrae el producto del contexto.
        
        Args:
            user_message (str): Mensaje actual del usuario
            conversation_history (list): Historial de conversación
            
        Returns:
            dict: {
                "es_cantidad": bool,
                "cantidad": int or None,
                "producto_contexto": str or None,
                "tipo_consulta": str
            }
        """
        if not conversation_history:
            return {
                "es_cantidad": False,
                "cantidad": None,
                "producto_contexto": None,
                "tipo_consulta": "nueva_consulta"
            }
        
        # Formatear historial para Gemini
        historial_formateado = self._format_conversation_history(conversation_history)
        
        prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}

ANÁLISIS DE CONTEXTO:
Analiza el siguiente historial de conversación y el mensaje actual del usuario.

HISTORIAL PREVIO:
{historial_formateado}

MENSAJE ACTUAL DEL USUARIO: "{user_message}"

Tu tarea es determinar:
1. ¿Es este mensaje una indicación de CANTIDAD para un producto ya mencionado?
2. Si es cantidad, ¿cuántas unidades quiere?
3. ¿Cuál es el producto del contexto anterior?

RESPONDE EXACTAMENTE en este formato JSON:
{{
    "es_cantidad": true/false,
    "cantidad": número_entero_o_null,
    "producto_contexto": "nombre_del_producto_o_null",
    "tipo_consulta": "cantidad" o "producto_nuevo" o "general"
}}

EJEMPLOS:
- Si dice "quiero 5 unidades" después de preguntar por paracetamol → {{"es_cantidad": true, "cantidad": 5, "producto_contexto": "paracetamol", "tipo_consulta": "cantidad"}}
- Si dice "tienes ibuprofeno?" → {{"es_cantidad": false, "cantidad": null, "producto_contexto": null, "tipo_consulta": "producto_nuevo"}}
- Si dice "hola" → {{"es_cantidad": false, "cantidad": null, "producto_contexto": null, "tipo_consulta": "general"}}
"""

        try:
            logger.info(f"Analizando contexto con Gemini para: '{user_message}'")
            response = self.model.generate_content(prompt)
            resp_text = response.text.strip()
            
            # Extraer JSON de la respuesta
            import json
            import re
            
            # Buscar el JSON en la respuesta
            json_match = re.search(r'\{.*\}', resp_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                resultado = json.loads(json_str)
                
                logger.info(f"Análisis de contexto: {resultado}")
                return resultado
            else:
                logger.warning(f"No se pudo extraer JSON de la respuesta: {resp_text}")
                return {
                    "es_cantidad": False,
                    "cantidad": None,
                    "producto_contexto": None,
                    "tipo_consulta": "general"
                }
                
        except Exception as e:
            logger.error(f"Error en análisis de contexto con Gemini: {e}")
            return {
                "es_cantidad": False,
                "cantidad": None,
                "producto_contexto": None,
                "tipo_consulta": "general"
            }
    
    def _detectar_producto_con_gemini(self, user_message):
        """
        Usa Gemini para determinar si el mensaje pregunta por un producto específico.
        """
        prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}
Determina SI el siguiente mensaje está preguntando por un producto específico.
- Si SÍ, responde SOLO con el nombre del producto (p. ej. "paracetamol", "ibuprofeno").
- Si NO, responde exactamente con la palabra GENERAL.
Mensaje: "{user_message}"
"""
        try:
            response = self.model.generate_content(prompt)
            resp = response.text.strip()
            
            # Procesar la respuesta
            if resp.upper() == "GENERAL":
                return "consulta_general", None
            else:
                # Limpiar la respuesta para obtener solo el nombre del medicamento
                producto = resp.strip()
                return "consulta_producto", producto
        except Exception as e:
            logger.error(f"Error en _detectar_producto_con_gemini: {e}")
            return "consulta_general", None

    def generate_response(self, user_message, conversation_history=None):
        """
        Genera una respuesta basada en el mensaje del usuario utilizando Gemini.
        """
        try:
            # Verificar si es una consulta sobre entrega para hoy
            if self._es_consulta_entrega_hoy(user_message):
                logger.info("Detectada consulta sobre entrega para HOY - respuesta directa")
                return "La entrega normalmente se realiza al día siguiente, sujeta a disponibilidad. Para confirmar stock o programar la entrega, por favor contáctanos directamente. (Origen: DF)"
            
            # Formatear el historial de conversación si está disponible
            context = ""
            if conversation_history:
                context = self._format_conversation_history(conversation_history)
                logger.info(f"Incluyendo historial de conversación ({len(conversation_history)} turnos)")
            
            prompt = f"{GEMINI_SYSTEM_INSTRUCTIONS}\n\nContexto de conversación:\n{context}\n\nMensaje del cliente: {user_message}"
            logger.info(f"Enviando prompt a Gemini para respuesta general. Mensaje: '{user_message[:50]}...'")
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"Respuesta recibida de Gemini ({len(response_text)} caracteres)")
            
            return response_text
        except Exception as e:
            logger.error(f"Error en generate_response: {e}")
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"
    
    def generate_product_response(self, user_message, producto_info, additional_context="", conversation_history=None):
        """
        Genera una respuesta basada en el mensaje del usuario y las opciones de productos disponibles.
        ACTUALIZADO: Usa análisis de contexto con Gemini para determinar cantidad.
        """
        try:
            # Verificar si es una consulta sobre entregas
            es_consulta_entrega = self._es_consulta_entrega_hoy(user_message) or re.search(r'(?:para\s+cuándo|para\s+cuando|cuándo|cuando)\s+(?:sería|seria|es)\s+(?:la\s+)?entrega', user_message.lower())
                
            # Si es una consulta explícita sobre entregas, dar respuesta directa
            if es_consulta_entrega:
                logger.info("Detectada consulta sobre entrega - generando respuesta específica")
                
                # Si tiene opción de entrega inmediata (Sufarmed o Base Interna)
                if (producto_info.get("opcion_entrega_inmediata") and 
                    (producto_info["opcion_entrega_inmediata"].get("fuente") == "Sufarmed" or 
                     producto_info["opcion_entrega_inmediata"].get("fuente") == "Base Interna")):
                    return "La entrega se puede realizar hoy mismo. Para confirmar disponibilidad, por favor contáctanos directamente. (Origen: SF)"
                elif (producto_info.get("opcion_mejor_precio") and 
                    producto_info["opcion_mejor_precio"].get("fuente") == "Base Interna"):
                    return "La entrega se puede realizar hoy mismo. Para confirmar disponibilidad, por favor contáctanos directamente. (Origen: BI)"
                else:
                    return "La entrega normalmente se realiza al día siguiente, sujeta a disponibilidad. Para confirmar stock o programar la entrega, por favor contáctanos directamente. (Origen: DF)"
            
            # Verificar si es una consulta sobre descuentos o promociones
            if self._es_consulta_descuento(user_message):
                logger.info("Detectada consulta sobre descuentos o promociones")
                
                respuestas_descuento = [
                    "Podemos ofrecer descuentos por volumen. Por favor, comunícate directamente para más detalles.",
                    "Los descuentos pueden aplicar dependiendo del producto o la cantidad. Llámanos para confirmarlo.",
                    "Sí manejamos promociones en algunas presentaciones. Contáctanos y te damos la información completa.",
                    "Contamos con descuentos especiales dependiendo del producto y cantidad. Comunícate directamente con nosotros para conocer las opciones disponibles.",
                    "Para información sobre descuentos y promociones, te invitamos a contactarnos directamente por teléfono o mensaje."
                ]
                
                indice = hash(user_message) % len(respuestas_descuento)
                response_text = respuestas_descuento[indice]
                
                logger.info(f"Respuesta de descuento seleccionada: '{response_text}'")
                return response_text
            
            mensaje_final = "Para más información o confirmar tu pedido, responde este mensaje."
            
            # Verificar si hay opciones disponibles
            if not producto_info.get("opcion_entrega_inmediata") and not producto_info.get("opcion_mejor_precio"):
                logger.warning("No se encontraron opciones de producto disponibles")
                return f"Lo siento, no encontramos este producto disponible en nuestro inventario en este momento. {mensaje_final}"
            
            # ✅ USAR GEMINI PARA DETECTAR CANTIDAD EN CONTEXTO
            contexto_analisis = self.analizar_contexto_con_gemini(user_message, conversation_history)
            
            # Determinar cantidad basada en análisis de Gemini
            cantidad = 1  # Valor por defecto
            if contexto_analisis.get("es_cantidad") and contexto_analisis.get("cantidad"):
                cantidad = contexto_analisis["cantidad"]
                logger.info(f"Gemini detectó cantidad en contexto: {cantidad}")
            
            # Función para aplicar margen y formatear precio
            def aplicar_margen_precio(precio_str, fuente):
                """Aplica margen solo si NO es de la Base Interna"""
                try:
                    precio_limpio = precio_str.replace('$', '').replace(',', '').strip()
                    precio_float = float(precio_limpio)
                    
                    if fuente == "Base Interna":
                        return f"${precio_float:.2f}"
                    
                    precio_con_margen = precio_float * 1.45
                    return f"${precio_con_margen:.2f}"
                except (ValueError, AttributeError):
                    logger.warning(f"No se pudo convertir el precio: {precio_str}")
                    return precio_str
            
            logger.info(f"Cantidad final detectada: {cantidad}")
            
            # Conversión de nombre de fuente a código interno
            fuente_mapping = {
                "Sufarmed": "SF",
                "Difarmer": "DF", 
                "Fanasa": "FN",
                "Nadro": "ND",
                "FANASA": "FN",
                "NADRO": "ND",
                "Base Interna": "BI"
            }
            
            # Si hay doble opción (entrega inmediata y mejor precio son diferentes)
            if producto_info.get("tiene_doble_opcion", False):
                logger.info("Generando respuesta con doble opción")
                
                opcion_entrega_inmediata = producto_info["opcion_entrega_inmediata"]
                opcion_mejor_precio = producto_info["opcion_mejor_precio"]
                
                # Aplicar margen según corresponda
                precio_entrega_inmediata = aplicar_margen_precio(
                    opcion_entrega_inmediata['precio'], 
                    opcion_entrega_inmediata.get('fuente', '')
                )
                precio_mejor_precio = aplicar_margen_precio(
                    opcion_mejor_precio['precio'],
                    opcion_mejor_precio.get('fuente', '')
                )
                
                # Ajustar precio según la cantidad solicitada
                if cantidad > 1:
                    valor_entrega = float(precio_entrega_inmediata.replace('$', '').replace(',', ''))
                    valor_mejor = float(precio_mejor_precio.replace('$', '').replace(',', ''))
                    
                    total_entrega = valor_entrega * cantidad
                    total_mejor = valor_mejor * cantidad
                    
                    precio_entrega_inmediata = f"${total_entrega:.2f}"
                    precio_mejor_precio = f"${total_mejor:.2f}"
                
                fuente_entrega = fuente_mapping.get(opcion_entrega_inmediata.get('fuente', ''), 'XX')
                fuente_precio = fuente_mapping.get(opcion_mejor_precio.get('fuente', ''), 'XX')
                
                respuesta = f"📦 {cantidad} unidad(es) solicitada(s):\n"
                respuesta += f"🚚 Entrega hoy mismo por {precio_entrega_inmediata}\n"
                respuesta += f"💲 Mejor precio con entrega mañana por {precio_mejor_precio}\n"
                respuesta += f"{mensaje_final} (Origen: {fuente_entrega}/{fuente_precio})"
                
                return respuesta
            
            # Si solo hay una opción
            logger.info("Generando respuesta con una sola opción")
            
            producto = producto_info.get("opcion_entrega_inmediata") or producto_info.get("opcion_mejor_precio")
            
            precio_con_margen = aplicar_margen_precio(
                producto['precio'],
                producto.get('fuente', '')
            )
            
            # Ajustar precio según la cantidad solicitada
            if cantidad > 1:
                valor = float(precio_con_margen.replace('$', '').replace(',', ''))
                total = valor * cantidad
                precio_con_margen = f"${total:.2f}"
            
            # Formato especial para productos de Base Interna
            if producto.get("fuente") == "Base Interna":
                stock_disponible = producto.get('existencia', '0')
                try:
                    stock_num = int(float(stock_disponible))
                    if stock_num > 0:
                        stock_text = f"📦 Tenemos {stock_num} unidades disponibles"
                    else:
                        stock_text = "📦 Consultar disponibilidad"
                except:
                    stock_text = "📦 Consultar disponibilidad"
                
                respuesta = f"✅ {cantidad} unidad(es) solicitada(s)\n"
                respuesta += f"Precio total: {precio_con_margen}\n"
                respuesta += f"🚚 Entrega hoy mismo\n"
                respuesta += f"{stock_text}\n"
                respuesta += f"{mensaje_final} (Origen: BI)"
                
                return respuesta
            
            # Para productos externos
            es_entrega_inmediata = producto.get("fuente") == "Sufarmed"
            mensaje_entrega = "🚚 Entrega hoy mismo." if es_entrega_inmediata else "📦 Entrega mañana."
            
            codigo_fuente = fuente_mapping.get(producto.get('fuente', ''), 'XX')
            
            respuesta = f"✅ {cantidad} unidad(es) solicitada(s).\n"
            respuesta += f"Precio total: {precio_con_margen}\n"
            respuesta += f"{mensaje_entrega}\n"
            respuesta += f"{mensaje_final} (Origen: {codigo_fuente})"
            
            return respuesta
                
        except Exception as e:
            logger.error(f"Error en generate_product_response: {e}")
            return f"Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta nuevamente más tarde."
    
    def detectar_producto(self, user_message, conversation_history=None):
        """
        ✅ ACTUALIZADO: Usa Gemini para analizar contexto completo y detectar productos.
        
        Args:
            user_message (str): Mensaje del usuario
            conversation_history (list, optional): Historial de conversación
            
        Returns:
            tuple: ('consulta_producto', nombre_producto) o ('consulta_general', None)
        """
        # ✅ USAR ANÁLISIS DE CONTEXTO CON GEMINI
        contexto_analisis = self.analizar_contexto_con_gemini(user_message, conversation_history)
        
        # Si Gemini detectó que es una consulta de cantidad para un producto previo
        if (contexto_analisis.get("es_cantidad") and 
            contexto_analisis.get("producto_contexto")):
            
            producto_contexto = contexto_analisis["producto_contexto"]
            cantidad = contexto_analisis.get("cantidad", 1)
            
            logger.info(f"Gemini detectó consulta de cantidad ({cantidad}) para producto: {producto_contexto}")
            return "consulta_producto", producto_contexto
        
        # Si no es cantidad en contexto, determinar si es consulta de producto nuevo
        if contexto_analisis.get("tipo_consulta") == "producto_nuevo":
            # Usar Gemini para extraer el producto del mensaje actual
            tipo, producto = self._detectar_producto_con_gemini(user_message)
            return tipo, producto
        elif contexto_analisis.get("tipo_consulta") == "general":
            return "consulta_general", None
        else:
            # Fallback: usar detección con Gemini para casos no claros
            tipo, producto = self._detectar_producto_con_gemini(user_message)
            return tipo, producto
