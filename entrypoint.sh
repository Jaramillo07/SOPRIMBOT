#!/bin/bash
set -e

# Verificar las variables de entorno necesarias
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: La variable GEMINI_API_KEY no está configurada"
    exit 1
fi

if [ -z "$WHATSAPP_TOKEN" ]; then
    echo "Error: La variable WHATSAPP_TOKEN no está configurada"
    exit 1
fi

if [ -z "$WHATSAPP_VERIFY_TOKEN" ]; then
    echo "Error: La variable WHATSAPP_VERIFY_TOKEN no está configurada"
    exit 1
fi

if [ -z "$WHATSAPP_PHONE_ID" ]; then
    echo "Error: La variable WHATSAPP_PHONE_ID no está configurada"
    exit 1
fi

# Iniciar el servidor en modo producción
echo "Iniciando SOPRIM BOT en modo producción..."
exec uvicorn main:app --host 0.0.0.0 --port 8080
