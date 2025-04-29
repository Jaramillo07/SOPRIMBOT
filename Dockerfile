FROM python:3.10-slim

# 1) Instalar curl y otras dependencias del sistema
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

# 2) Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub \
      | apt-key add - \
  && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
      >> /etc/apt/sources.list.d/google.list \
  && apt-get update \
  && apt-get install -y google-chrome-stable \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 3) Verificar instalación de Chrome
RUN google-chrome --version

# 4) Instalar ChromeDriver dinámicamente según la versión de Chrome
RUN set -eux; \
    CHROME_MAJOR=$(dpkg-query --showformat='${Version}' --show google-chrome-stable | cut -d. -f1); \
    echo "Chrome major version: ${CHROME_MAJOR}"; \
    CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}"); \
    echo "Matching ChromeDriver version: ${CHROMEDRIVER_VERSION}"; \
    wget -qO /tmp/chromedriver_linux64.zip \
      "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"; \
    unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/; \
    chmod +x /usr/local/bin/chromedriver; \
    rm /tmp/chromedriver_linux64.zip

# 5) Definir directorio de trabajo
WORKDIR /app

# 6) Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7) Copiar el resto del código de la aplicación
COPY . .

# 8) Variables de entorno para Chrome sin interfaz gráfica
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROME_ARGS="--no-sandbox --headless --disable-gpu --disable-dev-shm-usage"

# 9) Exponer el puerto de FastAPI
EXPOSE 8080

# 10) Entrypoint
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
