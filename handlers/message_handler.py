"""
Manejador de mensajes para SOPRIM BOT.
Optimizado para servicio farmacéutico con búsqueda en base interna y scrapers.
"""
import logging
import re
import traceback
from services.gemini_service import GeminiService
from services.whatsapp_service import WhatsAppService
from services.scraping_service import ScrapingService
from services.ocr_service import OCRService
from services.sheets_service import SheetsService  # Servicio para base interna
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
        self.sheets_service = SheetsService()  # Servicio para base interna
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
            "zoloft", "viagra", "cialis", "ventolin", "prilosec"
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
        Procesa un mensaje entrante y genera una respuesta.
        Optimizado para consultas de farmacia y medicamentos.
        
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
        
        # Procesar imágenes si hay alguna
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
        
        # Obtener historial de conversación de Firestore
        historial = obtener_historial(clean_phone)
        logger.info(f"Recuperado historial para {clean_phone}: {len(historial)} turnos")
        
        # Detectar si es consulta de medicamento
        es_consulta_medicamento, producto_detectado = self.detectar_consulta_medicamento(mensaje)
        
        # Si no detectamos localmente, intentar con Gemini
        if not es_consulta_medicamento or not producto_detectado:
            try:
                tipo_mensaje_gemini, producto_detectado_gemini = self.gemini_service.detectar_producto(mensaje)
                if tipo_mensaje_gemini == "consulta_producto" and producto_detectado_gemini:
                    es_consulta_medicamento = True
                    producto_detectado = producto_detectado_gemini
                    logger.info(f"Gemini detectó medicamento: {producto_detectado}")
            except Exception as e:
                logger.error(f"Error al detectar producto con Gemini: {e}")
        
        # Si es consulta de medicamento, primero buscamos en Google Sheets
        if es_consulta_medicamento and producto_detectado:
            logger.info(f"Iniciando búsqueda para: {producto_detectado}")
            
            # PRIMERO: Buscar en la base interna (Google Sheets)
            try:
                producto_interno = self.sheets_service.buscar_producto(producto_detectado)
                
                if producto_interno:
                    logger.info(f"¡Producto encontrado en base interna! Nombre: {producto_interno['nombre']}")
                    
                    # Preparar formato para la respuesta del bot
                    product_info = {
                        "opcion_mejor_precio": producto_interno,
                        "opcion_entrega_inmediata": None,
                        "tiene_doble_opcion": False
                    }
                    
                    # Generar respuesta con Gemini incluyendo el historial
                    respuesta = self.gemini_service.generate_product_response(
                        mensaje, 
                        product_info,
                        additional_context="Información de nuestra base de datos interna.",
                        conversation_history=historial
                    )
                    
                    # Guardar la interacción en Firestore
                    guardar_interaccion(clean_phone, mensaje, respuesta)
                    logger.info(f"Guardada interacción en Firestore para {clean_phone}")
                    
                    # Intentar enviar respuesta
                    result = self.whatsapp_service.send_text_message(phone_number, respuesta)
                    
                    # Verificar si hubo error de sandbox
                    if result.get("status") == "error":
                        logger.error("Error al enviar respuesta de producto interno")
                        return {
                            "success": False,
                            "message_type": "error_sandbox",
                            "error": result.get("message", "Error al enviar mensaje"),
                            "respuesta": respuesta
                        }
                    
                    # IMPORTANTE: Retornar aquí para NO ejecutar los scrapers
                    return {
                        "success": True,
                        "message_type": "producto_interno",
                        "producto": producto_detectado,
                        "fuente": "Base Interna",
                        "respuesta": respuesta
                    }
            except Exception as e:
                logger.error(f"Error al buscar en base interna: {e}")
                logger.error(traceback.format_exc())
            
            # SOLO si no encuentra en la base interna o hay error, continuar con los scrapers
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
                    
                    # Generar respuesta personalizada para producto no encontrado
                    respuesta = self.gemini_service.generate_response(
                        f"No encontré información específica sobre {producto_detectado} en ninguna de nuestras fuentes. "
                        f"Pero podemos ayudarte a conseguirlo. ¿Podrías proporcionar más detalles como "
                        f"marca, concentración o presentación? {mensaje}",
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
        
        # Para cualquier otro tipo de mensaje (incluyendo saludos o preguntas generales)
        logger.info("Generando respuesta orientada al negocio farmacéutico con Gemini")
        
        # NUEVO: Verificar si el mensaje incluía una imagen procesada con OCR
        contexto_imagen = ""
        if texto_extraido and media_urls and not texto_extraido.startswith("No se pudo"):
            contexto_imagen = f"El usuario envió una imagen que contiene el siguiente texto: {texto_extraido}"
            logger.info("Añadiendo contexto de imagen procesada")
        
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
            "message_type": "respuesta_farmaceutica",
            "respuesta": respuesta
        }
