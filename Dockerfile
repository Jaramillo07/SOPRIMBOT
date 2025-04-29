FROM python:3.10-slim

WORKDIR /app

# Instalar Chrome y sus dependencias para Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oE "[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}") \
    && CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d '.' -f 1) \
    && CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION") \
    && wget "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/bin/ \
    && chmod +x /usr/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Copiar archivos de requisitos primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de los archivos del proyecto
COPY . .

# Hacer ejecutable el script de entrada
RUN chmod +x entrypoint.sh

# Exponer el puerto que usará la aplicación
EXPOSE 8080

# Comando para iniciar la aplicación
CMD ["./entrypoint.sh"]
