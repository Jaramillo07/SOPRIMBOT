"""
Módulo de scraping específico para la farmacia Sufarmed.
✅ CORREGIDO: Si login falla, NO busca nada y pasa al siguiente scraper.
ACTUALIZADO: Con normalización de búsqueda específica para Sufarmed.
REGLA SUFARMED: Solo nombre del principio activo (sin formas farmacéuticas ni dosis).
REQUERIMIENTO: Login obligatorio - sin login no hay búsqueda.
"""
import logging
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException
)
from config.settings import HEADLESS_BROWSER

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ NUEVAS CONFIGURACIONES DE TIMEOUT
LOGIN_TIMEOUT_GLOBAL = 45  # Timeout global para todo el proceso de login (segundos)
MAX_LOGIN_ATTEMPTS = 2     # Máximo 2 intentos de login antes de continuar sin autenticación

def normalizar_busqueda_sufarmed(producto_nombre):
    """
    Normaliza la búsqueda para SUFARMED: solo nombre del principio activo.
    Ejemplo: "diclofenaco inyectable 75 mg" → "diclofenaco"
    
    Args:
        producto_nombre (str): Nombre completo del producto
        
    Returns:
        str: Solo el nombre del principio activo
    """
    if not producto_nombre:
        return producto_nombre
    
    # Convertir a minúsculas para procesamiento
    texto = producto_nombre.lower().strip()
    
    # Formas farmacéuticas y palabras a eliminar
    palabras_eliminar = [
        # Formas farmacéuticas
        'inyectable', 'tabletas', 'tablets', 'cápsulas', 'capsulas', 
        'jarabe', 'solución', 'solucion', 'crema', 'gel', 'ungüento',
        'gotas', 'ampolletas', 'ampollas', 'suspensión', 'suspension',
        'comprimidos', 'pastillas', 'tabs', 'cap', 'sol', 'iny',
        'ampolla', 'vial', 'frasco', 'sobre', 'tubo',
        # Concentraciones y unidades
        'mg', 'g', 'ml', 'mcg', 'ui', 'iu', '%', 'cc', 'mgs',
        # Números (cualquier número será eliminado)
    ]
    
    # Dividir en palabras
    palabras = texto.split()
    palabras_filtradas = []
    
    for palabra in palabras:
        # Eliminar números
        if re.match(r'^\d+(?:\.\d+)?$', palabra):
            continue
        # Eliminar números con unidades pegadas (ej: "75mg", "10ml")
        if re.match(r'^\d+(?:\.\d+)?(mg|g|ml|mcg|ui|iu|%|cc)$', palabra):
            continue
        # Eliminar palabras de la lista
        if palabra in palabras_eliminar:
            continue
        # Mantener solo palabras del nombre del principio activo
        palabras_filtradas.append(palabra)
    
    # Tomar solo la primera palabra significativa (el principio activo principal)
    if palabras_filtradas:
        resultado = palabras_filtradas[0]
    else:
        # Si no queda nada, usar la primera palabra original
        resultado = producto_nombre.split()[0] if producto_nombre.split() else producto_nombre
    
    logger.info(f"[SUFARMED] Normalización: '{producto_nombre}' → '{resultado}'")
    return resultado

class ScrapingService:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos
    mediante scraping en Sufarmed.
    """
    
    def __init__(self, headless: bool = HEADLESS_BROWSER,
                username: str = "laubec83@gmail.com", 
                password: str = "Sr3ChK8pBoSEScZ",
                login_url: str = "https://sufarmed.com/sufarmed/iniciar-sesion"):
        """
        Inicializa el servicio de scraping
        
        Args:
            headless (bool): Si es True, el navegador se ejecuta en modo headless
            username (str): Nombre de usuario para login
            password (str): Contraseña para login
            login_url (str): URL de la página de login
        """
        self.headless = headless
        self.username = username
        self.password = password
        self.login_url = login_url
        self.timeout = 15
        logger.info("ScrapingService para Sufarmed inicializado")
    
    def buscar_producto(self, nombre_producto: str) -> dict:
        """
        Busca un producto en Sufarmed y extrae su información.
        Método principal para compatibilidad con el servicio integrado.
        ACTUALIZADO: Con normalización específica para Sufarmed.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Información del producto o None si no se encuentra
        """
        logger.info(f"Iniciando búsqueda en Sufarmed para: '{nombre_producto}'")
        
        # ✅ NUEVO: Normalizar búsqueda para Sufarmed
        nombre_normalizado = normalizar_busqueda_sufarmed(nombre_producto)
        
        return buscar_producto_sufarmed(nombre_normalizado)

def find_one(driver, wait, candidates):
    """
    Prueba varios selectores y devuelve el primer elemento encontrado.
    candidates: [(By, selector), ...]
    """
    for by, sel in candidates:
        try:
            return wait.until(EC.presence_of_element_located((by, sel)))
        except TimeoutException:
            continue
    raise NoSuchElementException(f"No se encontró ninguno de {candidates}")

def inicializar_navegador(headless: bool = HEADLESS_BROWSER):
    """
    Inicializa el navegador Chrome de forma compatible con entornos Docker/headless.
    CORREGIDO: Evita webdriver-manager y usa Chrome directamente.
    """
    # Rutas predefinidas para entornos Docker
    chrome_binary_path = "/usr/bin/google-chrome"
    
    options = webdriver.ChromeOptions()
    
    # Configuración para entorno headless
    if headless:
        options.add_argument("--headless=new")  # Versión moderna del flag headless
    
    # Opciones críticas para entorno Docker/containerizado
    options.add_argument("--no-sandbox")  # Requerido para ejecutar Chrome en contenedor
    options.add_argument("--disable-dev-shm-usage")  # Evita problemas de memoria compartida
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # ✅ NUEVAS OPCIONES PARA EVITAR ERRORES DE CONEXIÓN
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--remote-debugging-port=9222")
    
    # Especificar la ruta al binario Chrome
    options.binary_location = chrome_binary_path
    
    try:
        # Verificar que el binario de Chrome existe
        if not os.path.exists(chrome_binary_path):
            logger.error(f"Binario de Chrome no encontrado en: {chrome_binary_path}")
            return None
        
        logger.info("🚀 Inicializando Chrome SIN webdriver-manager (directo)")
        
        # ✅ CAMBIO PRINCIPAL: NO usar webdriver-manager, usar driver del sistema
        try:
            # Método 1: Usar chromedriver del sistema directamente
            driver = webdriver.Chrome(options=options)
            logger.info("✅ Chrome inicializado con chromedriver del sistema")
        except Exception as e1:
            logger.warning(f"⚠️ Falló chromedriver del sistema: {e1}")
            
            # Método 2: Intentar con Service vacío
            try:
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                logger.info("✅ Chrome inicializado con Service vacío")
            except Exception as e2:
                logger.warning(f"⚠️ Falló Service vacío: {e2}")
                
                # Método 3: Último recurso - usar webdriver-manager con versión específica
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    # Forzar una versión estable conocida
                    service = Service(ChromeDriverManager(version="114.0.5735.90").install())
                    driver = webdriver.Chrome(service=service, options=options)
                    logger.info("✅ Chrome inicializado con webdriver-manager versión específica")
                except Exception as e3:
                    logger.error(f"❌ Todos los métodos fallaron: {e3}")
                    return None
        
        # Verificar que el navegador se inicializó correctamente
        try:
            user_agent = driver.execute_script("return navigator.userAgent")
            logger.info(f"✅ Navegador verificado - User-Agent: {user_agent[:50]}...")
        except Exception as e:
            logger.error(f"❌ Chrome inicializado pero no responde: {e}")
            try:
                driver.quit()
            except:
                pass
            return None
        
        # Establecer timeouts razonables
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        return driver
        
    except WebDriverException as e:
        logger.error(f"❌ Error específico de WebDriver al inicializar Chrome: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error general al inicializar el navegador: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def login_with_timeout(driver, username, password, login_url, timeout):
    """
    ✅ NUEVA FUNCIÓN: Realiza el inicio de sesión en Sufarmed con timeout global
    
    Args:
        driver (webdriver.Chrome): Instancia del navegador
        username (str): Nombre de usuario
        password (str): Contraseña
        login_url (str): URL de la página de login
        timeout (int): Tiempo máximo de espera por elemento
        
    Returns:
        bool: True si el login fue exitoso, False en caso contrario
    """
    start_time = time.time()
    
    try:
        wait = WebDriverWait(driver, timeout)
        
        # 1) Navegar a la página de login
        logger.info(f"⏰ Navegando a la página de login: {login_url}")
        driver.get(login_url)
        time.sleep(2)
        
        # ✅ VERIFICAR TIMEOUT GLOBAL
        if time.time() - start_time > LOGIN_TIMEOUT_GLOBAL:
            logger.warning(f"⏰ Timeout global ({LOGIN_TIMEOUT_GLOBAL}s) alcanzado al cargar página de login")
            return False

        # 2) Cerrar banner de cookies si existe
        try:
            btn = driver.find_element(
                By.CSS_SELECTOR,
                ".js-cookie-accept, .gdpr-accept, button[aria-label*='Aceptar']"
            )
            btn.click()
            logger.info("Banner de cookies cerrado")
            time.sleep(1)
        except NoSuchElementException:
            logger.info("No se encontró banner de cookies")
        
        # ✅ VERIFICAR TIMEOUT GLOBAL
        if time.time() - start_time > LOGIN_TIMEOUT_GLOBAL:
            logger.warning(f"⏰ Timeout global ({LOGIN_TIMEOUT_GLOBAL}s) alcanzado al cerrar cookies")
            return False

        # 3) Buscar campos de login
        logger.info("Buscando campos de login")
        email = find_one(driver, wait, [
            (By.ID,           "email"),
            (By.NAME,         "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
        ])
        pwd = find_one(driver, wait, [
            (By.ID,           "passwd"),
            (By.NAME,         "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ])
        
        # ✅ VERIFICAR TIMEOUT GLOBAL
        if time.time() - start_time > LOGIN_TIMEOUT_GLOBAL:
            logger.warning(f"⏰ Timeout global ({LOGIN_TIMEOUT_GLOBAL}s) alcanzado al buscar campos")
            return False

        # 4) Ingresar credenciales
        logger.info(f"Ingresando credenciales para usuario: {username}")
        email.clear()
        email.send_keys(username)
        pwd.clear()
        pwd.send_keys(password)

        # 5) Buscar botón de login
        login_button = find_one(driver, wait, [
            (By.CSS_SELECTOR, "form#login-form button[type='submit']"),
            (By.XPATH, "//form[@id='login-form']//button[contains(normalize-space(),'Iniciar sesión')]"),
        ])

        # Asegurar visibilidad y hacer clic
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_button)
        time.sleep(0.3)
        
        # ✅ VERIFICAR TIMEOUT GLOBAL
        if time.time() - start_time > LOGIN_TIMEOUT_GLOBAL:
            logger.warning(f"⏰ Timeout global ({LOGIN_TIMEOUT_GLOBAL}s) alcanzado antes del clic")
            return False

        # Clic con fallback JS
        try:
            login_button.click()
            logger.info("Botón de login clickeado")
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", login_button)
            logger.info("Botón de login clickeado mediante JavaScript")

        # 6) Esperar redirección (con timeout reducido para no exceder el global)
        tiempo_restante = LOGIN_TIMEOUT_GLOBAL - (time.time() - start_time)
        if tiempo_restante <= 0:
            logger.warning(f"⏰ Timeout global ({LOGIN_TIMEOUT_GLOBAL}s) alcanzado antes de verificar redirección")
            return False
        
        try:
            wait_redireccion = WebDriverWait(driver, min(10, tiempo_restante))
            wait_redireccion.until(EC.url_contains("/mi-cuenta"))
            logger.info("✅ Redirigido a /mi-cuenta")
        except TimeoutException:
            logger.warning("No se detectó redirección a /mi-cuenta")

        # 7) Verificar menú de usuario
        time.sleep(2)
        if driver.find_elements(By.CSS_SELECTOR, "a.account"):
            tiempo_total = time.time() - start_time
            logger.info(f"✅ Login exitoso en {tiempo_total:.1f}s – elemento `.account` presente.")
            return True
        else:
            logger.error("❌ Login parece fallido.")
            try:
                driver.save_screenshot("sufarmed_login_failed.png")
            except Exception as e:
                logger.warning(f"No se pudo guardar captura de pantalla: {e}")
            return False

    except Exception as e:
        tiempo_total = time.time() - start_time
        logger.error(f"Error durante el login después de {tiempo_total:.1f}s: {e}")
        return False

def es_pagina_producto(driver):
    """
    Verifica si la página actual es una página de producto.
    """
    try:
        # Verificar si estamos en una página de producto buscando elementos característicos
        indicadores_producto = [
            ".product-title",
            ".product-name", 
            ".product-info",
            ".product-detail",
            "h1.product",
            ".single-product"
        ]
        
        for selector in indicadores_producto:
            if driver.find_elements(By.CSS_SELECTOR, selector):
                return True
        
        # Verificar por URL
        current_url = driver.current_url.lower()
        if any(keyword in current_url for keyword in ['/producto/', '/product/', '/detalle/']):
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Error verificando si es página de producto: {e}")
        return False

def extraer_info_producto(driver):
    """
    Extrae información detallada del producto desde la página actual.
    
    Args:
        driver: Instancia del navegador
        
    Returns:
        dict: Información del producto
    """
    info_producto = {
        "nombre": None,
        "precio": None,
        "codigo": None,
        "descripcion": None,
        "existencia": None,
        "laboratorio": None,
        "registro_sanitario": None,
        "imagen": None,
        "nombre_farmacia": "Sufarmed"
    }
    
    try:
        # Extraer nombre del producto
        selectores_nombre = [
            "h1.product-title",
            "h1.product-name", 
            ".product-title",
            ".product-name",
            "h1",
            ".entry-title"
        ]
        
        for selector in selectores_nombre:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                if elemento and elemento.text.strip():
                    info_producto["nombre"] = elemento.text.strip()
                    logger.info(f"Nombre extraído: {info_producto['nombre']}")
                    break
            except NoSuchElementException:
                continue
        
        # Extraer precio
        selectores_precio = [
            ".price",
            ".product-price",
            ".precio",
            ".price-current",
            ".sale-price"
        ]
        
        for selector in selectores_precio:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                if elemento and elemento.text.strip():
                    info_producto["precio"] = elemento.text.strip()
                    logger.info(f"Precio extraído: {info_producto['precio']}")
                    break
            except NoSuchElementException:
                continue
        
        # Extraer código del producto
        selectores_codigo = [
            ".product-code",
            ".sku",
            ".codigo",
            "[data-sku]"
        ]
        
        for selector in selectores_codigo:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                if elemento:
                    codigo_text = elemento.text.strip() or elemento.get_attribute("data-sku")
                    if codigo_text:
                        info_producto["codigo"] = codigo_text
                        logger.info(f"Código extraído: {info_producto['codigo']}")
                        break
            except NoSuchElementException:
                continue
        
        # Extraer existencia/disponibilidad
        selectores_existencia = [
            ".stock",
            ".availability",
            ".existencia",
            ".disponible"
        ]
        
        for selector in selectores_existencia:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                if elemento and elemento.text.strip():
                    info_producto["existencia"] = elemento.text.strip()
                    logger.info(f"Existencia extraída: {info_producto['existencia']}")
                    break
            except NoSuchElementException:
                continue
        
        # Extraer laboratorio/fabricante
        try:
            page_text = driver.page_source.lower()
            patrones_laboratorio = ["laboratorio:", "fabricante:", "marca:"]
            for patron in patrones_laboratorio:
                if patron in page_text:
                    inicio = page_text.find(patron) + len(patron)
                    fin = page_text.find("\n", inicio)
                    if fin == -1:
                        fin = inicio + 100
                    valor = page_text[inicio:fin].strip()
                    if valor:
                        info_producto["laboratorio"] = valor[:50]  # Limitar longitud
                        logger.info(f"Laboratorio extraído: {info_producto['laboratorio']}")
                        break
        except Exception as e:
            logger.warning(f"Error extrayendo laboratorio: {e}")
        
        # Extraer registro sanitario
        try:
            page_text = driver.page_source.lower()
            patrones_registro = ["registro sanitario:", "reg. sanitario:", "no. registro:"]
            for patron in patrones_registro:
                if patron in page_text:
                    inicio = page_text.find(patron) + len(patron)
                    fin = page_text.find("\n", inicio)
                    if fin == -1:
                        fin = inicio + 50
                    valor = page_text[inicio:fin].strip()
                    if valor:
                        info_producto["registro_sanitario"] = valor
                        logger.info(f"Registro sanitario extraído: {valor}")
                        break
        except Exception as e:
            logger.warning(f"Error extrayendo registro sanitario: {e}")
        
        # Extraer imagen del producto
        try:
            selectores_imagen = [
                ".product-image img",
                ".product-photo img", 
                ".featured-image img",
                ".main-image img"
            ]
            
            for selector in selectores_imagen:
                try:
                    elemento = driver.find_element(By.CSS_SELECTOR, selector)
                    if elemento:
                        src = elemento.get_attribute("src")
                        if src and src.startswith("http"):
                            info_producto["imagen"] = src
                            logger.info(f"URL de imagen: {info_producto['imagen']}")
                            break
                except NoSuchElementException:
                    continue
        except Exception as e:
            logger.warning(f"Error extrayendo imagen: {e}")
        
        # Verificar si se extrajo información válida
        if info_producto["nombre"]:
            logger.info("✅ Información del producto extraída con éxito")
            # Imprimir información extraída para depuración
            for campo, valor in info_producto.items():
                if valor:
                    logger.info(f"{campo}: {valor}")
            return info_producto
        else:
            logger.warning("⚠️ No se pudo extraer información válida del producto")
            return None
    
    except Exception as e:
        logger.error(f"Error general al extraer información del producto: {e}")
        return None

def buscar_producto_sufarmed(nombre_producto: str) -> dict:
    """
    ✅ FUNCIÓN PRINCIPAL CORREGIDA: Busca un producto en Sufarmed con timeout global.
    Si el login falla, NO realiza búsqueda y pasa al siguiente scraper.
    
    Args:
        nombre_producto (str): Nombre del producto YA NORMALIZADO para Sufarmed
        
    Returns:
        dict: Información del producto o error si login falla
    """
    logger.info(f"🚀 Iniciando búsqueda de producto NORMALIZADO en Sufarmed: {nombre_producto}")
    
    # Configuración inicial
    headless = HEADLESS_BROWSER
    username = "laubec83@gmail.com"
    password = "Sr3ChK8pBoSEScZ"
    login_url = "https://sufarmed.com/sufarmed/iniciar-sesion"
    timeout = 15
    
    # Inicializar variables
    driver = None
    resultados = []
    login_exitoso = False
    
    try:
        # ✅ PASO 1: Inicializar el navegador
        logger.info("📱 Inicializando navegador...")
        driver = inicializar_navegador(headless)
        if not driver:
            logger.error("❌ No se pudo inicializar el navegador, abortando búsqueda")
            return {
                "error": "error_navegador",
                "mensaje": "No se pudo inicializar el navegador",
                "estado": "error",
                "fuente": "Sufarmed"
            }
        
        # Verificación de funcionalidad básica
        try:
            driver.execute_script("return navigator.userAgent")
        except Exception as e:
            logger.error(f"❌ El navegador no responde correctamente: {e}")
            if driver:
                driver.quit()
            return {
                "error": "error_navegador",
                "mensaje": "El navegador no responde correctamente",
                "estado": "error",
                "fuente": "Sufarmed"
            }
        
        # ✅ PASO 2: Intentar login con timeout global y múltiples intentos
        logger.info(f"🔐 Iniciando proceso de login (timeout global: {LOGIN_TIMEOUT_GLOBAL}s, máx. intentos: {MAX_LOGIN_ATTEMPTS})")
        
        for intento in range(1, MAX_LOGIN_ATTEMPTS + 1):
            logger.info(f"🔄 Intento de login #{intento}/{MAX_LOGIN_ATTEMPTS}")
            
            try:
                login_exitoso = login_with_timeout(driver, username, password, login_url, timeout)
                if login_exitoso:
                    logger.info(f"✅ Login exitoso en intento #{intento}")
                    break
                else:
                    logger.warning(f"⚠️ Login fallido en intento #{intento}")
                    if intento < MAX_LOGIN_ATTEMPTS:
                        logger.info("🔄 Esperando 3 segundos antes del siguiente intento...")
                        time.sleep(3)
            except Exception as e:
                logger.warning(f"⚠️ Error en intento de login #{intento}: {e}")
                if intento < MAX_LOGIN_ATTEMPTS:
                    time.sleep(3)
        
        # ✅ PASO 3: Si login falla, NO buscar nada (salir inmediatamente)
        if login_exitoso:
            logger.info("✅ Login exitoso, procediendo con la búsqueda")
        else:
            logger.warning("❌ Login fallido después de todos los intentos, ABORTANDO búsqueda en Sufarmed")
            logger.info("🔄 Continuando con el siguiente scraper...")
            return {
                "error": "login_fallido",
                "mensaje": "Login fallido en Sufarmed, no se realizó búsqueda",
                "estado": "login_requerido",
                "fuente": "Sufarmed",
                "busqueda_realizada": False
            }
        
        # ✅ PASO 4: Realizar búsqueda del producto (solo si login exitoso)
        logger.info(f"🔍 Accediendo al sitio web de Sufarmed para buscar: {nombre_producto}")
        driver.get("https://sufarmed.com")
        
        # Esperar a que cargue la página y buscar el campo de búsqueda
        wait = WebDriverWait(driver, 10)
        campo_busqueda = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='s']"))
        )
        
        # Ingresar el término de búsqueda NORMALIZADO
        logger.info(f"📝 Ingresando término de búsqueda: {nombre_producto}")
        campo_busqueda.clear()
        campo_busqueda.send_keys(nombre_producto)
        
        # Hacer clic en el botón de búsqueda
        boton_busqueda = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.search-btn"))
        )
        boton_busqueda.click()
        
        # Esperar a que carguen los resultados
        time.sleep(3)
        
        # ✅ PASO 5: Procesar resultados de búsqueda
        logger.info("📊 Procesando resultados de búsqueda...")
        
        # Extraer todos los enlaces de productos
        all_links = driver.find_elements(By.TAG_NAME, "a")
        
        # Términos de búsqueda para coincidencia
        terminos_busqueda = [t.lower() for t in nombre_producto.split()]
        logger.info(f"🎯 Términos de búsqueda: {terminos_busqueda}")
        
        # Sistema de puntuación para enlaces
        link_scores = []
        
        for link in all_links:
            try:
                href = link.get_attribute("href") or ""
                if href and not "/module/" in href.lower() and not "javascript:" in href.lower():
                    text = link.text.strip().lower()
                    if text and any(termino in text for termino in terminos_busqueda):
                        # Calcular puntuación basada en coincidencias
                        score = sum(1 for termino in terminos_busqueda if termino in text)
                        link_scores.append((score, href, text))
                        logger.info(f"🔗 Enlace encontrado (score {score}): {text[:50]}...")
            except Exception as e:
                continue
        
        # Ordenar por puntuación descendente
        link_scores.sort(key=lambda x: x[0], reverse=True)
        
        # ✅ PASO 6: Intentar extraer información de los mejores enlaces
        max_links_to_try = 3  # Limitar intentos para no alargar mucho el proceso
        
        for i, (score, href, text) in enumerate(link_scores[:max_links_to_try]):
            try:
                logger.info(f"🔍 Intentando enlace #{i+1} (score {score}): {href}")
                driver.get(href)
                time.sleep(2)
                
                # Verificar si es una página de producto
                if es_pagina_producto(driver):
                    logger.info("✅ Página de producto detectada, extrayendo información...")
                    
                    # Extraer información del producto
                    info_producto = extraer_info_producto(driver)
                    
                    if info_producto and info_producto.get("nombre"):
                        logger.info(f"✅ Información extraída exitosamente: {info_producto['nombre']}")
                        
                        # Añadir información de contexto
                        info_producto["nombre_farmacia"] = "Sufarmed"
                        info_producto["login_exitoso"] = True  # Solo llegamos aquí si login fue exitoso
                        info_producto["busqueda_normalizada"] = nombre_producto
                        
                        return info_producto
                    else:
                        logger.warning(f"⚠️ No se pudo extraer información válida del enlace #{i+1}")
                else:
                    logger.info(f"ℹ️ El enlace #{i+1} no es una página de producto")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error procesando enlace #{i+1}: {e}")
                continue
        
        # ✅ PASO 7: Si llegamos aquí el login fue exitoso pero no se encontró el producto
        logger.warning("⚠️ Login exitoso pero no se encontró información del producto")
        return {
            "error": "producto_no_encontrado",
            "mensaje": f"Producto '{nombre_producto}' no encontrado en Sufarmed (con login exitoso)",
            "estado": "no_encontrado",
            "fuente": "Sufarmed",
            "busqueda_normalizada": nombre_producto,
            "login_exitoso": True,
            "enlaces_intentados": len(link_scores)
        }
        
    except Exception as e:
        logger.error(f"❌ Error general durante la búsqueda en Sufarmed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Si el error ocurrió antes del login, indicar que se requiere login
        error_msg = "Error durante el proceso (login requerido para Sufarmed)"
        if 'login_exitoso' in locals() and login_exitoso:
            error_msg = f"Error durante la búsqueda: {str(e)}"
        
        return {
            "error": "error_general",
            "mensaje": error_msg,
            "estado": "error",
            "fuente": "Sufarmed",
            "busqueda_normalizada": nombre_producto if 'nombre_producto' in locals() else None,
            "login_requerido": True
        }
    
    finally:
        # ✅ GARANTIZAR LIMPIEZA: Cerrar navegador en todos los casos
        if driver:
            try:
                driver.quit()
                logger.info("🔚 Navegador cerrado correctamente")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando navegador: {e}")

# ✅ FUNCIÓN DE COMPATIBILIDAD PARA EL SERVICIO INTEGRADO
def buscar_producto_sufarmed_legacy(nombre_producto: str) -> dict:
    """
    Función legacy para compatibilidad con versiones anteriores.
    Redirige a la nueva función principal.
    """
    return buscar_producto_sufarmed(nombre_producto)

# ✅ COMPORTAMIENTO SIMPLIFICADO:
# 1. Intenta login con timeout de 45s máximo (2 intentos)
# 2. Si login exitoso → busca producto y extrae información
# 3. Si login falla → NO busca nada, retorna error y continúa con siguiente scraper
# 4. Limpieza garantizada de recursos en todos los casos
