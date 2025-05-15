"""
Módulo de scraping específico para la farmacia Sufarmed.
Este archivo contiene la lógica de scraping para buscar productos en Sufarmed,
optimizado para extraer correctamente precios y disponibilidad.
"""
import logging
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

class ScrapingServiceSufarmed:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos en Sufarmed.
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

            # 3) Inputs de email y contraseña
            logger.info("Buscando campos de login")
            email = self.find_one(driver, wait, [
                (By.ID, "email"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
            ])
            pwd = self.find_one(driver, wait, [
                (By.ID, "passwd"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ])

            # 4) Ingresar credenciales
            logger.info(f"Ingresando credenciales para usuario: {self.username}")
            email.clear()
            email.send_keys(self.username)
            pwd.clear()
            pwd.send_keys(self.password)

            # 5) **Botón EXACTO de "Iniciar sesión" dentro del form**
            login_button = self.find_one(driver, wait, [
                (By.CSS_SELECTOR, "form#login-form button[type='submit']"),
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
                bool(driver.find_elements(By.CSS_SELECTOR, "h1[itemprop='name']")),
                bool(driver.find_elements(By.CSS_SELECTOR, ".product_header_container, .product-detail-name, .page-product-box")),
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
        Optimizado para extraer correctamente precio y disponibilidad.
        
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
                "precio": None,
                "existencia": "0",
                "disponible": False,
                "fuente": "Sufarmed"
            }
            
            logger.info(f"Extrayendo información del producto en URL: {info_producto['url']}")
            
            # Dar tiempo para que la página cargue completamente
            time.sleep(3)
            
            # Extraer el nombre del producto
            try:
                nombre_elem = driver.find_element(By.CSS_SELECTOR, "h1[itemprop='name']")
                info_producto["nombre"] = nombre_elem.text.strip()
                logger.info(f"Nombre extraído: {info_producto['nombre']}")
            except NoSuchElementException:
                try:
                    # Intentar con otro selector alternativo
                    nombre_elem = driver.find_element(By.CSS_SELECTOR, ".product_header_container h1, .page-heading")
                    info_producto["nombre"] = nombre_elem.text.strip()
                    logger.info(f"Nombre extraído (alt): {info_producto['nombre']}")
                except NoSuchElementException:
                    logger.warning("No se pudo encontrar el nombre del producto")
            
            # Extraer el precio del producto (solo disponible al estar logueado)
            try:
                # Intentar diferentes selectores para el precio
                precio_selectores = [
                    ".current-price span", 
                    ".product-price", 
                    ".our_price_display", 
                    "#our_price_display",
                    ".price",
                    "[itemprop='price']",
                    ".product-price-and-shipping span.price",
                    ".product-price .current-price",
                    ".price-container .price",
                    "#content-wrapper .current-price"
                ]
                
                for selector in precio_selectores:
                    try:
                        precio_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        precio_texto = precio_elem.text.strip()
                        # Asegurarse de que realmente es un precio
                        if any(char.isdigit() for char in precio_texto):
                            info_producto["precio"] = precio_texto
                            logger.info(f"Precio extraído: {info_producto['precio']}")
                            break
                    except NoSuchElementException:
                        continue
            except Exception as e:
                logger.warning(f"Error al extraer precio: {e}")
            
            # Extraer la imagen del producto
            try:
                imagen_elem = driver.find_element(By.CSS_SELECTOR, "#bigpic")
                info_producto["imagen"] = imagen_elem.get_attribute("src")
                logger.info(f"Imagen extraída: {info_producto['imagen']}")
            except NoSuchElementException:
                try:
                    selectores_imagen = [
                        ".product-detail-picture img", 
                        ".product_img_link img", 
                        ".product-image img"
                    ]
                    
                    for selector in selectores_imagen:
                        try:
                            imagen_elem = driver.find_element(By.CSS_SELECTOR, selector)
                            info_producto["imagen"] = imagen_elem.get_attribute("src")
                            logger.info(f"Imagen extraída ({selector}): {info_producto['imagen']}")
                            break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    logger.warning(f"Error al buscar imagen alternativa: {e}")
            
            # Verificar disponibilidad - Método principal
            try:
                disponibilidad_elementos = driver.find_elements(By.CSS_SELECTOR, 
                    ".disponible, .stock-disponible, #availability_value, .product-availability")
                
                for elem in disponibilidad_elementos:
                    texto = elem.text.strip().lower()
                    if "disponible" in texto and "no disponible" not in texto:
                        info_producto["disponible"] = True
                        info_producto["existencia"] = "1"  # Al menos hay una unidad
                        logger.info(f"Producto disponible: {texto}")
                        break
            except Exception as e:
                logger.warning(f"Error al verificar disponibilidad: {e}")
            
            # Método 2: Buscar en tablas específicas
            try:
                if not info_producto["disponible"]:
                    filas = driver.find_elements(By.CSS_SELECTOR, "table tr, .table-data-sheet tr, .data-sheet tr")
                    
                    for fila in filas:
                        try:
                            celdas = fila.find_elements(By.TAG_NAME, "td")
                            if len(celdas) >= 2:
                                clave = celdas[0].text.strip().lower()
                                valor = celdas[1].text.strip()
                                
                                # Verificar disponibilidad/existencias en tabla
                                if ("disponib" in clave or "stock" in clave or "existencia" in clave) and not info_producto["disponible"]:
                                    if any(char.isdigit() for char in valor):
                                        digits = ''.join(filter(str.isdigit, valor))
                                        if digits:
                                            info_producto["existencia"] = digits
                                            info_producto["disponible"] = int(digits) > 0
                                            logger.info(f"Existencias extraídas de tabla: {digits}")
                                    
                                    if not info_producto["disponible"] and "disponible" in valor.lower() and "no disponible" not in valor.lower():
                                        info_producto["disponible"] = True
                                        if info_producto["existencia"] == "0":
                                            info_producto["existencia"] = "1"
                                        logger.info("Producto disponible según texto de tabla")
                        except Exception:
                            continue
            except Exception as e:
                logger.warning(f"Error al buscar en tablas: {e}")
            
            # Método 3: Verificar en el texto general
            if not info_producto["disponible"]:
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                    if "en stock" in page_text or "hay disponibilidad" in page_text or "producto disponible" in page_text:
                        info_producto["disponible"] = True
                        if info_producto["existencia"] == "0":
                            info_producto["existencia"] = "1"
                        logger.info("Producto disponible según texto general")
                except Exception as e:
                    logger.warning(f"Error al verificar texto general: {e}")
            
            # Verificar si se extrajo información válida
            if info_producto["nombre"]:
                logger.info("Información del producto extraída con éxito")
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
            # Realizar login primero para obtener precios
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
            
            # Esperar un tiempo después de hacer clic para asegurar la carga
            time.sleep(2)
            
            # Extraer y almacenar todos los enlaces que contienen el nombre del producto en su href
            time.sleep(2) # Esperar a que cargue la página de resultados
            all_links = driver.find_elements(By.TAG_NAME, "a")
            
            # Dividir los términos de búsqueda para hacer una coincidencia más precisa
            terminos_busqueda = [t.lower() for t in nombre_producto.split()]
            logger.info(f"Términos de búsqueda: {terminos_busqueda}")
            
            # Sistema de puntuación para enlaces
            link_scores = []
            
            for link in all_links:
                try:
                    href = link.get_attribute("href") or ""
                    if href and not "/module/" in href.lower() and not "javascript:" in href.lower():
                        texto_link = link.text.lower()
                        url_lower = href.lower()
                        
                        # Calcular puntaje de relevancia
                        score = 0
                        
                        # Coincidencia exacta en la URL tiene prioridad máxima
                        if nombre_producto.lower() in url_lower:
                            score += 100
                            
                        # Coincidencia de todos los términos en URL
                        if all(term in url_lower for term in terminos_busqueda):
                            score += 50
                        else:
                            # Coincidencia parcial: sumar por cada término encontrado
                            for term in terminos_busqueda:
                                if term in url_lower:
                                    score += 10
                        
                        # Coincidencia en el texto visible del enlace
                        if nombre_producto.lower() in texto_link:
                            score += 30
                        elif all(term in texto_link for term in terminos_busqueda):
                            score += 20
                        else:
                            for term in terminos_busqueda:
                                if term in texto_link:
                                    score += 5
                        
                        # Solo considerar enlaces con puntaje positivo
                        if score > 0:
                            link_scores.append((href, score))
                            logger.info(f"Enlace encontrado: {href}, Texto: {texto_link}, Puntaje: {score}")
                except:
                    continue
            
            # Ordenar enlaces por puntaje (mayor a menor)
            link_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Convertir a lista de URLs
            product_links = [url for url, score in link_scores]
            
            # Eliminar duplicados preservando el orden
            product_links = list(dict.fromkeys(product_links))
            logger.info(f"Enlaces relacionados con el producto encontrados: {len(product_links)}")
            
            # Intentar navegar a cada enlace hasta encontrar una página de producto
            for url in product_links:
                try:
                    logger.info(f"Navegando a URL potencial de producto: {url}")
                    driver.get(url)
                    time.sleep(3)
                    
                    if self.es_pagina_producto(driver):
                        logger.info("Éxito! Página de producto encontrada.")
                        info_producto = self.extraer_info_producto(driver)
                        if info_producto:
                            resultados.append(info_producto)
                            
                            # Si encontramos un producto con nombre que coincide exactamente, 
                            # o contiene todos los términos de búsqueda, podemos devolverlo inmediatamente
                            nombre_producto_lower = nombre_producto.lower()
                            info_nombre_lower = info_producto["nombre"].lower() if info_producto["nombre"] else ""

                            if nombre_producto_lower == info_nombre_lower or all(term in info_nombre_lower for term in terminos_busqueda):
                                logger.info(f"Encontrado producto con coincidencia exacta: {info_producto['nombre']}")
                                return info_producto
                            
                            # Limitar a 3 resultados para no hacer la búsqueda demasiado lenta
                            if len(resultados) >= 3:
                                break
                except Exception as e:
                    logger.warning(f"Error al navegar a {url}: {e}")
            
            # Si llegamos aquí y tenemos resultados, devolvemos el primero (mejor puntuado)
            if resultados:
                logger.info(f"Retornando el mejor producto de {len(resultados)} encontrados")
                return resultados[0]
                
            # Si llegamos aquí, no encontramos una página de producto válida
            logger.warning("No se pudieron encontrar enlaces de productos válidos.")
            return None
            
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
