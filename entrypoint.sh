#!/bin/bash
set -e

# Imprimir mensaje de inicio para depuración
echo "Iniciando SOPRIM BOT..."

# Verificar las variables de entorno necesarias y mostrar mensajes informativos
if [ -z "$GEMINI_API_KEY" ]; then
    echo "ADVERTENCIA: La variable GEMINI_API_KEY no está configurada"
fi

if [ -z "$WHATSAPP_TOKEN" ]; then
    echo "ADVERTENCIA: La variable WHATSAPP_TOKEN no está configurada"
fi

if [ -z "$WHATSAPP_VERIFY_TOKEN" ]; then
    echo "ADVERTENCIA: La variable WHATSAPP_VERIFY_TOKEN no está configurada"
fi

if [ -z "$WHATSAPP_PHONE_ID" ]; then
    echo "ADVERTENCIA: La variable WHATSAPP_PHONE_ID no está configurada"
fi

# Imprimir directorio actual y archivos para depuración
echo "Directorio actual: $(pwd)"
echo "Archivos en directorio:"
ls -la

# Verificar que main.py existe
if [ ! -f "main.py" ]; then
    echo "ERROR: No se encuentra el archivo main.py"
    exit 1
fi

# Asegurarse que el puerto está configurado correctamente
export PORT=${PORT:-8080}
echo "Configurando puerto: $PORT"

# Iniciar el servidor - usando exec para que uvicorn reciba las señales directamente
echo "Iniciando servidor uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT
