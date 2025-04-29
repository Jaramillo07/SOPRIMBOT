FROM python:3.10-slim

# Instalar curl y otras dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
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
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
     >> /etc/apt/sources.list.d/google.list \
  && apt-get update \
  && apt-get install -y google-chrome-stable \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Verificar que Chrome está instalado y obtener su versión
RUN google-chrome --version

# ── Nuevo bloque dinámico para ChromeDriver ───────────────────────────────────
RUN set -eux; \
    # Extrae la versión mayor de Chrome (p.ej. 135 de "Google Chrome 135.0.####.##") \
    CHROME_MAJOR=$(google-chrome --version | awk '{print $3}' | cut -d. -f1); \
    echo "Chrome major version: $CHROME_MAJOR"; \
    # Descarga la última versión de ChromeDriver compatible con esa major \
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}"); \
    echo "Matching ChromeDriver version: $CHROMEDRIVER_VERSION"; \
    wget -q -O /tmp/chromedriver.zip \
      "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"; \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/; \
    chmod +x /usr/local/bin/chromedriver; \
    rm /tmp/chromedriver.zip
# ───────────────────────────────────────────────────────────────────────────────

# Configurar directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Configurar variables de entorno para Chrome sin interfaz gráfica
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROME_PATH=/usr/lib/chromium/ \
    CHROME_ARGS="--no-sandbox --headless --disable-gpu --disable-dev-shm-usage"

# Puerto para FastAPI
EXPOSE 8080

# Script de inicio
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
