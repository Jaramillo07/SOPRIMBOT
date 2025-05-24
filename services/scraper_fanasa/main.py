#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
USERNAME = "ventas@insumosjip.com"  # Usuario para FANASA
PASSWORD = "210407"                # Contraseña para FANASA
LOGIN_URL = "https://carrito.fanasa.com/login"  # URL correcta del portal de carrito
TIMEOUT = 20                       # Tiempo de espera para elementos (segundos) - AUMENTADO A 20
LOGIN_TIMEOUT = 20                 # Timeout específico para login (segundos)

def inicializar_navegador(headless=True):
    """
    Inicializa el navegador Chrome con opciones configuradas.
    
    Args:
        headless (bool): Si es True, el navegador se ejecuta en modo headless (sin interfaz gráfica)
        
    Returns:
        webdriver.Chrome: Instancia del navegador
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    # Configuración adicional para mejorar la estabilidad
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Ignorar errores de certificado SSL
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-insecure-localhost")
    
    # Reducir el nivel de logging para evitar mostrar errores SSL
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Configurar timeouts más agresivos
    options.add_argument("--timeout=20")
    options.add_argument("--page-load-strategy=none")  # No esperar a que cargue todo
    
    try:
        # Inicializar el navegador Chrome
        driver = webdriver.Chrome(options=options)
        
        # Configurar timeouts del driver
        driver.set_page_load_timeout(LOGIN_TIMEOUT)
        driver.implicitly_wait(5)  # Timeout implícito más corto
        
        logger.info("Navegador Chrome inicializado correctamente")
        return driver
    except Exception as e:
        logger.error(f"Error al inicializar el navegador: {e}")
        return None

def login_fanasa_carrito():
    """
    Realiza el proceso de login en el portal de carrito de FANASA.
    CON TIMEOUT DE 20 SEGUNDOS - Si no responde, continúa con el proceso.
    
    Returns:
        tuple: (webdriver.Chrome, bool) - (driver, login_exitoso)
    """
    driver = inicializar_navegador(headless=True)
    if not driver:
        logger.error("No se pudo inicializar el navegador. Abortando.")
        return None, False
    
    login_exitoso = False
    
    try:
        logger.info(f"🔄 Iniciando proceso de login con timeout de {LOGIN_TIMEOUT} segundos")
        
        # Marcar tiempo de inicio
        start_time = time.time()
        
        # 1. Navegar a la página de login con timeout
        logger.info(f"Navegando a la página de login: {LOGIN_URL}")
        try:
            driver.get(LOGIN_URL)
            # Esperar máximo 10 segundos para que cargue la página
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.info("✅ Página de login cargada correctamente")
        except TimeoutException:
            logger.warning("⚠️ Timeout cargando página de login, pero continuando...")
        
        # Verificar si ya pasaron 20 segundos
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado al cargar página")
            return driver, False
        
        # Tomar captura de pantalla inicial
        try:
            driver.save_screenshot("01_fanasa_carrito_login_inicio.png")
            logger.info("Captura de pantalla guardada: 01_fanasa_carrito_login_inicio.png")
        except:
            logger.warning("No se pudo guardar captura de pantalla")
        
        # 2. Buscar campo de usuario con timeout reducido
        logger.info("🔍 Buscando campo de usuario...")
        
        username_field = None
        try:
            # Usar WebDriverWait con timeout corto
            wait_short = WebDriverWait(driver, 5)
            
            username_selectors = [
                "input[placeholder='Usuario o correo']",
                "#email",
                "input[type='email']",
                "input[type='text']:first-of-type",
                ".form-control:first-of-type"
            ]
            
            for selector in username_selectors:
                try:
                    username_field = wait_short.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Campo de usuario encontrado con selector: {selector}")
                    break
                except TimeoutException:
                    continue
                
                # Verificar timeout general
                if time.time() - start_time > LOGIN_TIMEOUT:
                    logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado buscando usuario")
                    return driver, False
            
            # Si no encontramos con selectores específicos, buscar cualquier input visible
            if not username_field:
                try:
                    all_inputs = driver.find_elements(By.TAG_NAME, "input")
                    visible_inputs = [inp for inp in all_inputs if inp.is_displayed()]
                    
                    if visible_inputs:
                        username_field = visible_inputs[0]
                        logger.info("✅ Campo de usuario encontrado como primer input visible")
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"Error buscando campo de usuario: {e}")
        
        # Verificar timeout y campo de usuario
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado")
            return driver, False
            
        if not username_field:
            logger.warning("❌ No se pudo encontrar el campo de usuario, pero continuando...")
            return driver, False
        
        # 3. Ingresar usuario
        try:
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info(f"✅ Usuario ingresado: {USERNAME}")
            time.sleep(0.5)  # Pausa corta
        except Exception as e:
            logger.warning(f"Error ingresando usuario: {e}")
            return driver, False
        
        # Verificar timeout
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado después de ingresar usuario")
            return driver, False
        
        # 4. Buscar campo de contraseña
        logger.info("🔍 Buscando campo de contraseña...")
        
        password_field = None
        try:
            password_selectors = [
                "input[placeholder='Contraseña']",
                "#password",
                "input[type='password']",
                "input.form-control[type='password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = wait_short.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Campo de contraseña encontrado con selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # Si no encontramos, buscar por tipo password
            if not password_field:
                try:
                    password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                    if password_inputs:
                        for inp in password_inputs:
                            if inp.is_displayed():
                                password_field = inp
                                logger.info("✅ Campo de contraseña encontrado por tipo 'password'")
                                break
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Error buscando campo de contraseña: {e}")
        
        # Verificar timeout y campo de contraseña
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado buscando contraseña")
            return driver, False
            
        if not password_field:
            logger.warning("❌ No se pudo encontrar el campo de contraseña, pero continuando...")
            return driver, False
        
        # 5. Ingresar contraseña
        try:
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("✅ Contraseña ingresada")
            time.sleep(0.5)  # Pausa corta
        except Exception as e:
            logger.warning(f"Error ingresando contraseña: {e}")
            return driver, False
        
        # Verificar timeout
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado después de ingresar contraseña")
            return driver, False
        
        # 6. Buscar y hacer clic en botón de login
        logger.info("🔍 Buscando botón 'Iniciar sesión'...")
        
        login_button = None
        try:
            button_selectors = [
                "button.btn-primary",
                "button[type='submit']",
                "button:contains('Iniciar sesión')",
                ".btn-primary",
                ".btn-login"
            ]
            
            for selector in button_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and "iniciar sesión" in button.text.lower():
                            login_button = button
                            logger.info(f"✅ Botón 'Iniciar sesión' encontrado con selector: {selector}")
                            break
                    if login_button:
                        break
                except:
                    continue
            
            # Si no encontramos, intentar con XPath
            if not login_button:
                try:
                    xpath_buttons = driver.find_elements(By.XPATH, 
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'iniciar sesión')]")
                    if xpath_buttons:
                        for button in xpath_buttons:
                            if button.is_displayed():
                                login_button = button
                                logger.info("✅ Botón 'Iniciar sesión' encontrado por texto")
                                break
                except:
                    pass
            
        except Exception as e:
            logger.warning(f"Error buscando botón de login: {e}")
        
        # Verificar timeout
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado buscando botón")
            return driver, False
        
        # 7. Hacer clic en el botón o enviar con Enter
        try:
            if login_button:
                try:
                    # Intentar clic normal
                    login_button.click()
                    logger.info("✅ Clic en botón 'Iniciar sesión' realizado")
                except ElementClickInterceptedException:
                    # Si hay algo interceptando el clic, intentar con JavaScript
                    driver.execute_script("arguments[0].click();", login_button)
                    logger.info("✅ Clic en botón realizado con JavaScript")
            else:
                # Si no hay botón, intentar Enter en contraseña
                logger.warning("❌ No se encontró botón. Intentando enviar formulario con Enter.")
                password_field.send_keys(Keys.RETURN)
                logger.info("✅ Formulario enviado con Enter")
            
            # Esperar un momento para que se procese
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Error al hacer clic o enviar formulario: {e}")
            return driver, False
        
        # Verificar timeout después del envío
        if time.time() - start_time > LOGIN_TIMEOUT:
            logger.warning(f"⏰ Timeout general de {LOGIN_TIMEOUT}s alcanzado después de enviar login")
            return driver, False
        
        # 8. Verificar si el login fue exitoso (con timeout reducido)
        logger.info("🔍 Verificando resultado del login...")
        
        try:
            # Esperar máximo 5 segundos para verificar el resultado
            time.sleep(2)
            
            current_url = driver.current_url
            logger.info(f"URL actual después del intento de login: {current_url}")
            
            # Verificar si ya no estamos en la página de login
            login_exitoso = "/login" not in current_url
            
            # También verificar si hay indicadores de sesión iniciada
            if not login_exitoso:
                try:
                    page_text = driver.page_source.lower()
                    success_indicators = [
                        "cerrar sesión" in page_text,
                        "logout" in page_text,
                        "mi cuenta" in page_text,
                        "carrito" in page_text and not "/login" in current_url
                    ]
                    
                    login_exitoso = any(success_indicators)
                except:
                    pass
            
            # Verificar si hay mensajes de error visibles
            has_error = False
            try:
                error_messages = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .text-danger")
                for error in error_messages:
                    if error.is_displayed():
                        has_error = True
                        logger.error(f"❌ Mensaje de error detectado: {error.text}")
                        break
            except:
                pass
            
            # Resultado final
            if login_exitoso and not has_error:
                logger.info("✅ ¡LOGIN EXITOSO EN FANASA CARRITO!")
                try:
                    driver.save_screenshot("05_fanasa_carrito_login_exitoso.png")
                except:
                    pass
                return driver, True
            else:
                logger.warning("⚠️ Login en FANASA Carrito no confirmado o falló")
                if has_error:
                    logger.error("❌ Se detectaron mensajes de error en la página")
                try:
                    driver.save_screenshot("error_login_no_confirmado.png")
                except:
                    pass
                return driver, False
                
        except Exception as e:
            logger.warning(f"Error verificando resultado del login: {e}")
            return driver, False
        
    except Exception as e:
        logger.error(f"❌ Error durante el proceso de login: {e}")
        try:
            driver.save_screenshot("error_general_login.png")
        except:
            pass
        return driver, False

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en FANASA.
    
    Args:
        driver: WebDriver con la página cargada
        nombre_producto: Nombre del producto a buscar
        
    Returns:
        bool: True si se encontraron resultados
    """
    if not driver:
        logger.error("❌ Driver no válido para búsqueda")
        return False
    
    try:
        logger.info(f"🔍 Iniciando búsqueda de producto: {nombre_producto}")
        
        # Esperar a que la página esté cargada
        time.sleep(3)
        try:
            driver.save_screenshot("pagina_principal.png")
        except:
            pass
        
        # Buscar el input de búsqueda por varios selectores posibles
        search_field = None
        search_selectors = [
            "input[placeholder*='Nombre, laboratorio']",
            "input[placeholder*='nombre']",
            "input.search_input",
            "input[name='parametro1']",
            ".search input"
        ]
        
        wait_search = WebDriverWait(driver, 10)
        
        for selector in search_selectors:
            try:
                search_field = wait_search.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.info(f"✅ Campo de búsqueda encontrado con selector: {selector}")
                break
            except TimeoutException:
                continue
        
        # Si no se encuentra con CSS, intentar con XPath
        if not search_field:
            try:
                search_field = wait_search.until(
                    EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Nombre') or contains(@placeholder, 'nombre')]"))
                )
                logger.info("✅ Campo de búsqueda encontrado con XPath")
            except TimeoutException:
                pass
        
        # Como último recurso, buscar cualquier input visible
        if not search_field:
            try:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in all_inputs:
                    if inp.is_displayed() and inp.get_attribute("type") == "text":
                        search_field = inp
                        logger.info("✅ Campo de búsqueda encontrado como input genérico")
                        break
            except:
                pass
        
        if not search_field:
            logger.error("❌ No se pudo encontrar el campo de búsqueda")
            try:
                driver.save_screenshot("error_no_campo_busqueda.png")
            except:
                pass
            return False
        
        # Resaltar el campo de búsqueda en la captura
        try:
            driver.execute_script("arguments[0].style.border='3px solid red'", search_field)
            driver.save_screenshot("campo_busqueda_encontrado.png")
        except:
            pass
        
        # Limpiar e ingresar el término de búsqueda
        search_field.clear()
        search_field.send_keys(nombre_producto)
        logger.info(f"✅ Texto '{nombre_producto}' ingresado en campo de búsqueda")
        
        # Esperar un momento y enviar búsqueda
        time.sleep(2)
        search_field.send_keys(Keys.RETURN)
        logger.info("✅ Búsqueda enviada con tecla Enter")
        
        # Esperar a que se carguen los resultados
        time.sleep(5)
        
        # Tomar captura de la página de resultados
        try:
            driver.save_screenshot("resultados_busqueda.png")
        except:
            pass
        
        # Verificar la presencia de productos en la página
        product_indicators = [
            f"//h4[contains(text(), '{nombre_producto.upper()}')]",
            "//div[contains(@class, 'card')]",
            "//div[contains(@class, 'producto')]",
            "//button[contains(text(), 'Agregar a carrito')]",
            "//div[contains(text(), 'Precio Neto')]",
            "//div[contains(text(), 'Precio Público')]"
        ]
        
        for indicator in product_indicators:
            try:
                elements = driver.find_elements(By.XPATH, indicator)
                if elements and any(e.is_displayed() for e in elements):
                    logger.info(f"✅ Productos encontrados mediante indicador: {indicator}")
                    return True
            except:
                continue
        
        # Verificar si el término aparece en la página
        if nombre_producto.lower() in driver.page_source.lower():
            logger.info("✅ El término de búsqueda aparece en la página de resultados")
            return True
        else:
            logger.warning("⚠️ No se encontraron productos que coincidan con la búsqueda")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error durante la búsqueda: {e}")
        try:
            driver.save_screenshot("error_busqueda.png")
        except:
            pass
        return False

def extraer_info_productos(driver, numero_producto=0):
    """
    Extrae información de un producto directamente desde la tarjeta en la página de resultados.
    
    Args:
        driver: WebDriver con la página de resultados cargada
        numero_producto: Índice del producto a extraer (0 para el primero)
        
    Returns:
        dict: Diccionario con la información del producto o None si hay error
    """
    if not driver:
        logger.error("❌ No se proporcionó un navegador válido")
        return None
    
    try:
        logger.info(f"🔍 Extrayendo información del producto #{numero_producto}")
        
        # Guardar página para análisis
        try:
            driver.save_screenshot(f"pagina_resultados_producto_{numero_producto}.png")
        except:
            pass
        
        # Inicializar diccionario de información
        info_producto = {
            'url': driver.current_url,
            'nombre': '',
            'precio_neto': '',
            'pmp': '',
            'precio_publico': '',
            'precio_farmacia': '',
            'sku': '',
            'codigo': '',
            'laboratorio': '',
            'disponibilidad': '',
            'imagen': ''
        }
        
        # Buscar contenedores de productos (tarjetas)
        product_cards = []
        card_selectors = [
            "//div[contains(@class, 'card')]",
            "//div[contains(@class, 'row')][.//h4]",
            "//div[contains(@class, 'producto')]",
            "//div[contains(@class, 'card-body')]",
            "//div[.//button[contains(text(), 'Agregar a carrito')]]"
        ]
        
        for selector in card_selectors:
            try:
                cards = driver.find_elements(By.XPATH, selector)
                visible_cards = [card for card in cards if card.is_displayed()]
                if visible_cards:
                    product_cards = visible_cards
                    logger.info(f"✅ Encontradas {len(product_cards)} tarjetas de productos con selector: {selector}")
                    break
            except:
                continue
        
        if not product_cards:
            logger.warning("⚠️ No se encontraron tarjetas de productos. Intentando extraer de toda la página.")
            product_card = driver.find_element(By.TAG_NAME, "body")
        else:
            # Seleccionar la tarjeta según el índice proporcionado
            if numero_producto < len(product_cards):
                product_card = product_cards[numero_producto]
                logger.info(f"✅ Seleccionando producto #{numero_producto}")
                try:
                    driver.execute_script("arguments[0].style.border='3px solid green'", product_card)
                    driver.save_screenshot(f"tarjeta_producto_{numero_producto}_seleccionada.png")
                except:
                    pass
            else:
                logger.warning(f"⚠️ Índice {numero_producto} fuera de rango. Solo hay {len(product_cards)} productos. Usando el primero.")
                product_card = product_cards[0]
        
        # Extraer NOMBRE del producto
        try:
            nombre_elements = product_card.find_elements(By.XPATH, 
                ".//h4 | .//h2 | .//h3 | .//h5[contains(@class, 'Name-product')] | .//h5[contains(@class, 'name-product')] | .//h5[contains(@class, 'mb-2')] | .//div[contains(@class, 'name-product')] | .//div[contains(@class, 'product-name')] | .//strong")
            
            for element in nombre_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    if texto and len(texto) > 5 and "regresar" not in texto.lower():
                        info_producto['nombre'] = texto
                        logger.info(f"✅ Nombre del producto: {info_producto['nombre']}")
                        break
            
            # Si no encontramos el nombre, usar texto visible más largo
            if not info_producto['nombre']:
                visible_texts = []
                all_elements = product_card.find_elements(By.XPATH, ".//*")
                for element in all_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        if texto and len(texto) > 10 and "precio" not in texto.lower() and "$" not in texto:
                            visible_texts.append((len(texto), texto))
                
                if visible_texts:
                    visible_texts.sort(reverse=True)
                    info_producto['nombre'] = visible_texts[0][1]
                    logger.info(f"✅ Nombre del producto (texto más largo): {info_producto['nombre']}")
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo nombre: {e}")
        
        # Extraer PRECIOS
        try:
            # Buscar diferentes tipos de precios
            precio_patterns = [
                ("precio_neto", "Precio Neto"),
                ("pmp", "PMP"),
                ("precio_publico", "Precio Público"),
                ("precio_farmacia", "Precio Farmacia")
            ]
            
            for precio_key, precio_label in precio_patterns:
                try:
                    precio_elements = product_card.find_elements(By.XPATH, 
                        f".//div[contains(text(), '{precio_label}')]/following-sibling::* | .//h5[contains(text(), '{precio_label}')]/following-sibling::* | .//h6[contains(text(), '{precio_label}')]")
                    
                    for element in precio_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            if not texto:
                                try:
                                    next_sibling = element.find_element(By.XPATH, "following-sibling::*")
                                    texto = next_sibling.text.strip()
                                except:
                                    continue
                            
                            precio_match = re.search(r'\$?([\d,]+\.?\d*)', texto)
                            if precio_match:
                                info_producto[precio_key] = f"${precio_match.group(1)}"
                                logger.info(f"✅ {precio_label}: {info_producto[precio_key]}")
                                break
                except Exception as e:
                    logger.warning(f"⚠️ Error extrayendo {precio_label}: {e}")
            
            # Si no encontramos precios específicos, buscar cualquier elemento con $
            if not any([info_producto['precio_neto'], info_producto['pmp'], info_producto['precio_publico'], info_producto['precio_farmacia']]):
                precio_elements = product_card.find_elements(By.XPATH, ".//*[contains(text(), '$')]")
                for element in precio_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        precio_match = re.search(r'\$?([\d,]+\.?\d*)', texto)
                        if precio_match and float(precio_match.group(1).replace(',', '')) > 0:
                            info_producto['precio_neto'] = f"${precio_match.group(1)}"
                            logger.info(f"✅ Precio encontrado (genérico): {info_producto['precio_neto']}")
                            break
                            
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo precios: {e}")
        
        # Extraer CÓDIGO / SKU
        try:
            codigo_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Código')]/following-sibling::* | .//h6[contains(text(), 'ódigo:')] | .//h6[contains(text(), 'Código')] | .//div[contains(text(), 'Código')]")
            
            for element in codigo_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    codigo_match = re.search(r'[\d]{7,}', texto)
                    if codigo_match:
                        info_producto['codigo'] = codigo_match.group(0)
                        info_producto['sku'] = codigo_match.group(0)
                        logger.info(f"✅ Código/SKU: {info_producto['codigo']}")
                        break
            
            # Si no encontramos, buscar números largos en general
            if not info_producto['codigo']:
                all_elements = product_card.find_elements(By.XPATH, ".//*")
                for element in all_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        if re.search(r'[\d]{7,}', texto) and not re.search(r'\$', texto):
                            codigo_match = re.search(r'[\d]{7,}', texto)
                            if codigo_match:
                                info_producto['codigo'] = codigo_match.group(0)
                                info_producto['sku'] = codigo_match.group(0)
                                logger.info(f"✅ Código/SKU (genérico): {info_producto['codigo']}")
                                break
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo código/SKU: {e}")
        
        # Extraer LABORATORIO
        try:
            lab_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Laboratorio')]/following-sibling::* | .//div[contains(text(), 'LABORATORIO')]")
            
            for element in lab_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    if "laboratorio:" in texto.lower():
                        lab_match = re.search(r'laboratorio:?\s*(.+)', texto, re.IGNORECASE)
                        if lab_match:
                            info_producto['laboratorio'] = lab_match.group(1).strip()
                            logger.info(f"✅ Laboratorio: {info_producto['laboratorio']}")
                            break
                    elif len(texto) > 3 and "$" not in texto:
                        info_producto['laboratorio'] = texto
                        logger.info(f"✅ Laboratorio: {info_producto['laboratorio']}")
                        break
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo laboratorio: {e}")
        
        # Extraer DISPONIBILIDAD / STOCK
        try:
            stock_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Stock')] | .//div[contains(text(), 'Existencias')] | .//div[contains(text(), 'Disponibilidad')] | .//span[contains(@class, 'cantidad')] | .//h6[contains(@class, 'stock')]")
            
            for element in stock_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    if texto:
                        stock_match = re.search(r'(\d+)\s*disponibles', texto, re.IGNORECASE)
                        if stock_match:
                            info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                            logger.info(f"✅ Disponibilidad: {info_producto['disponibilidad']}")
                            break
                        elif "stock" in texto.lower() or "existencias" in texto.lower():
                            info_producto['disponibilidad'] = texto
                            logger.info(f"✅ Disponibilidad: {info_producto['disponibilidad']}")
                            break
            
            # Si no encontramos stock específico, usar valor predeterminado
            if not info_producto['disponibilidad']:
                info_producto['disponibilidad'] = "Stock disponible"
                logger.info("✅ Usando valor predeterminado para disponibilidad")
                
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo disponibilidad: {e}")
            info_producto['disponibilidad'] = "Stock disponible"
        
        # Extraer IMAGEN del producto
        try:
            img_elements = product_card.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                if img.is_displayed():
                    src = img.get_attribute("src")
                    if src and ("http" in src) and img.size['width'] > 50 and img.size['height'] > 50:
                        info_producto['imagen'] = src
                        logger.info(f"✅ URL de imagen: {info_producto['imagen']}")
                        break
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo imagen: {e}")
        
        # Verificar información mínima
        tiene_precio = any([info_producto['precio_neto'], info_producto['precio_publico'], 
                           info_producto['precio_farmacia'], info_producto['pmp']])
        tiene_codigo = bool(info_producto['codigo'])
        
        if tiene_precio and tiene_codigo:
            # Si tenemos precios y código pero no nombre, usar un nombre genérico
            if not info_producto['nombre'] and info_producto['codigo']:
                info_producto['nombre'] = f"Producto {info_producto['codigo']}"
                logger.info(f"✅ Usando código como nombre: {info_producto['nombre']}")
            
            logger.info("✅ Información mínima del producto extraída con éxito")
            return info_producto
        else:
            logger.warning("⚠️ No se pudo extraer información mínima de precios o código")
            return info_producto
    
    except Exception as e:
        logger.error(f"❌ Error general extrayendo información: {e}")
        try:
            driver.save_screenshot("error_extraccion_general.png")
        except:
            pass
        return None

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en FANASA.
    MEJORADA con timeout de 20 segundos para login.
    
    Args:
        nombre_medicamento (str): Nombre del medicamento a buscar
        headless (bool): Si es True, el navegador se ejecuta en modo headless
        
    Returns:
        dict: Diccionario con la información del medicamento en formato compatible
    """
    driver = None
    try:
        logger.info(f"🚀 Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")
        
        # 1. Iniciar sesión en FANASA CON TIMEOUT
        driver, login_exitoso = login_fanasa_carrito()
        
        if not driver:
            logger.error("❌ No se pudo inicializar el navegador. Abortando búsqueda.")
            return {
                "error": "error_navegador", 
                "mensaje": "No se pudo inicializar el navegador",
                "estado": "error",
                "fuente": "FANASA"
            }
        
        # 2. Decidir si continuar basado en el resultado del login
        if login_exitoso:
            logger.info("✅ Sesión iniciada exitosamente en FANASA")
        else:
            logger.warning("⚠️ Login no confirmado, pero continuando con la búsqueda...")
        
        # 3. Buscar el producto independientemente del resultado del login
        logger.info(f"🔍 Buscando producto: '{nombre_medicamento}'")
        
        resultado_busqueda = buscar_producto(driver, nombre_medicamento)
        
        if not resultado_busqueda:
            logger.warning(f"❌ No se pudo encontrar o acceder al producto: '{nombre_medicamento}'")
            return {
                "nombre": nombre_medicamento,
                "mensaje": f"No se encontró información para {nombre_medicamento} en FANASA",
                "estado": "no_encontrado",
                "fuente": "FANASA",
                "disponibilidad": "No disponible",
                "existencia": "0"
            }
        
        # 4. Extraer información del producto
        logger.info("📊 Extrayendo información del producto...")
        info_producto = extraer_info_productos(driver)
        
        # Añadir la fuente para integración con el servicio principal
        if info_producto:
            info_producto['fuente'] = 'FANASA'
            info_producto['estado'] = 'encontrado'
            
            # Compatibilidad para trabajar con el servicio de orquestación
            info_producto['existencia'] = '0'
            if info_producto['disponibilidad']:
                # Extraer números de la disponibilidad si existe
                stock_match = re.search(r'(\d+)', info_producto['disponibilidad'])
                if stock_match:
                    info_producto['existencia'] = stock_match.group(1)
                elif 'disponible' in info_producto['disponibilidad'].lower():
                    info_producto['existencia'] = 'Si'
            
            # Asignar precio principal
            info_producto['precio'] = (info_producto.get('precio_neto') or 
                                     info_producto.get('precio_publico') or 
                                     info_producto.get('precio_farmacia') or 
                                     info_producto.get('pmp') or 
                                     "0")
            
            logger.info(f"✅ Producto procesado: {info_producto['nombre']} - Precio: {info_producto['precio']} - Existencia: {info_producto['existencia']}")
            return info_producto
        else:
            return {
                "nombre": nombre_medicamento,
                "mensaje": f"No se pudo extraer información para {nombre_medicamento} en FANASA",
                "estado": "error_extraccion",
                "fuente": "FANASA",
                "disponibilidad": "Desconocida",
                "existencia": "0"
            }
        
    except Exception as e:
        logger.error(f"❌ Error general durante el proceso: {e}")
        return {
            "nombre": nombre_medicamento,
            "mensaje": f"Error al buscar {nombre_medicamento}: {str(e)}",
            "estado": "error",
            "fuente": "FANASA",
            "disponibilidad": "Error",
            "existencia": "0"
        }
    finally:
        if driver:
            logger.info("🔚 Cerrando navegador...")
            try:
                driver.quit()
            except:
                pass

# Para pruebas directas del módulo
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        medicamento = " ".join(sys.argv[1:])
    else:
        medicamento = input("Ingrese el nombre del medicamento a buscar: ")
    
    resultado = buscar_info_medicamento(medicamento, headless=False)  # False para ver el navegador
    
    if resultado and resultado.get('estado') == 'encontrado':
        print("\n✅ INFORMACIÓN DEL PRODUCTO ✅")
        print(f"Nombre: {resultado['nombre']}")
        print(f"Precio: {resultado.get('precio', 'No disponible')}")
        print(f"Existencia: {resultado['existencia']}")
        print(f"Disponibilidad: {resultado.get('disponibilidad', 'No disponible')}")
        print(f"Laboratorio: {resultado.get('laboratorio', 'No disponible')}")
        print(f"Código: {resultado.get('codigo', 'No disponible')}")
        print(f"URL: {resultado.get('url', 'No disponible')}")
    else:
        print(f"\n❌ {resultado.get('mensaje', 'No se encontró información del producto')}")
        print(f"Estado: {resultado.get('estado', 'desconocido')}")
