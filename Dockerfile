FROM python:3.10-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ✅ INSTALAR CHROME 130 (versión que funciona con tu código actual)
# Descargar e instalar versión específica que NO tiene problemas con Selenium
RUN wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_130.0.6723.116-1_amd64.deb \
    && dpkg -i google-chrome-stable_130.0.6723.116-1_amd64.deb || apt-get install -f -y \
    && apt-get update && apt-get install -f -y \
    && rm google-chrome-stable_130.0.6723.116-1_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ✅ PREVENIR que Chrome se actualice automáticamente
RUN apt-mark hold google-chrome-stable

# ✅ VERIFICAR que Chrome 130 se instaló correctamente
RUN google-chrome --version

# Crear directorio de trabajo
WORKDIR /app

# Crear directorios para logs y capturas de pantalla de todos los scrapers
RUN mkdir -p /app/debug_screenshots /app/debug_logs /app/conversations

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agregar undetected-chromedriver para el scraper NADRO
# (Compatible con los demás scrapers, solo añade una dependencia nueva)
RUN pip install --no-cache-dir undetected-chromedriver==3.5.4

# Copiar código de la aplicación
COPY . .

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

# Variables de entorno
ENV PORT=8080
ENV CHROME_VERSION=130.0.6723.116

# Exponer puerto
EXPOSE $PORT

# Definir el punto de entrada
ENTRYPOINT ["./entrypoint.sh"]
