# Dockerfile para FastAPI + ChromeDriver en Cloud Run
FROM python:3.10-slim

# Instalar dependencias del sistema (incluye Chrome)
RUN apt-get update && apt-get install -y \
    curl wget gnupg unzip fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libxcomposite1 libxdamage1 libxfixes3 \
    libxkbcommon0 libxrandr2 xdg-utils \
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

# Instalar ChromeDriver (versión fija)
RUN CHROMEDRIVER_VERSION="114.0.5735.90" \
  && wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
  && unzip chromedriver_linux64.zip \
  && mv chromedriver /usr/local/bin/ \
  && chmod +x /usr/local/bin/chromedriver \
  && rm chromedriver_linux64.zip

# Directorio de trabajo
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Asegura permisos de ejecución en el entrypoint
RUN chmod +x entrypoint.sh

# Expone el puerto que Cloud Run usará
EXPOSE 8080

# Arranca tu script
CMD ["./entrypoint.sh"]
