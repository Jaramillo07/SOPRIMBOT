"""
Manejador de mensajes mejorado para SOPRIM BOT.
Usa Gemini como clasificador principal en lugar de palabras clave.
"""
import logging
import traceback
import json
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService
from services.ocr_service import OCRService
from services.sheets_service import SheetsService
from services.firestore_service import obtener_historial, guardar_interaccion
from config.settings import ALLOWED_TEST_NUMBERS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartMessageClassifier:
    """Clasificador inteligente que usa Gemini para determinar el tipo de mensaje."""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
    
    def classify_message(self, mensaje: str, historial: list = None) -> dict:
        """
        Clasifica un mensaje usando Gemini.
        
        Returns:
            dict: {
                "tipo": str,  # producto_especifico, cantidad, descuentos, entrega, general, saludo
                "producto": str or None,
                "cantidad": int or str or None,
                "confianza": str
            }
        """
        try:
            # Preparar contexto del historial
            contexto_historial = ""
            if historial:
                # Tomar solo los últimos 4 intercambios
                recent = historial[-8:]
                for turn in recent:
                    role = turn.get("role", "")
                    content = turn.get("content", "")[:80]
                    if role and content:
                        contexto_historial += f"{role}: {content}\n"
            
            prompt = f"""
Eres un clasificador de mensajes para una farmacia. Analiza el mensaje y clasifícalo:

TIPOS POSIBLES:
1. producto_especifico: Busca un medicamento/producto por nombre
2. cantidad: Solo indica cantidad para producto anterior (ej: "2", "quiero 3", "ambas")  
3. descuentos: Pregunta sobre precios, descuentos, promociones
4. entrega: Pregunta sobre tiempos de entrega, envío
5. general: Servicios, horarios, ubicación de farmacia
6. saludo: Saludos, despedidas, agradecimientos

CONTEXTO PREVIO:
{contexto_historial}

MENSAJE: "{mensaje}"

Responde SOLO este JSON:
{{
    "tipo": "tipo_exacto",
    "producto": "nombre_producto_o_null", 
    "cantidad": "numero_o_palabra_o_null",
    "confianza": "alta_o_media_o_baja"
}}

EJEMPLOS:
- "tienes paracetamol?" → {{"tipo":"producto_especifico","producto":"paracetamol","cantidad":null,"confianza":"alta"}}
- "2" (después de hablar de un producto) → {{"tipo":"cantidad","producto":null,"cantidad":"2","confianza":"alta"}}
- "ambas" → {{"tipo":"cantidad","producto":null,"cantidad":"ambas","confianza":"alta"}}
- "hay descuentos?" → {{"tipo":"descuentos","producto":null,"cantidad":null,"confianza":"alta"}}
- "entregan hoy?" → {{"tipo":"entrega","producto":null,"cantidad":null,"confianza":"alta"}}
- "hola" → {{"tipo":"saludo","producto":null,"cantidad":null,"confianza":"alta"}}
"""

            response = self.gemini_service.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Limpiar respuesta
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1]
            
            clasificacion = json.loads(response_text)
            
            # Validar estructura
            required_keys = ["tipo", "producto", "cantidad", "confianza"]
            if all(key in clasificacion for key in required_keys):
                logger.info(f"Clasificación: {clasificacion}")
                return clasificacion
            else:
                logger.warning(f"Clasificación incompleta: {clasificacion}")
                return self._clasificacion_fallback(mensaje)
                
        except Exception as e:
            logger.error(f"Error en clasificación con Gemini: {e}")
            return self._clasificacion_fallback(mensaje)
    
    def _clasificacion_fallback(self, mensaje: str) -> dict:
        """Clasificación básica de respaldo cuando falla Gemini."""
        mensaje_lower = mensaje.lower().strip()
        
        # Detectar saludos simples
        if mensaje_lower in ["hola", "hi", "hello", "buenos días", "buenas tardes", "buenas noches", "gracias", "bye", "adiós"]:
            return {"tipo": "saludo", "producto": None, "cantidad": None, "confianza": "media"}
        
        # Detectar números simples o palabras de cantidad
        if mensaje_lower.isdigit() or mensaje_lower in ["dos", "tres", "cuatro", "cinco", "ambas", "ambos", "todas", "todos"]:
            return {"tipo": "cantidad", "producto": None, "cantidad": mensaje_lower, "confianza": "media"}
        
        # Detectar palabras de descuentos
        if any(word in mensaje_lower for word in ["descuento", "promoción", "oferta", "barato", "precio"]):
            return {"tipo": "descuentos", "producto": None, "cantidad": None, "confianza": "media"}
        
        # Detectar consultas de entrega
        if any(word in mensaje_lower for word in ["entrega", "envío", "hoy", "mañana", "cuándo", "cuando"]):
            return {"tipo": "entrega", "producto": None, "cantidad": None, "confianza": "media"}
        
        # Por defecto, asumir que es búsqueda de producto
        return {"tipo": "producto_especifico", "producto": mensaje, "cantidad": None, "confianza": "baja"}

class MessageHandler:
    """
    Manejador de mensajes simplificado que usa clasificación inteligente.
    """
    
    def __init__(self):
        """Inicializa el manejador con sus servicios."""
        logger.info("Inicializando MessageHandler con clasificador inteligente")
        self.gemini_service = GeminiService()
        self.whatsapp_service = WhatsAppService()
        self.scraping_service = ScrapingService()
        self.ocr_service = OCRService()
        self.sheets_service = SheetsService()
        self.classifier = SmartMessageClassifier(self.gemini_service)
        logger.info("MessageHandler inicializado correctamente")
    
    def _convertir_cantidad_especial(self, cantidad_str: str, existencias_disponibles: int = 0) -> int:
        """Convierte palabras especiales a números."""
        cantidad_str = str(cantidad_str).lower()
        
        conversiones = {
            "una": 1, "uno": 1,
            "dos": 2, "ambas": 2, "ambos": 2, "las dos": 2, "los dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "todas": max(existencias_disponibles, 1),
            "todos": max(existencias_disponibles, 1),
            "disponibles": max(existencias_disponibles, 1),
            "completo": max(existencias_disponibles, 1),
            "completa": max(existencias_disponibles, 1),
            "total": max(existencias_disponibles, 1)
        }
        
        # Si es número directo
        if cantidad_str.isdigit():
            return int(cantidad_str)
        
        # Si es palabra especial
        for palabra, numero in conversiones.items():
            if palabra in cantidad_str:
                return numero
        
        return 1  # Por defecto
    
    def _extraer_ultimo_producto(self, historial: list) -> str:
        """Extrae el último producto mencionado en el historial."""
        if not historial:
            return None
        
        # Buscar en mensajes del bot que contengan información de productos
        for mensaje in reversed(historial):
            if mensaje.get("role") == "assistant":
                content = mensaje.get("content", "")
                # Si es una respuesta de producto típica
                if any(indicador in content for indicador in ["Precio:", "Entrega", "unidad(es)", "✅", "📦", "🚚"]):
                    # Buscar el mensaje del usuario anterior
                    idx = historial.index(mensaje)
                    if idx > 0:
                        user_msg = historial[idx-1]
                        if user_msg.get("role") == "user":
                            # Intentar extraer producto con Gemini
                            try:
                                clasificacion = self.classifier.classify_message(user_msg.get("content", ""))
                                if clasificacion.get("tipo") == "producto_especifico" and clasificacion.get("producto"):
                                    return clasificacion["producto"]
                            except:
                                pass
        
        return None
    
    async def procesar_mensaje(self, mensaje: str, phone_number: str, media_urls: list = None):
        """
        Procesa un mensaje usando clasificación inteligente.
        """
        logger.info(f"Procesando mensaje: '{mensaje}' de {phone_number}")
        
        # Limpiar número de teléfono
        clean_phone = phone_number.replace("whatsapp:", "")
        formatted_number = self.whatsapp_service.format_phone_number(phone_number)
        
        # Verificar números permitidos
        if ALLOWED_TEST_NUMBERS and formatted_number not in ALLOWED_TEST_NUMBERS:
            logger.warning(f"Número {formatted_number} no permitido")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": f"Número no autorizado",
                "respuesta": None
            }
        
        # Procesar imágenes si existen
        if media_urls:
            try:
                texto_extraido = await self.ocr_service.process_images(media_urls)
                if texto_extraido and not texto_extraido.startswith("No se pudo"):
                    if not mensaje or mensaje.strip() == "":
                        mensaje = texto_extraido
                    else:
                        mensaje = f"{mensaje}\n\n[Texto de imagen: {texto_extraido}]"
                    logger.info("Texto de imagen agregado al mensaje")
                elif not mensaje or mensaje.strip() == "":
                    respuesta = "No pude extraer texto de la imagen. ¿Podrías escribir tu consulta?"
                    self.whatsapp_service.send_text_message(phone_number, respuesta)
                    return {"success": True, "message_type": "error_ocr", "respuesta": respuesta}
            except Exception as e:
                logger.error(f"Error procesando imágenes: {e}")
                if not mensaje or mensaje.strip() == "":
                    respuesta = "Error procesando imagen. Envía tu consulta en texto."
                    self.whatsapp_service.send_text_message(phone_number, respuesta)
                    return {"success": False, "message_type": "error_imagen", "respuesta": respuesta}
        
        # Obtener historial
        historial = obtener_historial(clean_phone)
        logger.info(f"Historial: {len(historial)} turnos")
        
        # 🧠 CLASIFICAR MENSAJE CON GEMINI
        clasificacion = self.classifier.classify_message(mensaje, historial)
        tipo = clasificacion.get("tipo")
        producto = clasificacion.get("producto")
        cantidad = clasificacion.get("cantidad")
        
        logger.info(f"🎯 Clasificación: {tipo} | Producto: {producto} | Cantidad: {cantidad}")
        
        # 📊 MANEJAR SEGÚN TIPO
        
        if tipo == "cantidad":
            return await self._manejar_cantidad(mensaje, cantidad, historial, phone_number, clean_phone)
        
        elif tipo == "producto_especifico":
            return await self._manejar_producto(mensaje, producto, historial, phone_number, clean_phone)
        
        elif tipo == "descuentos":
            return await self._manejar_descuentos(mensaje, historial, phone_number, clean_phone)
        
        elif tipo == "entrega":
            return await self._manejar_entrega(mensaje, historial, phone_number, clean_phone)
        
        else:  # saludo, general
            return await self._manejar_general(mensaje, historial, phone_number, clean_phone)
    
    async def _manejar_cantidad(self, mensaje: str, cantidad: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja mensajes que solo indican cantidad."""
        # Buscar último producto
        ultimo_producto = self._extraer_ultimo_producto(historial)
        
        if not ultimo_producto:
            respuesta = "¿Para qué producto necesitas esa cantidad? Puedes decirme el nombre del medicamento."
            result = self.whatsapp_service.send_text_message(phone_number, respuesta)
            guardar_interaccion(clean_phone, mensaje, respuesta)
            return {"success": True, "message_type": "solicitud_producto", "respuesta": respuesta}
        
        # Convertir cantidad
        cantidad_numerica = self._convertir_cantidad_especial(cantidad)
        
        # Buscar producto en base interna primero
        producto_interno = None
        try:
            producto_interno = self.sheets_service.buscar_producto(ultimo_producto, threshold=0.7)
        except Exception as e:
            logger.error(f"Error buscando en base interna: {e}")
        
        if producto_interno:
            # Respuesta con producto interno
            product_info = {
                "opcion_mejor_precio": producto_interno,
                "opcion_entrega_inmediata": None,
                "tiene_doble_opcion": False
            }
            
            respuesta = self.gemini_service.generate_product_response(
                f"quiero {cantidad_numerica} {ultimo_producto}", 
                product_info,
                additional_context="Actualización de cantidad.",
                conversation_history=historial
            )
            
            result = self.whatsapp_service.send_text_message(phone_number, respuesta)
            guardar_interaccion(clean_phone, mensaje, respuesta)
            
            return {
                "success": True,
                "message_type": "cantidad_actualizada",
                "producto": ultimo_producto,
                "cantidad": cantidad_numerica,
                "respuesta": respuesta
            }
        
        # Si no está en base interna, buscar en scrapers
        try:
            product_info = self.scraping_service.buscar_producto(ultimo_producto)
            
            if product_info and (product_info.get("opcion_entrega_inmediata") or product_info.get("opcion_mejor_precio")):
                respuesta = self.gemini_service.generate_product_response(
                    f"quiero {cantidad_numerica} {ultimo_producto}", 
                    product_info,
                    additional_context="Actualización de cantidad.",
                    conversation_history=historial
                )
                
                result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                guardar_interaccion(clean_phone, mensaje, respuesta)
                
                return {
                    "success": True,
                    "message_type": "cantidad_actualizada",
                    "producto": ultimo_producto,
                    "cantidad": cantidad_numerica,
                    "respuesta": respuesta
                }
        except Exception as e:
            logger.error(f"Error en scrapers: {e}")
        
        # Si no encontramos el producto
        respuesta = f"No encontré información actualizada sobre {ultimo_producto}. ¿Podrías confirmar el nombre del producto?"
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "producto_no_encontrado", "respuesta": respuesta}
    
    async def _manejar_producto(self, mensaje: str, producto: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja búsquedas de productos específicos."""
        logger.info(f"Buscando producto: {producto}")
        
        # Buscar en base interna primero
        producto_interno = None
        try:
            producto_interno = self.sheets_service.buscar_producto(producto, threshold=0.7)
        except Exception as e:
            logger.error(f"Error en base interna: {e}")
        
        if producto_interno:
            logger.info(f"Producto encontrado en base interna: {producto_interno.get('nombre')}")
            
            product_info = {
                "opcion_mejor_precio": producto_interno,
                "opcion_entrega_inmediata": None,
                "tiene_doble_opcion": False
            }
            
            respuesta = self.gemini_service.generate_product_response(
                mensaje, 
                product_info,
                additional_context="Información de nuestra base interna.",
                conversation_history=historial
            )
            
            result = self.whatsapp_service.send_text_message(phone_number, respuesta)
            guardar_interaccion(clean_phone, mensaje, respuesta)
            
            return {
                "success": True,
                "message_type": "producto_interno",
                "producto": producto,
                "fuente": "Base Interna",
                "respuesta": respuesta
            }
        
        # Buscar en scrapers
        try:
            product_info = self.scraping_service.buscar_producto(producto)
            
            if product_info and (product_info.get("opcion_entrega_inmediata") or product_info.get("opcion_mejor_precio")):
                respuesta = self.gemini_service.generate_product_response(
                    mensaje, 
                    product_info,
                    additional_context="Información de farmacias asociadas.",
                    conversation_history=historial
                )
                
                result = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
                guardar_interaccion(clean_phone, mensaje, respuesta)
                
                return {
                    "success": True,
                    "message_type": "producto_externo",
                    "producto": producto,
                    "respuesta": respuesta
                }
        except Exception as e:
            logger.error(f"Error en scrapers: {e}")
        
        # Producto no encontrado
        respuesta = f"No encontré {producto} en nuestras fuentes. ¿Podrías proporcionar más detalles como marca o presentación?"
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "producto_no_encontrado", "respuesta": respuesta}
    
    async def _manejar_descuentos(self, mensaje: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja consultas sobre descuentos y promociones."""
        respuestas_descuento = [
            "Sí manejamos descuentos por volumen. Contáctanos para más detalles.",
            "Tenemos promociones especiales dependiendo del producto. Llámanos para informarte.",
            "Los descuentos aplican según cantidad y producto. Comunícate directamente con nosotros."
        ]
        
        # Seleccionar respuesta basada en hash del mensaje
        indice = hash(mensaje) % len(respuestas_descuento)
        respuesta = respuestas_descuento[indice]
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "consulta_descuentos", "respuesta": respuesta}
    
    async def _manejar_entrega(self, mensaje: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja consultas sobre entregas."""
        respuesta = "La entrega normalmente es al día siguiente. Para entrega el mismo día, contactanos directamente para confirmar disponibilidad."
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "consulta_entrega", "respuesta": respuesta}
    
    async def _manejar_general(self, mensaje: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja mensajes generales, saludos y otros."""
        respuesta = self.gemini_service.generate_response(
            f"{mensaje}\n\n[INSTRUCCIÓN: Responde como asistente de farmacia profesional]",
            conversation_history=historial
        )
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "respuesta_general", "respuesta": respuesta}
