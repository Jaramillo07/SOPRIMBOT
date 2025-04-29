FROM python:3.10-slim

WORKDIR /app

# 1. Instalar dependencias del sistema y Chrome
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      wget curl gnupg unzip xvfb libxi6 libgconf-2-4; \
    curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /usr/share/keyrings/google.gpg; \
    echo "deb [signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends google-chrome-stable; \
    rm -rf /var/lib/apt/lists/*

# 2. Instalar ChromeDriver de forma robusta
RUN set -eux; \
    CHROME_MAJOR=$(dpkg-query -W -f='${Version}' google-chrome-stable | cut -d. -f1); \
    CHROMEDRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}); \
    wget -qO /tmp/chromedriver_linux64.zip \
      "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"; \
    unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/; \
    chmod +x /usr/local/bin/chromedriver; \
    rm /tmp/chromedriver_linux64.zip

# 3. Variables de entorno para Selenium/Puppeteer
ENV CHROME_BIN=/usr/bin/google-chrome-stable \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    PUPPETEER_SKIP_DOWNLOAD=true

# 4. Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# 5. Instalar dependencias Python
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar código y definir comando de inicio
COPY --chown=appuser:appuser . .
CMD ["python", "app.py"]
