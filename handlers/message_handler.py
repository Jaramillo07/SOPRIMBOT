"""
Manejador de mensajes para SOPRIM BOT.
CORREGIDO: Mejor manejo de contexto y cantidad específica vs consultas generales.
"""
import logging
import re
import traceback
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService
from services.ocr_service import OCRService
from services.sheets_service import SheetsService
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
    Clase que maneja los mensajes entrantes y coordina las respuestas
    con enfoque en consultas de productos farmacéuticos.
    CORREGIDO: Mejor manejo de contexto.
    """
    
    def __init__(self):
        """
        Inicializa el manejador de mensajes con sus servicios asociados.
        """
        logger.info("Inicializando MessageHandler optimizado para servicio farmacéutico")
        self.gemini_service = GeminiService()
        self.whatsapp_service = WhatsAppService()
        self.scraping_service = ScrapingService()
        self.ocr_service = OCRService()
        self.sheets_service = SheetsService()
        logger.info("MessageHandler inicializado correctamente")
    
    def detectar_consulta_medicamento(self, mensaje):
        """
        Detecta si el mensaje es una consulta sobre un medicamento.
        Optimizado para el sector farmacéutico.
        
        Args:
            mensaje (str): Mensaje a analizar
            
        Returns:
            tuple: (es_consulta_medicamento, producto_detectado)
        """
        if not mensaje:
            return False, None
            
        mensaje_lower = mensaje.lower()
        producto_detectado = None
        
        # Patrones para detectar consultas sobre productos farmacéuticos
        patrones_producto = [
            r'(?:tienes|tienen|venden|hay|disponible|disponibles)\s+(.+?)(?:\?|$)',
            r'(?:busco|necesito|quiero|ocupo)\s+(.+?)(?:\?|$)',
            r'(?:me pueden conseguir|consiguen|habrá|habra)\s+(.+?)(?:\?|$)',
            r'(?:vende[ns]|tiene[ns]|manejan|traen)\s+(.+?)(?:\?|$)',
            r'(?:precio de|cuánto cuesta|costo de|valor de|precio del|cuanto vale)\s+(.+?)(?:\?|$)',
            r'(?:dosis|pastillas|tabletas|comprimidos|jarabe|suspensión|ampolletas)\s+(?:de|del|para)\s+(.+?)(?:\?|$)',
            r'(?:medicamento|medicina|medicinas|fármaco|remedio)\s+(?:para|de|del|contra)\s+(.+?)(?:\?|$)'
        ]
        
        # Buscar coincidencias en los patrones
        for patron in patrones_producto:
            match = re.search(patron, mensaje_lower)
            if match:
                producto_detectado = match.group(1).strip()
                # Limpiar términos comunes
                terminos_eliminar = ["el", "la", "los", "las", "algún", "alguna", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas"]
                for termino in terminos_eliminar:
                    if producto_detectado.startswith(f"{termino} "):
                        producto_detectado = producto_detectado[len(termino)+1:]
                
                logger.info(f"Producto detectado: {producto_detectado}")
                return True, producto_detectado
        
        # Lista ampliada de medicamentos comunes
        palabras_medicamento = [
            # Analgésicos y antiinflamatorios
            "paracetamol", "ibuprofeno", "aspirina", "naproxeno", "diclofenaco", 
            "ketorolaco", "indometacina", "meloxicam", "piroxicam", "metamizol",
            # Antibióticos
            "amoxicilina", "azitromicina", "ciprofloxacino", "cefalexina", 
            "ampicilina", "penicilina", "claritromicina", "doxiciclina", 
            "clindamicina", "levofloxacino", "moxifloxacino", "ceftriaxona",
            # Antiácidos y protectores gástricos
            "omeprazol", "pantoprazol", "lansoprazol", "esomeprazol", 
            "ranitidina", "famotidina", "sucralfato", "magaldrato",
            # Antialérgicos
            "loratadina", "cetirizina", "fexofenadina", "desloratadina", 
            "clorfenamina", "difenhidramina",
            # Otros medicamentos comunes
            "metformina", "captopril", "enalapril", "losartan", "atenolol", 
            "metoprolol", "amlodipino", "simvastatina", "atorvastatina", 
            "levotiroxina", "alprazolam", "clonazepam", "diazepam", 
            "fluoxetina", "sertralina", "paroxetina", "sildenafil",
            "tadalafil", "ambroxol", "salbutamol", "prednisona", 
            "dexametasona", "betametasona", "aciclovir", "valaciclovir",
            "loperamida", "metoclopramida", "butilhioscina", "tramadol",
            "codeína", "fluconazol", "itraconazol", "nistatina",
            "clotrimazol", "miconazol", "rapamune", "sirolimus",
            # Nombres comerciales comunes
            "aspirina", "tylenol", "advil", "motrin", "aleve", "nexium", 
            "zantac", "pepcid", "claritin", "zyrtec", "allegra", "benadryl",
            "lipitor", "crestor", "synthroid", "xanax", "valium", "prozac",
            "zoloft", "viagra", "cialis", "ventolin", "prilosec", "dualgos"
        ]
        
        for palabra in palabras_medicamento:
            if palabra in mensaje_lower:
                logger.info(f"Medicamento detectado por palabra clave: {palabra}")
                return True, palabra
        
        # Buscar términos que indiquen síntomas o condiciones médicas
        sintomas_condiciones = [
            "dolor", "fiebre", "gripe", "tos", "diarrea", "vómito", "náusea",
            "alergia", "infección", "inflamación", "presión alta", "diabetes",
            "colesterol", "tiroides", "ansiedad", "depresión", "insomnio",
            "artritis", "migraña", "asma", "acidez", "gastritis", "úlcera"
        ]
        
        for sintoma in sintomas_condiciones:
            if sintoma in mensaje_lower:
                # Buscar el término más largo que contenga el síntoma
                palabras = mensaje_lower.split()
                for i in range(len(palabras)):
                    if sintoma in palabras[i]:
                        # Intentar encontrar una frase de contexto (3 palabras antes y después)
                        inicio = max(0, i-3)
                        fin = min(len(palabras), i+4)
                        contexto = " ".join(palabras[inicio:fin])
                        logger.info(f"Consulta médica detectada por síntoma: {sintoma} (contexto: {contexto})")
                        return True, contexto
        
        # Si no se detecta un producto o síntoma específico, verificar si es consulta general
        if any(term in mensaje_lower for term in ["medicina", "medicamento", "pastilla", "farmacia", "remedio", "receta"]):
            logger.info("Consulta general sobre farmacia/medicamentos detectada")
            return True, None
        
        logger.info("No se detectó consulta de medicamento específico")
        return False, None
    
    async def procesar_mensaje(self, mensaje: str, phone_number: str, media_urls: list = None):
        """
        ✅ CORREGIDO: Procesa un mensaje con mejor manejo de contexto y cantidad.
        
        Args:
            mensaje (str): Mensaje entrante del usuario
            phone_number (str): Número de teléfono del remitente
            media_urls (list, optional): Lista de URLs de imágenes adjuntas
            
        Returns:
            dict: Resultado de la operación
        """
        logger.info(f"📱 Procesando mensaje: '{mensaje}' de {phone_number}")
        if media_urls:
            logger.info(f"🖼️ El mensaje incluye {len(media_urls)} imágenes: {media_urls}")
        
        # Limpiar el número de teléfono para Firestore
        clean_phone = phone_number.replace("whatsapp:", "")
        
        # Verificar si el número está en la lista de permitidos (solo en pruebas)
        formatted_number = self.whatsapp_service.format_phone_number(phone_number)
        logger.info(f"📞 Número formateado: {formatted_number}")
        if ALLOWED_TEST_NUMBERS and formatted_number not in ALLOWED_TEST_NUMBERS:
            logger.warning(f"⚠️ Número {formatted_number} no está en la lista de permitidos: {ALLOWED_TEST_NUMBERS}")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": f"El número {formatted_number} no está en la lista de números permitidos para pruebas",
                "respuesta": None
            }
        else:
            logger.info(f"✅ Número {formatted_number} está permitido para interacción")
        
        # Procesar imágenes si hay alguna
        texto_extraido = ""
        if media_urls:
            logger.info(f"🖼️ Procesando {len(media_urls)} imágenes con OCR...")
            try:
                texto_extraido = await self.ocr_service.process_images(media_urls)
                logger.info(f"📝 Resultado del procesamiento OCR: {texto_extraido[:200] if texto_extraido else 'No hay texto'}")
                
                if texto_extraido and not texto_extraido.startswith("No se pudo"):
                    logger.info(f"✅ Texto extraído con éxito: {texto_extraido[:100]}...")
                    # Si no hay mensaje de texto, usamos solo el texto extraído
                    if not mensaje or mensaje.strip() == "":
                        mensaje = texto_extraido
                    else:
                        # Si hay ambos, los combinamos
                        mensaje = f"{mensaje}\n\n[Texto de la imagen: {texto_extraido}]"
                    
                    logger.info(f"📝 Mensaje combinado: {mensaje[:100]}...")
                else:
                    logger.warning("⚠️ No se pudo extraer texto de las imágenes")
                    if not mensaje or mensaje.strip() == "":
                        respuesta = "He recibido tu imagen pero no he podido extraer texto de ella. ¿Podrías enviar el mensaje en formato texto o una imagen más clara?"
                        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                        return {
                            "success": True,
                            "message_type": "error_ocr",
                            "respuesta": respuesta
                        }
            except Exception as e:
                logger.error(f"❌ Error al procesar imágenes: {e}")
                logger.error(traceback.format_exc())
                if not mensaje or mensaje.strip() == "":
                    respuesta = "Lo siento, hubo un problema técnico al procesar tu imagen. ¿Podrías enviar tu consulta en formato texto?"
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    return {
                        "success": False,
                        "message_type": "error_imagen",
                        "error": str(e),
                        "respuesta": respuesta
                    }
        
        # Obtener historial de conversación de Firestore
        historial = obtener_historial(clean_phone)
        logger.info(f"📚 Recuperado historial para {clean_phone}: {len(historial)} turnos")
        
        # ✅ CORREGIDO: Analizar contexto con Gemini ANTES de procesar
        logger.info("🧠 Analizando contexto con Gemini...")
        contexto_analisis = self.gemini_service.analizar_contexto_con_gemini(mensaje, historial)
        logger.info(f"📊 Análisis de contexto Gemini: {contexto_analisis}")
        
        # ✅ CORREGIDO: Si es consulta de CANTIDAD para un producto anterior
        if (contexto_analisis.get("es_cantidad") and 
            contexto_analisis.get("producto_contexto")):
            
            producto_del_contexto = contexto_analisis["producto_contexto"]
            cantidad_solicitada = contexto_analisis.get("cantidad", 1)
            
            logger.info(f"📦 DETECTADA CONSULTA DE CANTIDAD: {cantidad_solicitada} unidades de {producto_del_contexto}")
            
            # Buscar el producto del contexto en base interna
            producto_interno = None
            try:
                logger.info(f"🔍 Buscando en base interna: {producto_del_contexto}")
                producto_interno = self.sheets_service.buscar_producto(producto_del_contexto, threshold=0.7)
            except Exception as e:
                logger.error(f"❌ Error al buscar en base interna: {e}")

            if producto_interno:
                logger.info(f"✅ PRODUCTO DEL CONTEXTO encontrado en base interna: {producto_interno.get('nombre', 'desconocido')}")
                
                try:
                    # Preparar formato para la respuesta del bot
                    product_info = {
                        "opcion_mejor_precio": producto_interno,
                        "opcion_entrega_inmediata": None,
                        "tiene_doble_opcion": False
                    }
                    
                    # ✅ CORREGIDO: Usar parámetros de cantidad específica
                    respuesta = self.gemini_service.generate_product_response(
                        mensaje, 
                        product_info,
                        additional_context=f"Cliente solicita {cantidad_solicitada} unidades del producto {producto_del_contexto} de nuestra base de datos interna.",
                        conversation_history=historial,
                        es_consulta_cantidad=True,
                        cantidad_solicitada=cantidad_solicitada
                    )
                    
                    # Guardar la interacción en Firestore
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
                    
                    # Intentar enviar respuesta
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    if result.get("status") == "error":
                        logger.error("❌ Error al enviar respuesta de cantidad producto interno")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result.get("message", "Error al enviar mensaje"),
                            "respuesta": respuesta
                        }
                    
                    return {
                        "success": True,
                        "message_type": "cantidad_producto_interno",
                        "producto": producto_del_contexto,
                        "cantidad": cantidad_solicitada,
                        "fuente": "Base Interna",
                        "respuesta": respuesta
                    }
                except Exception as e:
                    logger.error(f"❌ Error al procesar cantidad producto interno: {e}")
                    logger.error(traceback.format_exc())
            
            # Si no está en base interna, buscar con scrapers
            logger.info(f"🔍 Producto del contexto NO encontrado en base interna, procediendo con scrapers: {producto_del_contexto}")
            try:
                product_info = self.scraping_service.buscar_producto(producto_del_contexto)
                
                if product_info:
                    logger.info(f"✅ Información encontrada para cantidad de {producto_del_contexto} en {product_info.get('fuente', 'farmacia')}")
                    
                    farmacia_nombre = product_info.get('nombre_farmacia', product_info.get('fuente', 'farmacia'))
                    additional_context = f"Cliente solicita {cantidad_solicitada} unidades. Esta información proviene de {farmacia_nombre}."
                    
                    # ✅ CORREGIDO: Usar parámetros de cantidad específica
                    respuesta = self.gemini_service.generate_product_response(
                        mensaje, 
                        product_info,
                        additional_context=additional_context,
                        conversation_history=historial,
                        es_consulta_cantidad=True,
                        cantidad_solicitada=cantidad_solicitada
                    )
                    
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
                    
                    result = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
                    
                    if result.get("text", {}).get("status") == "error":
                        logger.error("❌ Error al enviar respuesta de cantidad producto scraper")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result["text"].get("message", "Error al enviar mensaje"),
                            "respuesta": respuesta
                        }
                    
                    return {
                        "success": True,
                        "message_type": "cantidad_producto_scraper",
                        "producto": producto_del_contexto,
                        "cantidad": cantidad_solicitada,
                        "fuente": product_info.get('fuente', 'farmacia'),
                        "tiene_imagen": bool(product_info.get("imagen")),
                        "respuesta": respuesta
                    }
                else:
                    logger.info(f"❌ No se encontró información para cantidad de {producto_del_contexto} en ninguna farmacia")
                    
                    respuesta = f"Lo siento, no encontré disponibilidad de {producto_del_contexto} para {cantidad_solicitada} unidades. ¿Te gustaría que busque alternativas similares?"
                    
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
                    
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    if result.get("status") == "error":
                        logger.error("❌ Error al enviar respuesta de cantidad producto no encontrado")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result.get("message", "Error al enviar mensaje"),
                            "respuesta": respuesta
                        }
                    
                    return {
                        "success": True,
                        "message_type": "cantidad_producto_no_encontrado",
                        "producto": producto_del_contexto,
                        "cantidad": cantidad_solicitada,
                        "respuesta": respuesta
                    }
            except Exception as e:
                logger.error(f"❌ Error durante el scraping para cantidad: {e}")
                logger.error(traceback.format_exc())
                
                respuesta = f"Lo siento, hubo un problema técnico al buscar {producto_del_contexto} para {cantidad_solicitada} unidades. Por favor, intenta nuevamente."
                guardar_interaccion(clean_phone, mensaje, respuesta)
                result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                
                return {
                    "success": False,
                    "message_type": "error_scraping_cantidad",
                    "error": str(e),
                    "producto": producto_del_contexto,
                    "cantidad": cantidad_solicitada,
                    "respuesta": respuesta
                }
        
        # ✅ CORREGIDO: Si NO es consulta de cantidad, continuar con el flujo normal
        # Detectar si es consulta de medicamento NUEVO
        es_consulta_medicamento, producto_detectado = self.detectar_consulta_medicamento(mensaje)
        
        # Si no detectamos localmente, intentar con Gemini
        if not es_consulta_medicamento or not producto_detectado:
            try:
                tipo_mensaje_gemini, producto_detectado_gemini = self.gemini_service.detectar_producto(
                    mensaje, 
                    conversation_history=historial
                )
                if tipo_mensaje_gemini == "consulta_producto" and producto_detectado_gemini:
                    es_consulta_medicamento = True
                    producto_detectado = producto_detectado_gemini
                    logger.info(f"🧠 Gemini detectó medicamento NUEVO: {producto_detectado}")
            except Exception as e:
                logger.error(f"❌ Error al detectar producto con Gemini: {e}")
        
        # ✅ CORREGIDO: Si es consulta de medicamento NUEVO (consulta general de disponibilidad)
        if es_consulta_medicamento and producto_detectado:
            logger.info(f"🔍 Iniciando búsqueda para producto NUEVO: {producto_detectado}")
            
            # PRIMERO: Buscar en la base interna (Google Sheets)
            producto_interno = None
            try:
                logger.info(f"🔍 Buscando producto NUEVO en base interna: '{producto_detectado}'")
                producto_interno = self.sheets_service.buscar_producto(producto_detectado, threshold=0.7)
                logger.info(f"📊 Resultado de búsqueda interna: {producto_interno}")
            except Exception as e:
                logger.error(f"❌ Error al buscar en base interna: {e}")
                logger.error(traceback.format_exc())
            
            # Si encontramos el producto en la base interna, procesarlo
            if producto_interno:
                logger.info(f"✅ ÉXITO: Producto NUEVO encontrado en base interna: {producto_interno.get('nombre', 'desconocido')}")
                
                try:
                    product_info = {
                        "opcion_mejor_precio": producto_interno,
                        "opcion_entrega_inmediata": None,
                        "tiene_doble_opcion": False
                    }
                    
                    # ✅ CORREGIDO: Consulta general de disponibilidad (NO cantidad específica)
                    respuesta = self.gemini_service.generate_product_response(
                        mensaje, 
                        product_info,
                        additional_context="Información de nuestra base de datos interna.",
                        conversation_history=historial,
                        es_consulta_cantidad=False,  # ✅ CLAVE: NO es consulta de cantidad
                        cantidad_solicitada=None     # ✅ CLAVE: No hay cantidad específica
                    )
                    
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
                    
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    if result.get("status") == "error":
                        logger.error("❌ Error al enviar respuesta de producto interno")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result.get("message", "Error al enviar mensaje"),
                            "respuesta": respuesta
                        }
                    
                    return {
                        "success": True,
                        "message_type": "producto_interno",
                        "producto": producto_detectado,
                        "fuente": "Base Interna",
                        "respuesta": respuesta
                    }
                except Exception as e:
                    logger.error(f"❌ Error al procesar producto interno: {e}")
                    logger.error(traceback.format_exc())
                    return {
                        "success": False,
                        "message_type": "error_producto_interno",
                        "error": str(e),
                        "producto": producto_detectado,
                        "respuesta": f"Lo siento, encontré información del producto pero hubo un error al procesarla. Por favor, intenta nuevamente."
                    }
            
            # SOLO si no encuentra en la base interna, continuar con los scrapers
            logger.info(f"🔍 Producto NUEVO NO encontrado en base interna, procediendo con scrapers: {producto_detectado}")
            try:
                product_info = self.scraping_service.buscar_producto(producto_detectado)
                
                if product_info:
                    logger.info(f"✅ Información encontrada para {producto_detectado} en {product_info.get('fuente', 'farmacia')}")
                    
                    farmacia_nombre = product_info.get('nombre_farmacia', product_info.get('fuente', 'farmacia'))
                    additional_context = f"Esta información proviene de {farmacia_nombre}."
                    
                    # ✅ CORREGIDO: Consulta general de disponibilidad (NO cantidad específica)
                    respuesta = self.gemini_service.generate_product_response(
                        mensaje, 
                        product_info,
                        additional_context=additional_context,
                        conversation_history=historial,
                        es_consulta_cantidad=False,  # ✅ CLAVE: NO es consulta de cantidad
                        cantidad_solicitada=None     # ✅ CLAVE: No hay cantidad específica
                    )
                    
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
                    
                    result = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
                    
                    if result.get("text", {}).get("status") == "error":
                        logger.error("❌ Error al enviar respuesta de producto")
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
                    logger.info(f"❌ No se encontró información para {producto_detectado} en ninguna farmacia")
                    
                    respuesta = self.gemini_service.generate_response(
                        f"No encontré información específica sobre {producto_detectado} en ninguna de nuestras fuentes. "
                        f"Pero podemos ayudarte a conseguirlo. ¿Podrías proporcionar más detalles como "
                        f"marca, concentración o presentación? {mensaje}",
                        conversation_history=historial
                    )
                    
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
                    
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    if result.get("status") == "error":
                        logger.error("❌ Error al enviar respuesta de producto no encontrado")
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
                logger.error(f"❌ Error durante el scraping: {e}")
                logger.error(traceback.format_exc())
        
        # Para cualquier otro tipo de mensaje (incluyendo saludos o preguntas generales)
        logger.info("💬 Generando respuesta orientada al negocio farmacéutico con Gemini")
        
        # Verificar si el mensaje incluía una imagen procesada con OCR
        contexto_imagen = ""
        if texto_extraido and media_urls and not texto_extraido.startswith("No se pudo"):
            contexto_imagen = f"El usuario envió una imagen que contiene el siguiente texto: {texto_extraido}"
            logger.info("🖼️ Añadiendo contexto de imagen procesada")
        
        # Generar respuesta con Gemini incluyendo el historial y contexto de imagen
        mensaje_para_gemini = mensaje
        if contexto_imagen:
            mensaje_para_gemini = f"{mensaje}\n\n[CONTEXTO: {contexto_imagen}]"
            
        # Instrucción adicional para Gemini: enfoque en farmacia
        mensaje_con_instruccion = f"{mensaje_para_gemini}\n\n[INSTRUCCIÓN: Responde como asistente de farmacia, orienta la respuesta hacia servicios farmacéuticos o información de salud relevante]"
        
        respuesta = self.gemini_service.generate_response(
            mensaje_con_instruccion,
            conversation_history=historial
        )
        
        # Guardar la interacción en Firestore
        guardar_interaccion(clean_phone, mensaje, respuesta)
        logger.info(f"💾 Guardada interacción en Firestore para {clean_phone}")
        
        result = self.whatsapp_service.send_text_message(phone_number, respuesta)
        
        # Verificar si hubo error de sandbox
        if result.get("status") == "error":
            logger.error("❌ Error al enviar respuesta general")
            return {
                "success": False,
                "message_type": "error_sandbox",
                "error": result.get("message", "Error al enviar mensaje"),
                "respuesta": respuesta
            }
        
        return {
            "success": True,
            "message_type": "respuesta_farmaceutica",
            "respuesta": respuesta
        }
