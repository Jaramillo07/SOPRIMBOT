"""
MessageHandler actualizado que usa el GeminiService optimizado con clasificación inteligente.
Mantiene toda la funcionalidad existente pero simplifica la lógica de detección.
"""
import logging
import traceback
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

class MessageHandler:
    """
    Manejador de mensajes que usa el GeminiService optimizado con clasificación inteligente.
    """
    
    def __init__(self):
        """Inicializa el manejador con sus servicios."""
        logger.info("Inicializando MessageHandler con GeminiService optimizado")
        self.gemini_service = GeminiService()
        self.whatsapp_service = WhatsAppService()
        self.scraping_service = ScrapingService()
        self.ocr_service = OCRService()
        self.sheets_service = SheetsService()
        logger.info("MessageHandler inicializado correctamente")
    
    def _convertir_cantidad_especial(self, cantidad_str: str, existencias_disponibles: int = 0) -> int:
        """Convierte palabras especiales a números."""
        if isinstance(cantidad_str, int):
            return cantidad_str
            
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
    
    async def procesar_mensaje(self, mensaje: str, phone_number: str, media_urls: list = None):
        """
        Procesa un mensaje usando el clasificador inteligente del GeminiService.
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
        
        # 🧠 USAR CLASIFICADOR INTELIGENTE DEL GEMINI SERVICE
        try:
            clasificacion = self.gemini_service.classify_message_smart(mensaje, historial)
            tipo = clasificacion.get("tipo")
            producto = clasificacion.get("producto")
            cantidad = clasificacion.get("cantidad")
            confianza = clasificacion.get("confianza")
            
            logger.info(f"🎯 Clasificación: {tipo} | Producto: {producto} | Cantidad: {cantidad} | Confianza: {confianza}")
        except Exception as e:
            logger.error(f"Error en clasificación inteligente: {e}")
            # Usar detección clásica como respaldo
            tipo, producto = self.gemini_service.detectar_producto(mensaje, historial)
            cantidad = None
            if tipo == "consulta_producto":
                tipo = "producto_especifico"
            else:
                tipo = "general"
            logger.info(f"🔧 Clasificación de respaldo: {tipo} | Producto: {producto}")
        
        # 📊 MANEJAR SEGÚN TIPO DETECTADO
        
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
        # Usar la función existente del GeminiService para extraer último producto
        ultimo_producto = self.gemini_service._extraer_ultimo_producto(historial)
        
        if not ultimo_producto:
            respuesta = "¿Para qué producto necesitas esa cantidad? Puedes decirme el nombre del medicamento."
            result = self.whatsapp_service.send_text_message(phone_number, respuesta)
            guardar_interaccion(clean_phone, mensaje, respuesta)
            return {"success": True, "message_type": "solicitud_producto", "respuesta": respuesta}
        
        # Convertir cantidad usando función helper
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
            
            # Usar la función completa del GeminiService
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
            
            # Usar la función completa del GeminiService
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
        # Usar las respuestas de descuento del GeminiService
        if self.gemini_service._es_consulta_descuento(mensaje):
            respuestas_descuento = [
                "Sí manejamos descuentos por volumen. Contáctanos para más detalles.",
                "Tenemos promociones especiales dependiendo del producto. Llámanos para informarte.",
                "Los descuentos aplican según cantidad y producto. Comunícate directamente con nosotros."
            ]
            
            # Seleccionar respuesta basada en hash del mensaje
            indice = hash(mensaje) % len(respuestas_descuento)
            respuesta = respuestas_descuento[indice]
        else:
            # Usar Gemini para generar respuesta más contextual
            respuesta = self.gemini_service.generate_response(
                f"{mensaje}\n\n[INSTRUCCIÓN: El usuario pregunta sobre descuentos o promociones. Responde como farmacia que maneja descuentos por volumen]",
                conversation_history=historial
            )
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "consulta_descuentos", "respuesta": respuesta}
    
    async def _manejar_entrega(self, mensaje: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja consultas sobre entregas."""
        # Usar la función existente del GeminiService
        if self.gemini_service._es_consulta_entrega_hoy(mensaje):
            respuesta = "La entrega normalmente es al día siguiente. Para entrega el mismo día, contáctanos directamente para confirmar disponibilidad."
        else:
            # Usar Gemini para respuesta más contextual
            respuesta = self.gemini_service.generate_response(
                f"{mensaje}\n\n[INSTRUCCIÓN: El usuario pregunta sobre entregas o tiempos de envío. Menciona que normalmente es al día siguiente]",
                conversation_history=historial
            )
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "consulta_entrega", "respuesta": respuesta}
    
    async def _manejar_general(self, mensaje: str, historial: list, phone_number: str, clean_phone: str):
        """Maneja mensajes generales, saludos y otros."""
        # Usar la función existente del GeminiService
        respuesta = self.gemini_service.generate_response(
            f"{mensaje}\n\n[INSTRUCCIÓN: Responde como asistente de farmacia profesional]",
            conversation_history=historial
        )
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        guardar_interaccion(clean_phone, mensaje, respuesta)
        
        return {"success": True, "message_type": "respuesta_general", "respuesta": respuesta}
    
    # ============================================================================
    # MANTENER FUNCIÓN LEGACY PARA COMPATIBILIDAD
    # ============================================================================
    
    def detectar_consulta_medicamento(self, mensaje):
        """
        Función legacy mantenida para compatibilidad.
        Ahora usa el clasificador inteligente internamente.
        """
        try:
            clasificacion = self.gemini_service.classify_message_smart(mensaje)
            if clasificacion.get("tipo") == "producto_especifico":
                return True, clasificacion.get("producto")
            else:
                return False, None
        except Exception as e:
            logger.error(f"Error en detectar_consulta_medicamento: {e}")
            # Respaldo usando función clásica
            tipo, producto = self.gemini_service.detectar_producto(mensaje)
            return tipo == "consulta_producto", producto
