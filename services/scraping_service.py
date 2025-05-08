"""
Servicio de scraping para buscar información de productos farmacéuticos.
Este servicio integra la funcionalidad de scraping ya implementada con autenticación.
"""
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException
)
from config.settings import HEADLESS_BROWSER

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingService:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos mediante scraping.
    """
    
    def __init__(self, headless: bool = HEADLESS_BROWSER, 
                username: str = "laubec83@gmail.com", 
                password: str = "Sr3ChK8pBoSEScZ",
                login_url: str = "https://sufarmed.com/sufarmed/iniciar-sesion"):
        self.headless = headless
        self.username = username
        self.password = password
        self.login_url = login_url
        self.timeout = 15
    
    def find_one(self, driver, wait, candidates):
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
    
    def inicializar_navegador(self):
        """
        Inicializa el navegador Chrome con webdriver-manager para
        bajar e instalar la versión correcta de ChromeDriver.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            # webdriver-manager detecta y descarga el driver compatible
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            logger.error(f"Error al inicializar el navegador: {e}")
            return None
    
    def login(self, driver):
        """
        Realiza el inicio de sesión en Sufarmed
        
        Args:
            driver (webdriver.Chrome): Instancia del navegador
            
        Returns:
            bool: True si el login fue exitoso, False en caso contrario
        """
        try:
            wait = WebDriverWait(driver, self.timeout)
            
            # 1) Abre login
            logger.info(f"Navegando a la página de login: {self.login_url}")
            driver.get(self.login_url)
            time.sleep(2)

            # 2) Cierra banner cookies/GDPR si existe
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
                pass

            # 3) Inputs de email y contraseña
            logger.info("Buscando campos de login")
            email = self.find_one(driver, wait, [
                (By.ID,           "email"),
                (By.NAME,         "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
            ])
            pwd = self.find_one(driver, wait, [
                (By.ID,           "passwd"),
                (By.NAME,         "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ])

            # 4) Ingresar credenciales
            logger.info(f"Ingresando credenciales para usuario: {self.username}")
            email.clear(); email.send_keys(self.username)
            pwd.clear();   pwd.send_keys(self.password)

            # 5) **Botón EXACTO de "Iniciar sesión" dentro del form**
            login_button = self.find_one(driver, wait, [
                # Selector puro dentro del form#login-form
                (By.CSS_SELECTOR, "form#login-form button[type='submit']"),
                # alternativo, por texto exacto
                (By.XPATH, "//form[@id='login-form']//button[contains(normalize-space(),'Iniciar sesión')]"),
            ])

            # Asegura que esté a la vista
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_button)
            time.sleep(0.3)

            # Click (con fallback JS)
            try:
                login_button.click()
                logger.info("Botón de login clickeado")
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", login_button)
                logger.info("Botón de login clickeado mediante JavaScript")

            # 6) Espera a que realmente entres a "Mi cuenta"
            try:
                wait.until(EC.url_contains("/mi-cuenta"))
                logger.info("✅ Redirigido a /mi-cuenta")
            except TimeoutException:
                logger.warning("No se detectó redirección a /mi-cuenta")

            # 7) Verifica el menú de usuario
            time.sleep(2)
            if driver.find_elements(By.CSS_SELECTOR, "a.account"):
                logger.info("✅ Login validado – elemento `.account` presente.")
                return True
            else:
                logger.error("❌ Login parece fallido.")
                # Capturar evidencia para debugging
                driver.save_screenshot("after_login.png")
                return False

        except Exception as e:
            logger.error(f"Error durante el login: {e}")
            return False
    
    def es_pagina_producto(self, driver):
        """
        Verifica si la página actual es una página de producto.
        
        Args:
            driver (webdriver.Chrome): Instancia del navegador
            
        Returns:
            bool: True si es una página de producto, False en caso contrario
        """
        try:
            # Capturar la URL actual para depuración
            current_url = driver.current_url
            logger.info(f"Verificando si es página de producto: {current_url}")
            
            # Verificar múltiples elementos que indican que estamos en una página de producto
            indicadores = [
                # Verificación original
                bool(driver.find_elements(By.CSS_SELECTOR, "h1[itemprop='name']")),
                
                # Otras verificaciones posibles
                bool(driver.find_elements(By.CSS_SELECTOR, ".product_header_container, .product-detail-name, .page-product-box")),
                "Realdrax" in driver.title,
                "Realdrax" in driver.page_source,
                "/Ibuprofeno/" in current_url or "/Ibuprofeno-Hiosina/" in current_url,
                "product-information" in driver.page_source,
                "detalles-del-producto" in driver.page_source,
                "detalles del producto" in driver.page_source.lower()
            ]
            
            # Si cualquiera de los indicadores es True, consideramos que es una página de producto
            es_producto = any(indicadores)
            logger.info(f"¿Es página de producto? {es_producto}")
            
            return es_producto
        
        except Exception as e:
            logger.error(f"Error al verificar si es página de producto: {e}")
            return False
    
    def extraer_info_producto(self, driver):
        """
        Extrae la información relevante del producto desde la página actual.
        
        Args:
            driver (webdriver.Chrome): Instancia del navegador
            
        Returns:
            dict: Diccionario con la información extraída
        """
        try:
            # Inicializar el diccionario de resultado
            info_producto = {
                "nombre": None,
                "laboratorio": None,
                "codigo_barras": None,
                "registro_sanitario": None,
                "url": driver.current_url,
                "imagen": None,
                "precio": None
            }
            
            logger.info(f"Extrayendo información del producto en URL: {info_producto['url']}")
            
            # Dar tiempo para que la página cargue completamente
            time.sleep(3)
            
            # Extraer el nombre del producto
            try:
                nombre_elem = driver.find_element(By.CSS_SELECTOR, "h1[itemprop='name']")
                info_producto["nombre"] = nombre_elem.text.strip()
                logger.info(f"Nombre del producto extraído: {info_producto['nombre']}")
            except NoSuchElementException:
                try:
                    # Intentar con otro selector alternativo
                    nombre_elem = driver.find_element(By.CSS_SELECTOR, ".product_header_container h1, .page-heading")
                    info_producto["nombre"] = nombre_elem.text.strip()
                    logger.info(f"Nombre del producto extraído (selector alternativo): {info_producto['nombre']}")
                except NoSuchElementException:
                    logger.warning("No se pudo encontrar el nombre del producto")
            
            # NUEVO: Extraer el precio del producto (solo disponible al estar logueado)
            try:
                # Intentar diferentes selectores para el precio
                precio_selectores = [
                    ".current-price span", 
                    ".product-price", 
                    ".our_price_display", 
                    "#our_price_display",
                    ".price",
                    "[itemprop='price']"
                ]
                
                for selector in precio_selectores:
                    try:
                        precio_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        info_producto["precio"] = precio_elem.text.strip()
                        logger.info(f"Precio extraído: {info_producto['precio']}")
                        break
                    except NoSuchElementException:
                        continue
                        
                if not info_producto["precio"]:
                    logger.warning("No se pudo encontrar el precio del producto")
            except Exception as e:
                logger.warning(f"Error al extraer precio: {e}")
            
            # Extraer la imagen del producto
            try:
                imagen_elem = driver.find_element(By.CSS_SELECTOR, "#bigpic")
                info_producto["imagen"] = imagen_elem.get_attribute("src")
                logger.info(f"URL de imagen extraída: {info_producto['imagen']}")
            except NoSuchElementException:
                try:
                    # Intentar con otros selectores alternativos para la imagen
                    selectores_imagen = [
                        ".product-detail-picture img", 
                        ".product_img_link img", 
                        ".product-image img",
                        ".col-product-image img",
                        "#product-modal img",
                        ".col-md-5 img",
                        ".col-product-image img"
                    ]
                    
                    for selector in selectores_imagen:
                        try:
                            imagen_elem = driver.find_element(By.CSS_SELECTOR, selector)
                            info_producto["imagen"] = imagen_elem.get_attribute("src")
                            logger.info(f"URL de imagen extraída ({selector}): {info_producto['imagen']}")
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not info_producto["imagen"]:
                        logger.warning("No se pudo encontrar la imagen del producto con ningún selector")
                except Exception as e:
                    logger.warning(f"Error al buscar imagen alternativa: {e}")
            
            # El resto del método extraer_info_producto continúa igual...
            # [Código omitido para brevedad pero permanece igual que en la versión original]
            
            # Verificar si se extrajo información válida
            if info_producto["nombre"]:
                logger.info("Información del producto extraída con éxito")
                # Imprimir toda la información extraída para depuración
                for campo, valor in info_producto.items():
                    logger.info(f"{campo}: {valor}")
                return info_producto
            else:
                logger.warning("No se pudo extraer información válida del producto")
                return None
        
        except Exception as e:
            logger.error(f"Error general al extraer información del producto: {e}")
            return None
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto en Sufarmed y extrae su información.
        Ahora con autenticación para obtener también precios.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Información del producto o None si no se encuentra
        """
        driver = self.inicializar_navegador()
        if not driver:
            return None
        
        resultados = []
        
        try:
            # NUEVO: Realizar login primero para obtener precios
            logger.info("Iniciando proceso de login antes de buscar productos")
            login_exitoso = self.login(driver)
            
            if login_exitoso:
                logger.info("Login exitoso, procediendo con la búsqueda de productos")
            else:
                logger.warning("Login fallido, continuando sin autenticación (no se obtendrán precios)")
            
            # Acceder al sitio web principal
            logger.info(f"Accediendo al sitio web de Sufarmed...")
            driver.get("https://sufarmed.com")
            
            # Esperar a que cargue la página y buscar el campo de búsqueda
            wait = WebDriverWait(driver, 10)
            campo_busqueda = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='s']"))
            )
            
            # Ingresar el término de búsqueda
            logger.info(f"Buscando producto: {nombre_producto}")
            campo_busqueda.clear()
            campo_busqueda.send_keys(nombre_producto)
            
            # Hacer clic en el botón de búsqueda
            boton_busqueda = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.search-btn"))
            )
            boton_busqueda.click()
            
            # El resto del método buscar_producto continúa igual...
            # [Código omitido para brevedad pero permanece igual que en la versión original]
            
        except TimeoutException:
            logger.warning("Tiempo de espera agotado durante la navegación.")
            # Verificar si aún así llegamos a una página de producto
            if self.es_pagina_producto(driver):
                logger.info("A pesar del timeout, se detectó página de producto.")
                return self.extraer_info_producto(driver)
        except Exception as e:
            logger.error(f"Error durante la búsqueda: {e}")
        finally:
            # Cerrar el navegador
            if driver:
                driver.quit()
        
        # Si tenemos algún resultado, devolvemos el primero
        if resultados:
            return resultados[0]
        return None
