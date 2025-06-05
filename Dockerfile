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

# ✅ INSTALACIÓN SIMPLE DE CHROME (sin conflictos)
RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ✅ PREVENIR auto-updates de Chrome
RUN apt-mark hold google-chrome-stable

# ✅ VERIFICAR instalación
RUN google-chrome --version

# Crear directorio de trabajo
WORKDIR /app

# Crear directorios necesarios
RUN mkdir -p /app/debug_screenshots /app/debug_logs /app/conversations

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar undetected-chromedriver para NADRO
RUN pip install --no-cache-dir undetected-chromedriver==3.5.4

# Copiar código de la aplicación
COPY . .

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

# Variables de entorno
ENV PORT=8080
ENV CHROME_STABLE=true

# Exponer puerto
EXPOSE $PORT

# Definir el punto de entrada
ENTRYPOINT ["./entrypoint.sh"]
