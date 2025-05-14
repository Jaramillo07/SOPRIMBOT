import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar el manejador de mensajes
from handlers.message_handler import MessageHandler

# Importar función del scraper
from services.scraper_difarmer.main import ejecutar_scraper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app
app = FastAPI(
    title="SOPRIM BOT API",
    description="API para el chatbot de farmacia SOPRIM BOT"
)

# Token para verificación del webhook
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "soprim123")

# Inicializar handler
message_handler = MessageHandler()


@app.get("/webhook")
async def verify(request: Request):
    args = dict(request.query_params)
    if args.get("hub.mode") == "subscribe" and args.get("hub.verify_token") == VERIFY_TOKEN:
        logger.info("Webhook verificado correctamente")
        return PlainTextResponse(content=args.get("hub.challenge"), status_code=200)
    logger.warning("Intento de verificación no autorizado")
    return PlainTextResponse(content="Unauthorized", status_code=403)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        form = await request.form()
        logger.info(f"Mensaje recibido (form): {form}")

        msg_text = form.get("Body", "")
        phone_number = form.get("From", "")

        logger.info(f"Procesando mensaje: '{msg_text}' de {phone_number}")
        result = await message_handler.procesar_mensaje(msg_text, phone_number)

        logger.info(f"Resultado del procesamiento: {result.get('message_type')}")
        return JSONResponse(content={"status": "processed"}, status_code=200)

    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)


@app.get("/")
async def root():
    return {"message": "SOPRIM BOT está activo 🧠", "version": "1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/test")
async def test_message(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        phone = data.get("phone", "+5212345678901")

        if not message:
            return JSONResponse(
                content={"status": "error", "message": "No se proporcionó un mensaje"},
                status_code=400
            )

        result = await message_handler.procesar_mensaje(message, phone)

        return JSONResponse(
            content={
                "status": "success",
                "message_type": result.get("message_type"),
                "response": result.get("respuesta", "Sin respuesta")
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error en test_message: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/run-scraper")
async def run_scraper_endpoint():
    """
    Endpoint para ejecutar el scraper de Difarmer manualmente.
    """
    try:
        resultado = ejecutar_scraper()
        return {"status": "ok", "resultado": resultado}
    except Exception as e:
        logger.error(f"Error al ejecutar el scraper: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
