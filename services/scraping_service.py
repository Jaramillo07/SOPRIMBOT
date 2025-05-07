"""
Servicio de scraping para buscar información de productos farmacéuticos.
Este servicio integra la funcionalidad de scraping ya implementada,
pero ahora usa webdriver-manager para alinear ChromeDriver automáticamente
y agrega autenticación para acceder a precios de productos en Sufarmed.
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import HEADLESS_BROWSER

# Credenciales para Sufarmed
SUFARMED_URL = "https://sufarmed.com/sufarmed/iniciar-sesion?back=https%3A%2F%2Fsufarmed.com%2Fsufarmed%2F"
SUFARMED_USERNAME = "laubec83@gmail.com"
SUFARMED_PASSWORD = "Sr3ChK8pBoSEScZ"

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
    
    def __init__(self, headless: bool = HEADLESS_BROWSER):
        self.headless = headless
        self.sesion_iniciada = False
    
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
    
    def iniciar_sesion_sufarmed(self, driver):
        """
        Inicia sesión en Sufarmed para acceder a información y precios.
        
        Args:
            driver (webdriver.Chrome): Instancia del navegador
            
        Returns:
            bool: True si la sesión se inició correctamente, False en caso contrario
        """
        try:
            # Registro detallado
            logger.info("Intentando iniciar sesión en Sufarmed...")
            
            # Acceder directamente a la página principal primero
            driver.get("https://sufarmed.com")
            time.sleep(2)
            
            # Buscar botón de inicio de sesión en la página principal
            try:
                botones_login = driver.find_elements(By.CSS_SELECTOR, ".user_login, .login, a[href*='login'], a[href*='iniciar-sesion']")
                if botones_login:
                    logger.info(f"Haciendo clic en botón de login encontrado: {botones_login[0].text}")
                    botones_login[0].click()
                    time.sleep(2)
                else:
                    # Si no encuentra botón de login, ir directamente a la URL de login
                    logger.info("No se encontró botón de login, accediendo directamente a URL de login")
                    driver.get(SUFARMED_URL)
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Error al intentar encontrar botón de login: {e}")
                # Ir a la URL de login directamente
                driver.get(SUFARMED_URL)
                time.sleep(2)
            
            # Tomar captura de pantalla para depuración (opcional)
            try:
                screenshot_path = "login_page.png"
                driver.save_screenshot(screenshot_path)
                logger.info(f"Captura de pantalla guardada en {screenshot_path}")
            except Exception as e:
                logger.warning(f"No se pudo guardar captura de pantalla: {e}")
            
            # Registrar URL actual y título para depuración
            current_url = driver.current_url
            current_title = driver.title
            logger.info(f"URL actual: {current_url}")
            logger.info(f"Título de la página: {current_title}")
            
            # Esperar a que cargue la página de inicio de sesión
            wait = WebDriverWait(driver, 15)  # Aumentar tiempo de espera
            
            # Buscar campos de inicio de sesión (probar diferentes selectores)
            try:
                # Intentar primero con ID (como especificado originalmente)
                campo_email = wait.until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                logger.info("Campo de email encontrado por ID")
                campo_password = driver.find_element(By.ID, "passwd")
                logger.info("Campo de contraseña encontrado por ID")
            except Exception as e:
                logger.warning(f"No se encontraron campos por ID: {e}")
                try:
                    # Intentar con nombre o tipo
                    campo_email = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
                    )
                    logger.info("Campo de email encontrado por tipo o nombre")
                    campo_password = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    logger.info("Campo de contraseña encontrado por tipo")
                except Exception as e2:
                    logger.error(f"No se pudieron encontrar los campos de inicio de sesión: {e2}")
                    return False
            
            # Ingresar credenciales con pausa entre cada acción
            logger.info("Limpiando e ingresando credenciales...")
            campo_email.clear()
            time.sleep(0.5)
            campo_email.send_keys(SUFARMED_USERNAME)
            time.sleep(0.5)
            campo_password.clear()
            time.sleep(0.5)
            campo_password.send_keys(SUFARMED_PASSWORD)
            time.sleep(0.5)
            
            # Buscar botón de inicio de sesión (probar diferentes selectores)
            try:
                # Intentar primero con ID
                boton_login = wait.until(
                    EC.element_to_be_clickable((By.ID, "SubmitLogin"))
                )
                logger.info("Botón de login encontrado por ID")
            except Exception as e:
                logger.warning(f"No se encontró botón por ID: {e}")
                try:
                    # Intentar con otros selectores comunes
                    selectores_boton = [
                        "button[type='submit']", 
                        "input[type='submit']",
                        ".login-button", 
                        ".btn-login", 
                        ".signin-button",
                        "button.btn-primary",
                        "input.btn-primary"
                    ]
                    
                    for selector in selectores_boton:
                        try:
                            botones = driver.find_elements(By.CSS_SELECTOR, selector)
                            if botones:
                                boton_login = botones[0]
                                logger.info(f"Botón de login encontrado con selector: {selector}")
                                break
                        except:
                            continue
                    else:
                        # Si no encuentra con ningún selector, buscar por texto
                        try:
                            botones_por_texto = driver.find_elements(By.XPATH, 
                                "//button[contains(text(),'Iniciar') or contains(text(),'Login') or contains(text(),'Entrar') or contains(text(),'Acceder')] | " +
                                "//input[@value='Iniciar' or @value='Login' or @value='Entrar' or @value='Acceder']")
                            if botones_por_texto:
                                boton_login = botones_por_texto[0]
                                logger.info("Botón de login encontrado por texto")
                            else:
                                logger.error("No se pudo encontrar el botón de inicio de sesión")
                                return False
                        except Exception as e3:
                            logger.error(f"Error al buscar botón por texto: {e3}")
                            return False
                except Exception as e2:
                    logger.error(f"Error al buscar botón con selectores alternativos: {e2}")
                    return False
            
            # Hacer clic en el botón de inicio de sesión
            logger.info("Haciendo clic en botón de inicio de sesión...")
            try:
                boton_login.click()
            except Exception as e:
                logger.warning(f"Error al hacer clic directo en botón: {e}")
                try:
                    # Intentar con JavaScript si el clic directo falla
                    driver.execute_script("arguments[0].click();", boton_login)
                    logger.info("Clic realizado con JavaScript")
                except Exception as e2:
                    logger.error(f"Error al hacer clic con JavaScript: {e2}")
                    return False
            
            # Esperar más tiempo para procesar el login
            logger.info("Esperando respuesta del servidor...")
            time.sleep(5)
            
            # Verificar si hay mensajes de error en la página
            try:
                mensajes_error = driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .error-message, .form-error")
                if mensajes_error:
                    for msg in mensajes_error:
                        logger.error(f"Mensaje de error en página: {msg.text}")
                    return False
            except:
                pass
            
            # Verificar URL después del login
            current_url_after_login = driver.current_url
            logger.info(f"URL después del intento de login: {current_url_after_login}")
            
            # Verificar si hay elementos que indican inicio de sesión exitoso
            logger.info("Verificando indicadores de sesión iniciada...")
            
            # Método 1: Verificar elementos en la página
            elementos_sesion = driver.find_elements(By.CSS_SELECTOR, ".account, .logout, .user-info, .user-name, .mi-cuenta")
            
            if elementos_sesion:
                logger.info(f"Elementos de sesión encontrados: {len(elementos_sesion)}")
                self.sesion_iniciada = True
                return True
            
            # Método 2: Verificar URL
            if "my-account" in current_url_after_login or "mi-cuenta" in current_url_after_login:
                logger.info("Inicio de sesión exitoso verificado por URL")
                self.sesion_iniciada = True
                return True
            
            # Método 3: Verificar cookies de sesión
            cookies = driver.get_cookies()
            session_cookies = [c for c in cookies if 'session' in c['name'].lower()]
            if session_cookies:
                logger.info(f"Cookies de sesión encontradas: {len(session_cookies)}")
                self.sesion_iniciada = True
                return True
            
            # Si no se verificó el inicio de sesión con ningún método
            logger.warning("No se pudo verificar el inicio de sesión, pero no se detectaron errores")
            
            # En caso de duda, intentar navegar de todas formas
            self.sesion_iniciada = True
            return True
                
        except Exception as e:
            logger.error(f"Error general al iniciar sesión en Sufarmed: {str(e)}")
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
            
            # Extraer el precio si se ha iniciada la sesión
            if self.sesion_iniciada:
                try:
                    # Método 1: Extraer directamente de las meta tags (más preciso en PrestaShop)
                    try:
                        # Buscar primero meta tags de precio que son bastante estables
                        js_script = """
                        const priceMeta = document.querySelector('meta[property="product:price:amount"]');
                        if (priceMeta) return priceMeta.getAttribute('content');
                        
                        // Alternativas de meta tags si la primera falla
                        const altMetas = [
                            'meta[property="product:pretax_price:amount"]',
                            'meta[property="og:price:amount"]',
                            'meta[itemprop="price"]'
                        ];
                        
                        for (let selector of altMetas) {
                            const meta = document.querySelector(selector);
                            if (meta) return meta.getAttribute('content');
                        }
                        
                        return null;
                        """
                        precio_meta = driver.execute_script(js_script)
                        
                        if precio_meta:
                            info_producto["precio"] = precio_meta
                            logger.info(f"Precio extraído de meta tag: {info_producto['precio']}")
                            precio_encontrado = True
                        else:
                            precio_encontrado = False
                    except Exception as e:
                        logger.warning(f"Error al extraer precio desde meta tags: {e}")
                        precio_encontrado = False
                    
                    # Método 2: Selectores directos basados en la estructura de PrestaShop
                    if not precio_encontrado:
                        selectores_precio = [
                            # Selectores específicos de PrestaShop
                            ".product-price .current-price",
                            "#our_price_display",
                            ".current-price span[content]",
                            "span[itemprop='price']",
                            ".current-price .price",
                            ".product-price",
                            
                            # Selectores genéricos
                            ".current-price",
                            ".price",
                            ".product-price span",
                            "#product-price",
                            ".price-tag span",
                            ".new-price",
                            "div.price .amount", 
                            "p.price"
                        ]
                        
                        for selector in selectores_precio:
                            try:
                                precio_elem = driver.find_element(By.CSS_SELECTOR, selector)
                                
                                # Intentar obtener el precio del atributo content primero
                                precio_texto = precio_elem.get_attribute("content")
                                
                                # Si no hay atributo content, usar el texto
                                if not precio_texto:
                                    precio_texto = precio_elem.text.strip()
                                    
                                if precio_texto:
                                    # Limpiar el precio (eliminar símbolos y formateo)
                                    precio_limpio = ''.join(c for c in precio_texto if c.isdigit() or c == '.' or c == ',')
                                    # Convertir comas a puntos
                                    precio_limpio = precio_limpio.replace(',', '.')
                                    info_producto["precio"] = precio_limpio
                                    logger.info(f"Precio extraído ({selector}): {info_producto['precio']}")
                                    precio_encontrado = True
                                    break
                            except NoSuchElementException:
                                continue
                    
                    # Método 3: Buscar en el texto de la página basado en patrones
                    if not precio_encontrado:
                        try:
                            # Buscar patrones como "$XX.XX" o "XX.XX MXN" en el texto de la página
                            page_text = driver.find_element(By.TAG_NAME, "body").text
                            
                            # Patrones comunes de precios en español
                            patrones_precio = [
                                r'\$\s*(\d+[\.,]\d+)',          # $28.15
                                r'(\d+[\.,]\d+)\s*MXN',          # 28.15 MXN
                                r'precio:?\s*\$?\s*(\d+[\.,]\d+)', # precio: $28.15
                                r'(\d+[\.,]\d+)\s*pesos'         # 28.15 pesos
                            ]
                            
                            for patron in patrones_precio:
                                matches = re.findall(patron, page_text)
                                if matches:
                                    # Usar el primer match como precio
                                    precio_texto = matches[0]
                                    precio_limpio = precio_texto.replace(',', '.')
                                    info_producto["precio"] = precio_limpio
                                    logger.info(f"Precio extraído por patrón: {info_producto['precio']}")
                                    precio_encontrado = True
                                    break
                        except Exception as e:
                            logger.warning(f"Error al extraer precio del texto: {e}")
                    
                    # Método 4: Buscar precio cerca del texto "Disponible"
                    if not precio_encontrado and "Disponible" in driver.page_source:
                        try:
                            # Definir la expresión XPath en una variable
                            xpath_query = "//*[contains(text(), 'Disponible')]/following::*[contains(text(), '$') or contains(@class, 'price')]"
                            # Usar la variable en la búsqueda
                            elementos_disponible = driver.find_elements(By.XPATH, xpath_query)
                            
                            if elementos_disponible:
                                for elem in elementos_disponible[:3]:
                                    texto = elem.text.strip()
                                    if '$' in texto or 'MXN' in texto:
                                        # Extraer dígitos y puntos
                                        precio_texto = ''.join(c for c in texto if c.isdigit() or c == '.' or c == ',')
                                        precio_limpio = precio_texto.replace(',', '.')
                                        info_producto["precio"] = precio_limpio
                                        logger.info(f"Precio extraído cerca de 'Disponible': {info_producto['precio']}")
                                        precio_encontrado = True
                                        break
                        except Exception as e:
                            logger.warning(f"Error al extraer precio cerca de 'Disponible': {e}")
                    
                    if not precio_encontrado:
                        logger.warning("No se pudo encontrar el precio del producto con ningún método")
                except Exception as e:
                    logger.warning(f"Error general al extraer precio: {e}")
            
            # Cambiar a la pestaña de detalles del producto si existe
            try:
                # Encontrar y hacer clic en la pestaña de detalles
                pestanas = driver.find_elements(By.CSS_SELECTOR, "a[href='#detalles-del-producto'], a[href='#product-details'], a[data-toggle='tab']")
                detalles_clickeado = False
                for pestana in pestanas:
                    try:
                        texto_pestana = pestana.text.lower()
                        if "detalles" in texto_pestana or "características" in texto_pestana or "descripción" in texto_pestana:
                            logger.info(f"Haciendo clic en pestaña: {pestana.text}")
                            driver.execute_script("arguments[0].click();", pestana)
                            time.sleep(1)  # Pequeña pausa para que cargue el contenido
                            detalles_clickeado = True
                            break
                    except:
                        pass
                
                if not detalles_clickeado:
                    logger.info("No se encontró pestaña de detalles o no se pudo hacer clic en ella")
            except Exception as e:
                logger.warning(f"Error al intentar cambiar a la pestaña de detalles: {e}")
            
            # Método 1: Extraer información basada en estructura dt/dd como se ve en la imagen
            try:
                logger.info("Buscando información en estructura dt/dd...")
                
                # Buscar todos los dt (términos) y sus dd (definiciones) asociados
                dt_elements = driver.find_elements(By.CSS_SELECTOR, "dt.name, dt")
                
                for dt in dt_elements:
                    try:
                        # Obtener el texto del término
                        term_text = dt.text.strip().lower()
                        logger.info(f"Término encontrado: {term_text}")
                        
                        # Buscar el dd asociado (puede ser el siguiente elemento hermano)
                        dd = None
                        
                        # Método 1: Buscar el siguiente elemento hermano directamente
                        try:
                            dd = dt.find_element(By.XPATH, "./following-sibling::dd[1]")
                        except:
                            # Método 2: Buscar por JavaScript
                            try:
                                dd_script = """
                                return arguments[0].nextElementSibling;
                                """
                                dd = driver.execute_script(dd_script, dt)
                            except:
                                pass
                        
                        if dd:
                            value_text = dd.text.strip()
                            logger.info(f"Valor asociado: {value_text}")
                            
                            # Mapear los términos a nuestros campos
                            if "laboratorio" in term_text:
                                info_producto["laboratorio"] = value_text
                                logger.info(f"Laboratorio extraído: {value_text}")
                            elif ("código" in term_text and "barras" in term_text) or "código de barras" in term_text:
                                info_producto["codigo_barras"] = value_text
                                logger.info(f"Código de barras extraído: {value_text}")
                            elif "registro" in term_text and "sanitario" in term_text:
                                info_producto["registro_sanitario"] = value_text
                                logger.info(f"Registro sanitario extraído: {value_text}")
                    except Exception as e:
                        logger.warning(f"Error al procesar término dt: {e}")
            except Exception as e:
                logger.warning(f"Error al procesar estructura dt/dd: {e}")

            # Método 2: Buscar en tablas específicas
            if not (info_producto["laboratorio"] and info_producto["codigo_barras"] and info_producto["registro_sanitario"]):
                try:
                    logger.info("Buscando en tablas...")
                    # Buscar filas de tabla con información
                    filas = driver.find_elements(By.CSS_SELECTOR, "table tr, .table-data-sheet tr, .data-sheet tr")
                    
                    for fila in filas:
                        try:
                            # Obtener celdas
                            celdas = fila.find_elements(By.TAG_NAME, "td")
                            if len(celdas) >= 2:
                                clave = celdas[0].text.strip().lower()
                                valor = celdas[1].text.strip()
                                
                                # Mapear claves a nuestros campos
                                if "laboratorio" in clave and not info_producto["laboratorio"]:
                                    info_producto["laboratorio"] = valor
                                    logger.info(f"Laboratorio extraído de tabla: {valor}")
                                elif ("codigo" in clave and "barras" in clave) and not info_producto["codigo_barras"]:
                                    info_producto["codigo_barras"] = valor
                                    logger.info(f"Código de barras extraído de tabla: {valor}")
                                elif "registro" in clave and "sanitario" in clave and not info_producto["registro_sanitario"]:
                                    info_producto["registro_sanitario"] = valor
                                    logger.info(f"Registro sanitario extraído de tabla: {valor}")
                        except Exception as e:
                            logger.warning(f"Error al procesar fila de tabla: {e}")
                except Exception as e:
                    logger.warning(f"Error al buscar en tablas: {e}")
            
            # Método 3: Buscar específicamente por XPath con el texto exacto visto en la imagen
            if not (info_producto["laboratorio"] and info_producto["codigo_barras"] and info_producto["registro_sanitario"]):
                try:
                    logger.info("Buscando con XPath específicos...")
                    # Xpath para laboratorio
                    if not info_producto["laboratorio"]:
                        try:
                            lab_xpath = "//dt[contains(text(), 'Laboratorio')]/following-sibling::dd[1] | //td[contains(text(), 'Laboratorio')]/following-sibling::td[1]"
                            lab_elements = driver.find_elements(By.XPATH, lab_xpath)
                            if lab_elements:
                                info_producto["laboratorio"] = lab_elements[0].text.strip()
                                logger.info(f"Laboratorio extraído por XPath: {info_producto['laboratorio']}")
                        except Exception as e:
                            logger.warning(f"Error al buscar laboratorio por XPath: {e}")
                    
                    # Xpath para código de barras
                    if not info_producto["codigo_barras"]:
                        try:
                            barcode_xpath = "//dt[contains(text(), 'Código de barras')]/following-sibling::dd[1] | //td[contains(text(), 'Código de barras')]/following-sibling::td[1]"
                            barcode_elements = driver.find_elements(By.XPATH, barcode_xpath)
                            if barcode_elements:
                                info_producto["codigo_barras"] = barcode_elements[0].text.strip()
                                logger.info(f"Código
