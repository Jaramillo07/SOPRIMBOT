# Busca esta sección en el método procesar_mensaje de la clase MessageHandler

# 3) Si es consulta de producto, hacemos scraping
if tipo_mensaje == "consulta_producto" and producto_detectado:
    logger.info(f"Iniciando búsqueda de información para: {producto_detectado}")
    try:
        # MODIFICADO: Ahora especificamos que queremos usar el scraper de Difarmer
        product_info = self.scraping_service.buscar_producto(producto_detectado, fuente="difarmer")
        
        if product_info:
            logger.info(f"Información encontrada para {producto_detectado}: {product_info}")
            respuesta = self.gemini_service.generate_product_response(mensaje, product_info)
            
            # Intentar enviar respuesta
            result = self.whatsapp_service.send_product_response(phone_number, respuesta, product_info)
            
            # Verificar si hubo error de sandbox
            if result.get("text", {}).get("sandbox_restriction"):
                logger.error("Error de sandbox al enviar respuesta de producto")
                return {
                    "success": False,
                    "message_type": "error_sandbox",
                    "error": result["text"].get("error"),
                    "suggestion": result["text"].get("suggestion"),
                    "respuesta": respuesta
                }
            
            return {
                "success": True,
                "message_type": "producto",
                "producto": producto_detectado,
                "tiene_imagen": bool(product_info.get("imagen")),
                "respuesta": respuesta
            }
        else:
            logger.info(f"No se encontró información para {producto_detectado}")
            respuesta = self.gemini_service.generate_response(
                f"No encontré información específica sobre {producto_detectado}. {mensaje}"
            )
            result = self.whatsapp_service.send_text_message(phone_number, respuesta)
            
            # Verificar si hubo error de sandbox
            if result.get("sandbox_restriction"):
                logger.error("Error de sandbox al enviar respuesta de producto no encontrado")
                return {
                    "success": False,
                    "message_type": "error_sandbox",
                    "error": result.get("error"),
                    "suggestion": result.get("suggestion"),
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
        # En caso de error, caer en respuesta general
