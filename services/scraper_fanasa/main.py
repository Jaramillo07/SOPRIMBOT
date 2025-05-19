#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal para el scraper de FANASA.
Proporciona funcionalidad para buscar información de productos en el portal FANASA Carrito.
"""

import time
import logging
import re
import os
import traceback
import undetected_chromedriver as uc
from functools import wraps
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
USERNAME = "ventas@insumosjip.com"  # Usuario para FANASA
PASSWORD = "210407"                # Contraseña para FANASA
LOGIN_URL = "https://carrito.fanasa.com/login"  # URL del portal de carrito
TIMEOUT = 20                       # Tiempo de espera para elementos (segundos)
MAX_RETRIES = 2                    # Número máximo de reintentos para operaciones clave

def guardar_screenshot_seguro(driver, nombre_archivo):
    """
    Guarda un screenshot solo si la variable de entorno DEBUG está establecida como "True".
    
    Args:
        driver: Instancia del navegador webdriver
        nombre_archivo: Nombre del archivo donde guardar el screenshot
    """
    if os.environ.get("DEBUG", "False") == "True":
        try:
            driver.save_screenshot(nombre_archivo)
            logger.debug(f"Screenshot guardado: {nombre_archivo}")
        except Exception as e:
            logger.warning(f"No se pudo guardar screenshot {nombre_archivo}: {e}")

def retry(max_attempts=MAX_RETRIES, delay=2):
    """
    Decorador para reintentar funciones que podrían fallar temporalmente.
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Tiempo de espera entre intentos (segundos)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, 
                        StaleElementReferenceException, WebDriverException) as e:
                    attempts += 1
                    last_exception = e
                    logger.warning(f"Intento {attempts}/{max_attempts} para {func.__name__} falló: {e}")
                    time.sleep(delay)
            
            # Si llegamos aquí, todos los intentos fallaron
            logger.error(f"Todos los reintentos para {func.__name__} fallaron con: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

def esperar_elemento(driver, locator, timeout=TIMEOUT, mensaje=None):
    """
    Espera que un elemento esté presente y visible en la página.
    
    Args:
        driver: Instancia del navegador
        locator: Tupla (By.XXX, "selector")
        timeout: Tiempo máximo de espera en segundos
        mensaje: Mensaje personalizado para el log
        
    Returns:
        WebElement o None si no se encuentra
    """
    msg = mensaje or f"elemento {locator[1]}"
    logger.info(f"Esperando {msg} (max {timeout}s)...")
    
    try:
        elemento = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
        logger.info(f"✅ {msg.capitalize()} encontrado")
        return elemento
    except TimeoutException:
        logger.warning(f"⏱️ Tiempo de espera agotado buscando {msg}")
        return None
    except Exception as e:
        logger.error(f"❌ Error buscando {msg}: {e}")
        return None

def esperar_elementos(driver, locator, timeout=TIMEOUT, mensaje=None):
    """
    Espera que elementos estén presentes en la página.
    
    Args:
        driver: Instancia del navegador
        locator: Tupla (By.XXX, "selector")
        timeout: Tiempo máximo de espera en segundos
        mensaje: Mensaje personalizado para el log
        
    Returns:
        Lista de WebElements o lista vacía si no se encuentran
    """
    msg = mensaje or f"elementos {locator[1]}"
    logger.info(f"Esperando {msg} (max {timeout}s)...")
    
    try:
        elementos = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(locator)
        )
        logger.info(f"✅ {len(elementos)} {msg} encontrados")
        return elementos
    except TimeoutException:
        logger.warning(f"⏱️ Tiempo de espera agotado buscando {msg}")
        return []
    except Exception as e:
        logger.error(f"❌ Error buscando {msg}: {e}")
        return []

def clic_seguro(driver, elemento, modo_js=False, scroll=True, mensaje=None):
    """
    Realiza un clic seguro en un elemento, con opciones para manejar casos difíciles.
    
    Args:
        driver: Instancia del navegador
        elemento: Elemento web para hacer clic
        modo_js: Si es True, usa JavaScript para hacer clic
        scroll: Si es True, hace scroll al elemento primero
        mensaje: Mensaje personalizado para el log
        
    Returns:
        bool: True si el clic fue exitoso
    """
    msg = mensaje or "elemento"
    try:
        if scroll:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elemento)
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"⚠️ No se pudo hacer scroll al {msg}: {e}")
        
        if modo_js:
            driver.execute_script("arguments[0].click();", elemento)
            logger.info(f"✅ Clic en {msg} realizado con JavaScript")
        else:
            elemento.click()
            logger.info(f"✅ Clic en {msg} realizado")
        
        return True
    except ElementClickInterceptedException:
        logger.warning(f"⚠️ Clic interceptado en {msg}. Intentando con JavaScript.")
        try:
            driver.execute_script("arguments[0].click();", elemento)
            logger.info(f"✅ Clic en {msg} realizado con JavaScript (tras intercepción)")
            return True
        except Exception as e:
            logger.error(f"❌ Error al hacer clic (JS) en {msg}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Error al hacer clic en {msg}: {e}")
        return False

def inicializar_navegador(headless=True):
    """
    Inicializa el navegador Chrome con undetected-chromedriver configurado para Cloud Run.
    
    Args:
        headless (bool): Si es True, el navegador se ejecuta en modo headless (sin interfaz gráfica)
        
    Returns:
        uc.Chrome: Instancia del navegador undetected-chromedriver
    """
    logger.info("Inicializando navegador Chrome con undetected-chromedriver...")
    
    try:
        # Configurar opciones para undetected-chromedriver
        options = uc.ChromeOptions()
        
        # Configuración para entorno headless en producción
        if headless:
            options.add_argument("--headless=new")
        
        # Flags necesarios para Cloud Run
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--window-size=1920,1080")
        
        # Configuración adicional para evitar problemas en Cloud Run
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Inicializar undetected_chromedriver
        driver = uc.Chrome(
            options=options,
            version_main=114,  # Ajustar a la versión de Chrome en tu entorno
            driver_executable_path=None,  # Autodetectar el ejecutable
            browser_executable_path=None,  # Autodetectar el navegador
            use_subprocess=True,  # Necesario para modo headless
            suppress_welcome=True  # Evitar pantallas de bienvenida
        )
        
        # Establecer timeouts más largos para evitar ReadTimeoutError
        driver.set_page_load_timeout(180)  # Timeout de 180 segundos para cargas de página
        driver.set_script_timeout(180)     # Timeout de 180 segundos para scripts
        
        # Configuración adicional
        driver.implicitly_wait(20)         # Espera implícita para elementos
        
        logger.info("✅ Navegador Chrome (undetected) inicializado correctamente")
        return driver
    except Exception as e:
        logger.error(f"❌ Error al inicializar el navegador undetected-chromedriver: {e}")
        logger.error(traceback.format_exc())
        return None

@retry(max_attempts=2, delay=3)
def login_fanasa_carrito():
    """
    Realiza el proceso de login en el portal de carrito de FANASA.
    
    Returns:
        uc.Chrome: Instancia del navegador con sesión iniciada o None si falla
    """
    driver = None
    try:
        driver = inicializar_navegador(headless=True)  # Usar True para entorno de producción
        if not driver:
            logger.error("❌ No se pudo inicializar el navegador. Abortando.")
            return None
        
        # 1. Navegar a la página de login
        logger.info(f"🌐 Navegando a la página de login: {LOGIN_URL}")
        try:
            driver.get(LOGIN_URL)
            logger.info("✅ Página de login cargada")
        except Exception as e:
            logger.error(f"❌ Error al cargar la página de login: {e}")
            driver.quit()
            return None
        
        # Esperar a que cargue completamente la página
        time.sleep(5)
        
        # 2. Buscar campo de usuario
        logger.info("🔍 Buscando campo de usuario...")
        
        username_field = None
        username_selectors = [
            "input[placeholder='Usuario o correo']",
            "#email",  # Posible ID
            "input[type='email']",
            "input[type='text']:first-of-type",
            ".form-control:first-of-type"
        ]
        
        for selector in username_selectors:
            try:
                fields = esperar_elementos(driver, (By.CSS_SELECTOR, selector), timeout=10, 
                                          mensaje=f"campo de usuario con selector '{selector}'")
                
                for field in fields:
                    if field.is_displayed():
                        username_field = field
                        logger.info(f"✅ Campo de usuario encontrado con selector: {selector}")
                        break
                if username_field:
                    break
            except Exception as e:
                logger.debug(f"⚠️ No se encontró campo de usuario con selector '{selector}': {e}")
                continue
        
        # Si no encontramos con los selectores específicos, buscar cualquier input visible
        if not username_field:
            try:
                logger.info("🔍 Buscando cualquier input visible como campo de usuario...")
                # Buscar todos los inputs visibles
                inputs = esperar_elementos(driver, (By.TAG_NAME, "input"), timeout=10,
                                          mensaje="inputs en la página")
                
                visible_inputs = []
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            visible_inputs.append(inp)
                    except:
                        pass
                
                if visible_inputs:
                    # Primer input visible probablemente sea el de usuario
                    username_field = visible_inputs[0]
                    logger.info("✅ Campo de usuario encontrado como primer input visible")
            except Exception as e:
                logger.error(f"❌ Error buscando inputs visibles: {e}")
        
        # Si no se encuentra el campo de usuario, no podemos continuar
        if not username_field:
            logger.error("❌ No se pudo encontrar el campo de usuario")
            guardar_screenshot_seguro(driver, "error_campo_usuario.png")
            driver.quit()
            return None
        
        # Limpiar e ingresar el usuario
        try:
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info(f"✅ Usuario ingresado: {USERNAME}")
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Error al ingresar usuario: {e}")
            guardar_screenshot_seguro(driver, "error_ingresar_usuario.png")
            driver.quit()
            return None
        
        # 3. Buscar campo de contraseña
        logger.info("🔍 Buscando campo de contraseña...")
        
        password_field = None
        password_selectors = [
            "input[placeholder='Contraseña']",
            "#password",  # Posible ID
            "input[type='password']",
            "input.form-control[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                fields = esperar_elementos(driver, (By.CSS_SELECTOR, selector), timeout=10,
                                          mensaje=f"campo de contraseña con selector '{selector}'")
                
                for field in fields:
                    if field.is_displayed():
                        password_field = field
                        logger.info(f"✅ Campo de contraseña encontrado con selector: {selector}")
                        break
                if password_field:
                    break
            except Exception as e:
                logger.debug(f"⚠️ No se encontró campo de contraseña con selector '{selector}': {e}")
                continue
        
        # Si no encontramos con selectores específicos, buscar por tipo password
        if not password_field:
            try:
                logger.info("🔍 Buscando por tipo 'password' como campo de contraseña...")
                password_inputs = esperar_elementos(driver, (By.CSS_SELECTOR, "input[type='password']"), 
                                                 timeout=10, mensaje="campos tipo password")
                
                for inp in password_inputs:
                    try:
                        if inp.is_displayed():
                            password_field = inp
                            logger.info("✅ Campo de contraseña encontrado por tipo 'password'")
                            break
                    except:
                        pass
            except Exception as e:
                logger.error(f"❌ Error buscando campos tipo password: {e}")
        
        # Si no se encuentra el campo de contraseña, no podemos continuar
        if not password_field:
            logger.error("❌ No se pudo encontrar el campo de contraseña")
            guardar_screenshot_seguro(driver, "error_campo_password.png")
            driver.quit()
            return None
        
        # Limpiar e ingresar la contraseña
        try:
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("✅ Contraseña ingresada")
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Error al ingresar contraseña: {e}")
            guardar_screenshot_seguro(driver, "error_ingresar_password.png")
            driver.quit()
            return None
        
        # 4. Buscar botón de inicio de sesión
        logger.info("🔍 Buscando botón 'Iniciar sesión'...")
        
        login_button = None
        button_selectors = [
            "button.btn-primary",  # Clase probable basada en la captura
            "button[type='submit']",
            ".btn-primary",
            ".btn-login"
        ]
        
        for selector in button_selectors:
            try:
                buttons = esperar_elementos(driver, (By.CSS_SELECTOR, selector), timeout=10,
                                          mensaje=f"botón de login con selector '{selector}'")
                
                for button in buttons:
                    try:
                        if button.is_displayed():
                            login_button = button
                            logger.info(f"✅ Botón 'Iniciar sesión' encontrado con selector: {selector}")
                            break
                    except:
                        pass
                if login_button:
                    break
            except Exception as e:
                logger.debug(f"⚠️ No se encontró botón de login con selector '{selector}': {e}")
                continue
        
        # Si no encontramos con CSS, intentar con XPath específico para el texto
        if not login_button:
            try:
                logger.info("🔍 Buscando botón por texto 'iniciar sesión'...")
                xpath_buttons = esperar_elementos(
                    driver, 
                    (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'iniciar sesión')]"),
                    timeout=10,
                    mensaje="botón por texto 'iniciar sesión'"
                )
                
                for button in xpath_buttons:
                    try:
                        if button.is_displayed():
                            login_button = button
                            logger.info("✅ Botón 'Iniciar sesión' encontrado por texto")
                            break
                    except:
                        pass
            except Exception as e:
                logger.error(f"❌ Error buscando botón por texto: {e}")
        
        # Si no se encuentra el botón, intentar enviar el formulario con Enter
        if not login_button:
            logger.warning("⚠️ No se encontró botón de inicio de sesión. Intentando enviar formulario con Enter.")
            try:
                password_field.send_keys(Keys.RETURN)
                logger.info("✅ Formulario enviado con tecla Enter")
                time.sleep(5)
            except Exception as e:
                logger.error(f"❌ Error al enviar formulario con Enter: {e}")
                guardar_screenshot_seguro(driver, "error_enviar_formulario.png")
                driver.quit()
                return None
        else:
            # Hacer clic en el botón
            if not clic_seguro(driver, login_button, mensaje="botón 'Iniciar sesión'"):
                logger.error("❌ No se pudo hacer clic en el botón de login")
                guardar_screenshot_seguro(driver, "error_clic_login.png")
                driver.quit()
                return None
            
            # Esperar a que se procese el login
            time.sleep(5)
        
        # 5. Verificar si el login fue exitoso
        current_url = driver.current_url
        logger.info(f"🌐 URL actual después del intento de login: {current_url}")
        
        # Verificar si ya no estamos en la página de login
        login_exitoso = "/login" not in current_url
        
        # También verificar si hay indicadores de sesión iniciada
        if not login_exitoso:
            logger.info("🔍 Verificando indicadores alternativos de sesión...")
            page_text = driver.page_source.lower()
            success_indicators = [
                "cerrar sesión" in page_text,
                "logout" in page_text,
                "mi cuenta" in page_text,
                "carrito" in page_text and not "/login" in current_url
            ]
            
            login_exitoso = any(success_indicators)
            
            if login_exitoso:
                logger.info("✅ Login exitoso detectado por indicadores secundarios")
        
        # Verificar si hay mensajes de error visibles
        has_error = False
        try:
            logger.info("🔍 Verificando mensajes de error...")
            error_messages = esperar_elementos(
                driver, 
                (By.CSS_SELECTOR, ".error, .alert-danger, .text-danger"),
                timeout=5,
                mensaje="mensajes de error"
            )
            
            for error in error_messages:
                try:
                    if error.is_displayed():
                        has_error = True
                        logger.error(f"❌ Mensaje de error detectado: {error.text}")
                        break
                except:
                    pass
        except Exception as e:
            logger.warning(f"⚠️ Error al verificar mensajes de error: {e}")
        
        # Resultado final
        if login_exitoso and not has_error:
            logger.info("🎉 ¡LOGIN EXITOSO EN FANASA CARRITO!")
            return driver
        else:
            logger.error("❌ ERROR: Login en FANASA Carrito fallido")
            
            if has_error:
                logger.error("❌ Se detectaron mensajes de error en la página")
            
            guardar_screenshot_seguro(driver, "error_login_fallido.png")
            driver.quit()
            return None
        
    except Exception as e:
        logger.error(f"❌ Error no manejado durante el proceso de login: {e}")
        logger.error(traceback.format_exc())
        if driver:
            guardar_screenshot_seguro(driver, "error_login_excepcion.png")
            driver.quit()
        return None

@retry(max_attempts=2, delay=2)
def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en FANASA usando búsqueda reactiva (sin Enter).

    Args:
        driver: WebDriver con sesión iniciada y login exitoso
        nombre_producto: texto a buscar

    Returns:
        bool: True si se detecta el producto en los resultados
    """
    if not driver:
        logger.error("❌ Driver no válido para búsqueda")
        return False

    try:
        logger.info(f"🔍 Iniciando búsqueda de producto: {nombre_producto}")
        
        # Esperar a que el campo de búsqueda esté disponible
        logger.info("⏳ Esperando que el campo de búsqueda esté disponible...")
        search_field = esperar_elemento(
            driver, 
            (By.CSS_SELECTOR, "input.search_input"), 
            timeout=20,  # Aumentado de 10 a 20 segundos para dar más tiempo
            mensaje="campo de búsqueda"
        )
        
        if not search_field:
            logger.error("❌ No se encontró el campo de búsqueda después de 20 segundos")
            guardar_screenshot_seguro(driver, "error_campo_busqueda_no_encontrado.png")
            return False

        # Asegurar que el campo esté enfocado
        try:
            logger.info("🖱️ Enfocando campo de búsqueda...")
            driver.execute_script("arguments[0].focus();", search_field)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo enfocar el campo de búsqueda: {e}")
            # Continuar de todos modos

        # Ingresar texto y disparar eventos de búsqueda reactiva
        try:
            logger.info(f"⌨️ Ingresando texto de búsqueda: '{nombre_producto}'...")
            # Método 1: Intentar con JavaScript para máxima compatibilidad
            driver.execute_script("""
                const input = arguments[0];
                input.value = arguments[1];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, search_field, nombre_producto)
            logger.info(f"✅ Texto '{nombre_producto}' ingresado y eventos disparados con JavaScript")
        except Exception as e:
            logger.warning(f"⚠️ Error al usar JavaScript para ingresar texto: {e}")
            try:
                # Método 2: Fallback a método tradicional si JavaScript falla
                search_field.clear()
                search_field.send_keys(nombre_producto)
                logger.info(f"✅ Texto '{nombre_producto}' ingresado con método tradicional")
            except Exception as e2:
                logger.error(f"❌ Error al ingresar texto de búsqueda: {e2}")
                guardar_screenshot_seguro(driver, "error_ingresar_texto_busqueda.png")
                return False

        # Esperar a que aparezcan resultados relacionados
        # Usamos la primera palabra del nombre del producto para mayor flexibilidad
        primera_palabra = nombre_producto.split()[0]
        logger.info(f"⏳ Esperando resultados que contengan '{primera_palabra}'...")
        
        try:
            WebDriverWait(driver, 20).until(  # Aumentado de 10 a 20 segundos
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{primera_palabra}')]"))
            )
            logger.info("📦 Resultados visibles tras la búsqueda reactiva")
        except TimeoutException:
            logger.warning(f"⏱️ Tiempo de espera agotado buscando resultados con '{primera_palabra}'")
            # Intentar con un XPath más general para detectar cualquier resultado de búsqueda
            try:
                logger.info("🔍 Intentando detectar cualquier resultado de búsqueda...")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results, .product-list, .product-item"))
                )
                logger.info("📦 Se detectaron posibles resultados de búsqueda generales")
            except TimeoutException:
                logger.error("❌ No se encontraron resultados de búsqueda después de 25 segundos")
                guardar_screenshot_seguro(driver, "error_no_resultados_busqueda.png")
                return False
        except Exception as e:
            logger.error(f"❌ Error inesperado al esperar resultados: {e}")
            guardar_screenshot_seguro(driver, "error_esperar_resultados.png")
            return False

        # Verificación adicional de resultados
        try:
            # Capturar una lista de elementos resultado para análisis
            resultado_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{primera_palabra}')]")
            if resultado_elements:
                logger.info(f"✅ Se encontraron {len(resultado_elements)} elementos que contienen '{primera_palabra}'")
            else:
                logger.warning("⚠️ No se encontraron elementos específicos, pero la búsqueda no falló")
        except Exception as e:
            logger.warning(f"⚠️ Error al verificar elementos de resultado: {e}")
            # No es un error crítico, continuamos

        # Captura para verificación
        guardar_screenshot_seguro(driver, "resultados_busqueda_reactiva.png")
        return True

    except Exception as e:
        logger.error(f"❌ Error no manejado durante la búsqueda reactiva: {e}")
        logger.error(traceback.format_exc())
        guardar_screenshot_seguro(driver, "error_busqueda_reactiva.png")
        return False

def extraer_info_producto(driver):
    """
    Extrae información detallada del producto de la página actual.
    Enfocado principalmente en precio y disponibilidad.
    
    Args:
        driver: Instancia del navegador con la página de detalle abierta
        
    Returns:
        dict: Diccionario con la información del producto o None si hay error
    """
    if not driver:
        logger.error("❌ No se proporcionó un navegador válido")
        return None
    
    try:
        logger.info("📊 Extrayendo información del producto...")
        # Esperar a que la página cargue completamente
        logger.info("⏳ Esperando que la página de detalle cargue completamente...")
        time.sleep(5)
        
        # Inicializar diccionario con todas las claves (incluso vacías)
        info_producto = {
            'url': driver.current_url,
            'nombre': '',
            'precio_neto': '',
            'pmp': '',
            'sku': '',
            'laboratorio': '',
            'disponibilidad': 'Stock disponible',
            'imagen': '',
            'descripcion': ''
        }

        # NOMBRE DEL PRODUCTO
        try:
            logger.info("🔍 Buscando nombre del producto...")
            nombre_selectors = [
                "h1", "h2", "h3", ".product-name", ".product-title", "h1.product-name", 
                ".name-product", "strong.name", ".product-header h1", "[itemprop='name']"
            ]
            
            for selector in nombre_selectors:
                try:
                    elements = esperar_elementos(
                        driver, 
                        (By.CSS_SELECTOR, selector), 
                        timeout=5,  # Tiempo reducido ya que es una secuencia de intentos
                        mensaje=f"elementos de nombre con selector '{selector}'"
                    )
                    
                    for element in elements:
                        try:
                            if element.is_displayed() and element.text.strip():
                                text = element.text.strip()
                                # Verificar si el texto parece un nombre de producto
                                if len(text) > 5 and not text.lower() in ["detalle", "detalle de producto"]:
                                    info_producto['nombre'] = text
                                    logger.info(f"✅ Nombre del producto: {info_producto['nombre']}")
                                    break
                        except Exception as e_inner:
                            logger.debug(f"⚠️ Error al procesar elemento de nombre: {e_inner}")
                            continue
                    if info_producto['nombre']:
                        break
                except Exception as e_selector:
                    logger.debug(f"⚠️ Selector '{selector}' falló: {e_selector}")
                    continue
                    
            if not info_producto['nombre']:
                logger.warning("⚠️ No se pudo encontrar el nombre del producto con los selectores estándar")
        except Exception as e:
            logger.warning(f"⚠️ Error general extrayendo nombre: {e}")

        # PRECIO NETO
        try:
            logger.info("🔍 Buscando precio neto...")
            
            # Estrategia 1: Buscar por texto "Precio Neto" seguido de un precio
            try:
                precio_neto_elements = esperar_elementos(
                    driver, 
                    (By.XPATH, "//*[contains(text(), 'Precio Neto')]/following::*[contains(text(), '$')]"), 
                    timeout=5,
                    mensaje="elementos de precio neto"
                )
                
                for element in precio_neto_elements:
                    try:
                        if element.is_displayed():
                            texto_precio = element.text.strip()
                            precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto_precio)
                            if precio_match:
                                info_producto['precio_neto'] = f"${precio_match.group(1)}"
                                logger.info(f"✅ Precio Neto: {info_producto['precio_neto']}")
                                break
                    except Exception as e_inner:
                        continue
            except Exception as e_strat1:
                logger.debug(f"⚠️ Estrategia 1 para precio falló: {e_strat1}")
            
            # Estrategia 2: Buscar cualquier elemento con precio si no se encontró
            if not info_producto['precio_neto']:
                try:
                    logger.info("🔍 Buscando cualquier elemento con precio...")
                    precio_elements = esperar_elementos(
                        driver, 
                        (By.XPATH, "//*[contains(text(), '$')]"), 
                        timeout=5,
                        mensaje="elementos con precio"
                    )
                    
                    for element in precio_elements:
                        try:
                            if element.is_displayed():
                                texto_precio = element.text.strip()
                                precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto_precio)
                                if precio_match and "$0" not in texto_precio and len(texto_precio) < 20:
                                    info_producto['precio_neto'] = f"${precio_match.group(1)}"
                                    logger.info(f"✅ Precio encontrado (alternativo): {info_producto['precio_neto']}")
                                    break
                        except Exception as e_inner:
                            continue
                except Exception as e_strat2:
                    logger.debug(f"⚠️ Estrategia 2 para precio falló: {e_strat2}")
                    
            if not info_producto['precio_neto']:
                logger.warning("⚠️ No se pudo encontrar el precio del producto")
        except Exception as e:
            logger.warning(f"⚠️ Error general extrayendo precio: {e}")

        # LABORATORIO / FABRICANTE
        try:
            logger.info("🔍 Buscando información de laboratorio/fabricante...")
            lab_elements = esperar_elementos(
                driver, 
                (By.XPATH, "//*[contains(text(), 'Laboratorio') or contains(text(), 'Fabricante')]/following::*"), 
                timeout=5,
                mensaje="elementos de laboratorio/fabricante"
            )
            
            for element in lab_elements:
                try:
                    if element.is_displayed() and element.text.strip():
                        texto = element.text.strip()
                        # Verificar que no sea un texto genérico o un precio
                        if len(texto) > 3 and "$" not in texto:
                            info_producto['laboratorio'] = texto
                            logger.info(f"✅ Laboratorio: {info_producto['laboratorio']}")
                            break
                except Exception as e_inner:
                    continue
                    
            if not info_producto['laboratorio']:
                logger.warning("⚠️ No se pudo encontrar información del laboratorio/fabricante")
        except Exception as e:
            logger.warning(f"⚠️ Error general extrayendo laboratorio: {e}")

        # DISPONIBILIDAD / STOCK
        try:
            logger.info("🔍 Buscando información de disponibilidad/stock...")
            # Buscar elementos que contengan explícitamente "Stock"
            stock_elements = esperar_elementos(
                driver, 
                (By.XPATH, "//*[contains(text(), 'Stock') or contains(text(), 'Disponibilidad') or contains(text(), 'Existencias')]"), 
                timeout=5,
                mensaje="elementos de stock/disponibilidad"
            )
            
            for element in stock_elements:
                try:
                    if element.is_displayed():
                        texto = element.text.strip()
                        if texto:
                            # Buscar un patrón como "Stock (366)"
                            stock_match = re.search(r'[Ss]tock\s*\((\d+)\)', texto)
                            if stock_match:
                                info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                            else:
                                # Si no sigue el patrón específico, usar el texto completo
                                info_producto['disponibilidad'] = texto
                            
                            logger.info(f"✅ Disponibilidad: {info_producto['disponibilidad']}")
                            break
                except Exception as e_inner:
                    continue
                    
            # Si no se pudo encontrar, dejamos el valor predeterminado
            if info_producto['disponibilidad'] == 'Stock disponible':
                logger.warning("⚠️ No se encontró información explícita de stock, usando valor predeterminado")
        except Exception as e:
            logger.warning(f"⚠️ Error general extrayendo disponibilidad: {e}")
        
        # Guardar una captura de la página para verificación
        guardar_screenshot_seguro(driver, "detalle_producto_extraido.png")
            
        return info_producto
            
    except Exception as e:
        logger.error(f"❌ Error general durante la extracción: {e}")
        logger.error(traceback.format_exc())
        guardar_screenshot_seguro(driver, "error_extraccion_producto.png")
        return None
            
@retry(max_attempts=2, delay=3)
def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en FANASA.
    
    Args:
        nombre_medicamento (str): Nombre del medicamento a buscar
        headless (bool): Si es True, el navegador se ejecuta en modo headless
        
    Returns:
        dict: Diccionario con la información del medicamento o diccionario con error si no se encuentra
    """
    driver = None
    try:
        # 1. Iniciar sesión en FANASA
        logger.info(f"🚀 Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")
        
        driver = login_fanasa_carrito()
        if not driver:
            mensaje_error = "No se pudo iniciar sesión en FANASA. Abortando búsqueda."
            logger.error(f"❌ {mensaje_error}")
            raise RuntimeError(mensaje_error)
        
        # 2. Buscar el producto
        logger.info(f"✅ Sesión iniciada. Buscando producto: '{nombre_medicamento}'")
        
        resultado_busqueda = buscar_producto(driver, nombre_medicamento)
        
        if not resultado_busqueda:
            logger.warning(f"⚠️ No se pudo encontrar o acceder al producto: '{nombre_medicamento}'")
            # Crear una respuesta estructurada para productos no encontrados
            return {
                "nombre": nombre_medicamento,
                "mensaje": f"No se encontró información para {nombre_medicamento} en FANASA",
                "estado": "no_encontrado",
                "fuente": "FANASA",
                "disponibilidad": "No disponible",
                "existencia": "0"
            }
        
        # 3. Extraer información del producto
        logger.info("📊 Extrayendo información del producto...")
        info_producto = extraer_info_producto(driver)
        
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
            
            logger.info(f"✅ Información extraída correctamente para: {nombre_medicamento}")
            return info_producto
        else:
            # Si no se pudo extraer información, lanzar ValueError
            mensaje_error = f"No se pudo extraer información para {nombre_medicamento} en FANASA"
            logger.error(f"❌ {mensaje_error}")
            raise ValueError(mensaje_error)
        
    except RuntimeError as e:
        logger.exception(f"❌ Error en login: {str(e)}")
        return {
            "nombre": nombre_medicamento,
            "mensaje": str(e),
            "estado": "error",
            "fuente": "FANASA",
            "disponibilidad": "Error",
            "existencia": "0"
        }
    except ValueError as e:
        logger.exception(f"❌ Error en extracción: {str(e)}")
        return {
            "nombre": nombre_medicamento,
            "mensaje": str(e),
            "estado": "error_extraccion",
            "fuente": "FANASA",
            "disponibilidad": "Desconocida",
            "existencia": "0"
        }
    except Exception as e:
        logger.exception(f"❌ Error general durante el proceso: {str(e)}")
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
            logger.info("🔒 Cerrando navegador...")
            try:
                driver.quit()
                logger.info("✅ Navegador cerrado correctamente")
            except Exception as e:
                logger.exception(f"⚠️ Error al cerrar el navegador: {str(e)}")

# Para ejecución directa como script independiente
if __name__ == "__main__":
    import sys
    import json
    
    print("=== Sistema de Búsqueda de Medicamentos en FANASA ===")
    
    # Si se proporciona un argumento por línea de comandos, usarlo como nombre del medicamento
    if len(sys.argv) > 1:
        medicamento = " ".join(sys.argv[1:])
    else:
        # De lo contrario, pedir al usuario
        medicamento = input("Ingrese el nombre del medicamento a buscar: ")
    
    print(f"\nBuscando información sobre: {medicamento}")
    print("Espere un momento...\n")
    
    # Buscar información del medicamento
    info = buscar_info_medicamento(medicamento)
    
    # Verificar el estado del resultado
    estado = info.get('estado', 'desconocido')
    
    if estado == 'encontrado':
        print("\n=== INFORMACIÓN DEL PRODUCTO ===")
        print(f"Nombre: {info.get('nombre', 'No disponible')}")
        print(f"Precio Neto: {info.get('precio_neto', 'No disponible')}")
        print(f"PMP: {info.get('pmp', 'No disponible')}")
        print(f"Laboratorio: {info.get('laboratorio', 'No disponible')}")
        print(f"Disponibilidad: {info.get('disponibilidad', 'No disponible')}")
        print(f"Existencia: {info.get('existencia', 'No disponible')}")
        print(f"URL: {info.get('url', 'No disponible')}")
        print("\nResultado: Producto encontrado")
    else:
        print(f"\n{info.get('mensaje', 'No se pudo obtener información del producto')}")
        print(f"\nEstado: {estado}")
    
    # Guardar resultado como JSON para procesamiento externo
    try:
        output_file = f"{medicamento.replace(' ', '_')}_resultado.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=4)
        print(f"\nResultado guardado en: {output_file}")
    except Exception as e:
        print(f"\nError al guardar resultado: {e}")

    sys.exit(0 if estado == 'encontrado' else 1)
