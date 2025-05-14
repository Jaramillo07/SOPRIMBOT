#!/bin/bash
set -e

echo "Iniciando SOPRIM BOT..."

# Debug de variables de entorno
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ADVERTENCIA: GEMINI_API_KEY no configurada"
fi
if [ -z "$WHATSAPP_TOKEN" ]; then
    echo "ADVERTENCIA: WHATSAPP_TOKEN no configurada"
fi
if [ -z "$WHATSAPP_VERIFY_TOKEN" ]; then
    echo "ADVERTENCIA: WHATSAPP_VERIFY_TOKEN no configurada"
fi
if [ -z "$WHATSAPP_PHONE_ID" ]; then
    echo "ADVERTENCIA: WHATSAPP_PHONE_ID no configurada"
fi

echo "Directorio actual: $(pwd)"
ls -la

if [ ! -f "main.py" ]; then
    echo "ERROR: No se encuentra main.py"
    exit 1
fi

export PORT=${PORT:-8080}
echo "Puerto configurado: $PORT"

echo "Arrancando servidor uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
