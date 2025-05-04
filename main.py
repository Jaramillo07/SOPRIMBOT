@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint principal para recibir mensajes de WhatsApp.
    Esta función procesa los mensajes entrantes y genera respuestas.
    """
    try:
        # Obtener el formulario de datos en lugar del JSON
        form = await request.form()
        logger.info(f"Mensaje recibido: {form}")
        
        # Obtener el texto del mensaje y el número de teléfono directamente del formulario
        msg_text = form.get("Body", "")
        phone_number = form.get("From", "")
        
        logger.info(f"Procesando mensaje: '{msg_text}' de {phone_number}")
                                
        # Procesar el mensaje usando nuestro manejador
        result = await message_handler.procesar_mensaje(msg_text, phone_number)
                                
        logger.info(f"Resultado del procesamiento: {result.get('message_type')}")
                                
        # No necesitamos devolver nada especial a WhatsApp
        return JSONResponse(content={"status": "processed"}, status_code=200)
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        # Siempre devolver 200 para que Meta no reintente
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)
