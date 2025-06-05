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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ✅ CORREGIDO: Instalar Chrome versión estable específica
# Método más robusto que funciona siempre
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable=114.* || \
       apt-get install -y google-chrome-stable=113.* || \
       apt-get install -y google-chrome-stable=112.* || \
       apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ✅ PREVENIR auto-updates de Chrome
RUN apt-mark hold google-chrome-stable

# ✅ VERIFICAR instalación de Chrome
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

# ✅ ChromeDriver se instalará automáticamente por webdriver-manager o Selenium 4
# No necesitamos instalarlo manualmente

# Copiar código de la aplicación
COPY . .

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

# ✅ VARIABLES DE ENTORNO
ENV CHROME_STABLE=true
ENV CHROMEDRIVER_AUTO=true

# Exponer puerto
ENV PORT=8080
EXPOSE $PORT

# Definir el punto de entrada
ENTRYPOINT ["./entrypoint.sh"]FROM python:3.10-slim

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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ✅ CORREGIDO: Instalar Chrome versión específica estable (NO la más reciente)
# Usar Chrome 114 que es muy estable y compatible con Selenium
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb \
    && dpkg -i google-chrome-stable_114.0.5735.90-1_amd64.deb || apt-get install -f -y \
    && apt-get install -f -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm google-chrome-stable_114.0.5735.90-1_amd64.deb

# ✅ PREVENIR auto-updates de Chrome
RUN apt-mark hold google-chrome-stable

# ✅ VERIFICAR instalación de Chrome
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

# ✅ INSTALAR ChromeDriver versión compatible con Chrome 114
RUN wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# ✅ VERIFICAR instalación de ChromeDriver
RUN chromedriver --version

# Copiar código de la aplicación
COPY . .

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

# ✅ VARIABLES DE ENTORNO para versiones fijas
ENV CHROME_VERSION=114.0.5735.90
ENV CHROMEDRIVER_VERSION=114.0.5735.90

# Exponer puerto
ENV PORT=8080
EXPOSE $PORT

# Definir el punto de entrada
ENTRYPOINT ["./entrypoint.sh"]
