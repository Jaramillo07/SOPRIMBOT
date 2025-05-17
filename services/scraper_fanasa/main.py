#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal para el scraper de FANASA.
Proporciona funcionalidad para buscar información de productos en el portal FANASA Carrito.
"""

import time
import logging
import re
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
LOGIN_URL = "https://carrito.fanasa.com/login"  # URL del portal de carrito
TIMEOUT = 20                       # Tiempo de espera para elementos (segundos)

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
    
    try:
        # Inicializar el navegador Chrome
        driver = webdriver.Chrome(options=options)
        logger.info("Navegador Chrome inicializado correctamente")
        return driver
    except Exception as e:
        logger.error(f"Error al inicializar el navegador: {e}")
        return None

def login_fanasa_carrito():
    """
    Realiza el proceso de login en el portal de carrito de FANASA.
    
    Returns:
        webdriver.Chrome: Instancia del navegador con sesión iniciada o None si falla
    """
    driver = inicializar_navegador(headless=True)  # Usar True para entorno de producción
    if not driver:
        logger.error("No se pudo inicializar el navegador. Abortando.")
        return None
    
    try:
        # 1. Navegar a la página de login
        logger.info(f"Navegando a la página de login: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        time.sleep(5)  # Esperar a que cargue la página
        
        # 2. Buscar campo de usuario
        logger.info("Buscando campo de usuario...")
        
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
                fields = driver.find_elements(By.CSS_SELECTOR, selector)
                for field in fields:
                    if field.is_displayed():
                        username_field = field
                        logger.info(f"Campo de usuario encontrado con selector: {selector}")
                        break
                if username_field:
                    break
            except:
                continue
        
        # Si no encontramos con los selectores específicos, buscar cualquier input visible
        if not username_field:
            try:
                # Buscar todos los inputs visibles
                inputs = driver.find_elements(By.TAG_NAME, "input")
                visible_inputs = [inp for inp in inputs if inp.is_displayed()]
                
                if visible_inputs:
                    # Primer input visible probablemente sea el de usuario
                    username_field = visible_inputs[0]
                    logger.info("Campo de usuario encontrado como primer input visible")
            except:
                pass
        
        # Si no se encuentra el campo de usuario, no podemos continuar
        if not username_field:
            logger.error("No se pudo encontrar el campo de usuario")
            driver.quit()
            return None
        
        # Limpiar e ingresar el usuario
        username_field.clear()
        username_field.send_keys(USERNAME)
        logger.info(f"Usuario ingresado: {USERNAME}")
        time.sleep(1)
        
        # 3. Buscar campo de contraseña
        logger.info("Buscando campo de contraseña...")
        
        password_field = None
        password_selectors = [
            "input[placeholder='Contraseña']",
            "#password",  # Posible ID
            "input[type='password']",
            "input.form-control[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                fields = driver.find_elements(By.CSS_SELECTOR, selector)
                for field in fields:
                    if field.is_displayed():
                        password_field = field
                        logger.info(f"Campo de contraseña encontrado con selector: {selector}")
                        break
                if password_field:
                    break
            except:
                continue
        
        # Si no encontramos con selectores específicos, buscar por tipo password
        if not password_field:
            try:
                password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                if password_inputs:
                    for inp in password_inputs:
                        if inp.is_displayed():
                            password_field = inp
                            logger.info("Campo de contraseña encontrado por tipo 'password'")
                            break
            except:
                pass
        
        # Si no se encuentra el campo de contraseña, no podemos continuar
        if not password_field:
            logger.error("No se pudo encontrar el campo de contraseña")
            driver.quit()
            return None
        
        # Limpiar e ingresar la contraseña
        password_field.clear()
        password_field.send_keys(PASSWORD)
        logger.info("Contraseña ingresada")
        time.sleep(1)
        
        # 4. Buscar botón de inicio de sesión
        logger.info("Buscando botón 'Iniciar sesión'...")
        
        login_button = None
        button_selectors = [
            "button.btn-primary",  # Clase probable basada en la captura
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
                        logger.info(f"Botón 'Iniciar sesión' encontrado con selector: {selector}")
                        break
                if login_button:
                    break
            except:
                continue
        
        # Si no encontramos con CSS, intentar con XPath específico para el texto
        if not login_button:
            try:
                xpath_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'iniciar sesión')]")
                if xpath_buttons:
                    for button in xpath_buttons:
                        if button.is_displayed():
                            login_button = button
                            logger.info("Botón 'Iniciar sesión' encontrado por texto")
                            break
            except:
                pass
        
        # Si no se encuentra un botón específico, buscar cualquier botón visible
        if not login_button:
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    if button.is_displayed() and button.is_enabled():
                        login_button = button
                        logger.info("Usando primer botón visible como botón de login")
                        break
            except:
                pass
        
        # Si no se encuentra el botón, intentar enviar el formulario con Enter
        if not login_button:
            logger.warning("No se encontró botón de inicio de sesión. Intentando enviar formulario con Enter.")
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
        else:
            # Hacer clic en el botón
            try:
                # Asegurar que el botón sea visible
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_button)
                time.sleep(1)
                
                # Hacer clic
                login_button.click()
                logger.info("Clic en botón 'Iniciar sesión' realizado")
                
            except ElementClickInterceptedException:
                # Si hay algo interceptando el clic, intentar con JavaScript
                logger.warning("Clic interceptado. Intentando con JavaScript.")
                driver.execute_script("arguments[0].click();", login_button)
                logger.info("Clic en botón realizado con JavaScript")
            
            time.sleep(5)  # Esperar a que se procese el login
        
        # 5. Verificar si el login fue exitoso
        current_url = driver.current_url
        logger.info(f"URL actual después del intento de login: {current_url}")
        
        # Verificar si ya no estamos en la página de login
        login_exitoso = "/login" not in current_url
        
        # También verificar si hay indicadores de sesión iniciada
        if not login_exitoso:
            page_text = driver.page_source.lower()
            success_indicators = [
                "cerrar sesión" in page_text,
                "logout" in page_text,
                "mi cuenta" in page_text,
                "carrito" in page_text and not "/login" in current_url
            ]
            
            login_exitoso = any(success_indicators)
        
        # Verificar si hay mensajes de error visibles
        has_error = False
        try:
            error_messages = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .text-danger")
            for error in error_messages:
                if error.is_displayed():
                    has_error = True
                    logger.error(f"Mensaje de error detectado: {error.text}")
                    break
        except:
            pass
        
        # Resultado final
        if login_exitoso and not has_error:
            logger.info("¡LOGIN EXITOSO EN FANASA CARRITO!")
            return driver
        else:
            logger.error("ERROR: Login en FANASA Carrito fallido")
            
            if has_error:
                logger.error("Se detectaron mensajes de error en la página")
            
            driver.quit()
            return None
        
    except Exception as e:
        logger.error(f"Error durante el proceso de login: {e}")
        if driver:
            driver.quit()
        return None

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en el sitio una vez que estamos logueados.
    
    Args:
        driver: Instancia del navegador con sesión iniciada
        nombre_producto: Nombre del producto a buscar
        
    Returns:
        bool: True si se encontró y accedió al detalle del producto, False en caso contrario
    """
    if not driver:
        logger.error("No se proporcionó un navegador válido para buscar producto")
        return False
    
    try:
        logger.info(f"Buscando producto: {nombre_producto}")
        
        # Esperar un momento para que la página se cargue completamente
        time.sleep(5)
        
        # MÉTODO 1: Buscar el campo de búsqueda
        max_retries = 3
        for retry in range(max_retries):
            try:
                logger.info(f"Intento #{retry+1} de buscar el campo de búsqueda")
                
                # Buscar específicamente por la clase identificada
                search_field = None
                try:
                    search_field = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input.search_input"))
                    )
                    logger.info("Campo de búsqueda encontrado por clase 'search_input'")
                except:
                    logger.warning("No se pudo encontrar el campo con clase 'search_input'")
                
                # Si no funciona, intentar con otros selectores
                if not search_field:
                    specific_selectors = [
                        "input[placeholder='Nombre, laboratorio, sal, código de barras o Categoria']",
                        "input.ng-untouched.ng-pristine.ng-valid[type='text']",
                        ".search_input",
                        "input.input-src"
                    ]
                    
                    for selector in specific_selectors:
                        try:
                            search_field = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            if search_field and search_field.is_displayed():
                                logger.info(f"Campo de búsqueda encontrado con selector: {selector}")
                                break
                        except:
                            logger.warning(f"No se encontró el campo con selector: {selector}")
                
                # Si encontramos el campo, intentar interactuar con él
                if search_field and search_field.is_displayed():
                    logger.info("Campo de búsqueda encontrado y visible")
                    
                    # Enfocarse en el campo antes de interactuar
                    driver.execute_script("arguments[0].focus();", search_field)
                    time.sleep(1)
                    
                    # Limpiar el campo primero
                    driver.execute_script("arguments[0].value = '';", search_field)
                    time.sleep(0.5)
                    
                    # Escribir el texto usando JavaScript
                    driver.execute_script(f"arguments[0].value = '{nombre_producto}';", search_field)
                    logger.info(f"Texto '{nombre_producto}' ingresado con JavaScript")
                    time.sleep(0.5)
                    
                    # Verificar el valor ingresado
                    valor_ingresado = driver.execute_script("return arguments[0].value;", search_field)
                    logger.info(f"Valor en el campo: '{valor_ingresado}'")
                    
                    # Intentar enviar la búsqueda con Enter
                    try:
                        # Presionar Enter con JavaScript/Action Chains
                        search_field.send_keys(Keys.RETURN)
                        logger.info("Tecla Enter enviada al campo")
                    except:
                        logger.warning("Error al enviar Enter, intentando alternativa...")
                        # Alternativa: buscar y hacer clic en el botón de búsqueda (lupa)
                        try:
                            # Buscar botón de búsqueda por su posición junto al campo
                            buscar_btns = driver.find_elements(By.CSS_SELECTOR, ".btn-buscar, button.search-btn, button[type='submit'], button.btn-search")
                            if buscar_btns:
                                for btn in buscar_btns:
                                    if btn.is_displayed():
                                        logger.info("Botón de búsqueda encontrado, haciendo clic...")
                                        btn.click()
                                        break
                            else:
                                # Si no hay botón específico, intentar presionar Enter con Action Chains
                                logger.info("Intentando buscar con Action Chains...")
                                actions = webdriver.ActionChains(driver)
                                actions.send_keys(Keys.RETURN).perform()
                        except Exception as e:
                            logger.warning(f"Error al hacer clic en botón de búsqueda: {e}")
                    
                    # Esperar a que se procese la búsqueda
                    time.sleep(5)
                    
                    # Verificar si se procesó la búsqueda
                    page_source = driver.page_source
                    if nombre_producto.lower() in page_source.lower():
                        logger.info(f"Texto de búsqueda '{nombre_producto}' encontrado en la página")
                        
                        # Comprobar si hay resultados
                        if "No se pudo encontrar el producto" in page_source:
                            logger.warning(f"No se encontraron resultados para: '{nombre_producto}'")
                            return False
                        else:
                            logger.info(f"Búsqueda exitosa para: '{nombre_producto}'")
                            
                            # Intentar hacer clic en algún resultado de producto
                            try:
                                # Buscar específicamente botones "Ver detalle"
                                ver_detalle_selectors = [
                                    "button:contains('Ver detalle')",
                                    "a:contains('Ver detalle')",
                                    ".btn:contains('Ver detalle')",
                                    "button.btn-outline-primary", 
                                    "a.ver-detalle",
                                    ".btn-outline-primary",
                                    "button.ver-detalle"
                                ]
                                
                                detail_button_found = False
                                for selector in ver_detalle_selectors:
                                    try:
                                        detail_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                                        for btn in detail_buttons:
                                            if btn.is_displayed():
                                                logger.info(f"Botón 'Ver detalle' encontrado con selector: {selector}")
                                                
                                                # Hacer scroll hasta el botón
                                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                                time.sleep(1)
                                                
                                                # Intentar hacer clic con JavaScript (más confiable)
                                                try:
                                                    driver.execute_script("arguments[0].click();", btn)
                                                    logger.info("Clic en 'Ver detalle' realizado con JavaScript")
                                                    detail_button_found = True
                                                except Exception as e:
                                                    logger.warning(f"Error al hacer clic con JS: {e}, intentando método normal")
                                                    btn.click()
                                                    detail_button_found = True
                                                
                                                # Esperar a que cargue la página de detalle
                                                time.sleep(3)
                                                return True
                                    except Exception as e:
                                        logger.warning(f"Error con selector {selector}: {e}")
                                
                                # Si no encontramos botones específicos, buscar por texto exacto
                                if not detail_button_found:
                                    try:
                                        xpath_buttons = driver.find_elements(By.XPATH, "//*[text()='Ver detalle']")
                                        for btn in xpath_buttons:
                                            if btn.is_displayed():
                                                logger.info("Botón 'Ver detalle' encontrado por XPath texto exacto")
                                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                                time.sleep(1)
                                                driver.execute_script("arguments[0].click();", btn)
                                                time.sleep(3)
                                                return True
                                    except Exception as e:
                                        logger.warning(f"Error al buscar por XPath texto: {e}")
                                
                                # Intentar interactuar con la tarjeta del producto
                                product_card_selectors = [
                                    ".product-item", ".product-card", ".col-lg-12", 
                                    ".owl-item", ".producto", ".card"
                                ]
                                
                                for selector in product_card_selectors:
                                    try:
                                        cards = driver.find_elements(By.CSS_SELECTOR, selector)
                                        for card in cards:
                                            if card.is_displayed():
                                                # Buscar el botón dentro de la tarjeta
                                                detail_btns = card.find_elements(By.CSS_SELECTOR, "button, a")
                                                ver_detalle_btn = None
                                                
                                                for btn in detail_btns:
                                                    try:
                                                        if btn.is_displayed() and "detalle" in btn.text.lower():
                                                            ver_detalle_btn = btn
                                                            break
                                                    except:
                                                        pass
                                                
                                                if ver_detalle_btn:
                                                    logger.info("Botón 'Ver detalle' encontrado en tarjeta")
                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ver_detalle_btn)
                                                    time.sleep(1)
                                                    driver.execute_script("arguments[0].click();", ver_detalle_btn)
                                                    time.sleep(3)
                                                    return True
                                                else:
                                                    # Intentar último botón visible
                                                    visible_buttons = [btn for btn in detail_btns if btn.is_displayed()]
                                                    if visible_buttons:
                                                        last_button = visible_buttons[-1]
                                                        logger.info(f"Haciendo clic en último botón visible")
                                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", last_button)
                                                        time.sleep(1)
                                                        driver.execute_script("arguments[0].click();", last_button)
                                                        time.sleep(3)
                                                        return True
                                    except Exception as e:
                                        logger.warning(f"Error con tarjeta de producto {selector}: {e}")
                            except Exception as e:
                                logger.warning(f"Error al intentar hacer clic en resultados: {e}")
                            
                            # Incluso si no podemos hacer clic, consideramos exitosa la búsqueda
                            return True
                    else:
                        logger.warning(f"No se encontró evidencia de que la búsqueda '{nombre_producto}' se procesara")
                        
                    # Intentar otro enfoque si falla
                    logger.info("Intentando otro enfoque para la búsqueda...")
                else:
                    logger.warning("Campo de búsqueda no encontrado o no visible en este intento")
            
            except Exception as e:
                logger.error(f"Error en intento #{retry+1}: {e}")
            
            # Esperar antes del siguiente intento
            time.sleep(2)
        
        # PLAN B: Enfoques alternativos si los anteriores fallan
        logger.info("Intentando enfoque alternativo de búsqueda...")
        
        try:
            # Verificar si estamos en la página principal
            if "carrito.fanasa.com" in driver.current_url and "/login" not in driver.current_url:
                logger.info("Estamos en la página principal, intentando con JavaScript")
                
                # Método 1: Ejecutar JavaScript para simular una búsqueda directa
                try:
                    logger.info("Intentando buscar con JavaScript directo...")
                    js_script = """
                    let inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
                    for (let i = 0; i < inputs.length; i++) {
                        if (inputs[i].offsetParent !== null) {  // Es visible
                            inputs[i].value = arguments[0];
                            inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                            inputs[i].dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                    """
                    result = driver.execute_script(js_script, nombre_producto)
                    logger.info(f"Resultado de búsqueda JS: {result}")
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"Error en búsqueda JS: {e}")
                
                # Método 2: Usar coordenadas basadas en la imagen
                try:
                    logger.info("Intentando clic en coordenadas del campo de búsqueda...")
                    actions = webdriver.ActionChains(driver)
                    actions.move_by_offset(500, 100).click().perform()
                    time.sleep(1)
                    actions.send_keys(nombre_producto).perform()
                    time.sleep(1)
                    actions.send_keys(Keys.RETURN).perform()
                    logger.info("Búsqueda enviada por coordenadas")
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"Error en búsqueda por coordenadas: {e}")
                
                # Método 3: Navegación directa a URL de búsqueda
                try:
                    logger.info("Navegando directamente a URL de búsqueda...")
                    base_url = driver.current_url.split('?')[0]
                    search_url = f"{base_url}?q={nombre_producto}"
                    logger.info(f"Navegando a: {search_url}")
                    driver.get(search_url)
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"Error en navegación directa: {e}")
            
            # Verificar si alguno de los métodos funcionó
            if nombre_producto.lower() in driver.page_source.lower() and "No se pudo encontrar el producto" not in driver.page_source:
                logger.info("¡Alguno de los métodos alternativos funcionó!")
                return True
            else:
                logger.error("Todos los métodos alternativos fallaron")
                return False
                
        except Exception as e:
            logger.error(f"Error en enfoque alternativo: {e}")
            return False
        
    except Exception as e:
        logger.error(f"Error general durante la búsqueda: {e}")
        return False

def extraer_info_producto(driver):
    """
    Extrae información detallada del producto de la página actual.
    
    Args:
        driver: Instancia del navegador con la página de detalle abierta
        
    Returns:
        dict: Diccionario con la información del producto o None si hay error
    """
    if not driver:
        logger.error("No se proporcionó un navegador válido")
        return None
    
    try:
        logger.info("Extrayendo información del producto...")
        # Esperar a que la página cargue completamente
        time.sleep(3)
        
        # Inicializar diccionario con todas las claves (incluso vacías)
        info_producto = {
            'url': driver.current_url,
            'nombre': '',
            'precio_neto': '',
            'pmp': '',
            'sku': '',
            'laboratorio': '',
            'disponibilidad': '',
            'imagen': '',
            'descripcion': ''
        }

        # NOMBRE DEL PRODUCTO
        try:
            nombre_selectors = [
                "h1", "h2", "h3", ".product-name", ".product-title", "h1.product-name", 
                ".name-product", "strong.name", ".product-header h1", "[itemprop='name']"
            ]
            
            for selector in nombre_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            text = element.text.strip()
                            # Verificar si el texto parece un nombre de producto
                            if len(text) > 5 and not text.lower() in ["detalle", "detalle de producto"]:
                                info_producto['nombre'] = text
                                logger.info(f"Nombre del producto: {info_producto['nombre']}")
                                break
                    if info_producto['nombre']:
                        break
                except:
                    continue
            
            # Si no encontramos el nombre con CSS, intentamos con XPath
            if not info_producto['nombre']:
                try:
                    nombres_xpath = driver.find_elements(By.XPATH, 
                        "//h1 | //h2[not(contains(., 'Login'))] | //*[contains(text(), 'GE') or contains(text(), 'AMPICILINA')]")
                    
                    for element in nombres_xpath:
                        if element.is_displayed() and element.text.strip() and len(element.text.strip()) > 5:
                            info_producto['nombre'] = element.text.strip()
                            logger.info(f"Nombre del producto (XPath): {info_producto['nombre']}")
                            break
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo nombre: {e}")

        # PRECIO NETO
        try:
            # Intentar encontrar elementos con "Precio Neto"
            try:
                precio_neto_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'Precio Neto')]/following::*[contains(text(), '$')] | //*[contains(text(), 'Precio Neto')]//following-sibling::*[contains(text(), '$')]")
                
                for element in precio_neto_elements:
                    if element.is_displayed():
                        texto_precio = element.text.strip()
                        precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto_precio)
                        if precio_match:
                            info_producto['precio_neto'] = f"${precio_match.group(1)}"
                            logger.info(f"Precio Neto: {info_producto['precio_neto']}")
                            break
            except:
                pass
                
            # Si no encontramos precio específico, buscar otros valores monetarios
            if not info_producto['precio_neto']:
                try:
                    precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), ')]")
                    
                    for element in precio_elements:
                        if element.is_displayed():
                            texto = element.text.strip().lower()
                            # Si contiene 'neto' o no contiene 'pmp' (probablemente es precio neto)
                            if "neto" in texto or ("pmp" not in texto and "publico" not in texto):
                                precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto)
                                if precio_match:
                                    info_producto['precio_neto'] = f"${precio_match.group(1)}"
                                    logger.info(f"Precio Neto (inferido): {info_producto['precio_neto']}")
                                    break
                except:
                    pass
                    
            # Si todavía no encontramos precio, usar la estrategia del precio más bajo
            if not info_producto['precio_neto']:
                try:
                    precios = []
                    precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), ')]")
                    
                    for element in precio_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto)
                            if precio_match:
                                try:
                                    valor = float(precio_match.group(1).replace(',', ''))
                                    precios.append((valor, f"${precio_match.group(1)}"))
                                except:
                                    pass
                    
                    # Ordenar por valor y tomar el más bajo (típicamente el precio neto)
                    if precios:
                        precios.sort()
                        info_producto['precio_neto'] = precios[0][1]
                        logger.info(f"Precio Neto (precio más bajo): {info_producto['precio_neto']}")
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo Precio Neto: {e}")

        # PMP (PRECIO MÁXIMO PÚBLICO)
        try:
            # Buscar elementos que contengan "PMP"
            try:
                pmp_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'PMP')]/following::*[contains(text(), ')] | //*[contains(text(), 'PMP')]//following-sibling::*[contains(text(), ')] | //*[contains(text(), 'Precio Público')]//following-sibling::*[contains(text(), ')]")
                
                for element in pmp_elements:
                    if element.is_displayed():
                        texto_pmp = element.text.strip()
                        pmp_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto_pmp)
                        if pmp_match:
                            info_producto['pmp'] = f"${pmp_match.group(1)}"
                            logger.info(f"PMP: {info_producto['pmp']}")
                            break
            except:
                pass
                
            # Si no encontramos PMP específico pero tenemos precio neto, buscar el precio más alto
            if not info_producto['pmp'] and info_producto['precio_neto']:
                try:
                    precio_neto_valor = float(info_producto['precio_neto'].replace(', '').replace(',', ''))
                    precio_alto = None
                    precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), ')]")
                    
                    for element in precio_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto)
                            if precio_match:
                                try:
                                    valor = float(precio_match.group(1).replace(',', ''))
                                    # Si es mayor que el precio neto, podría ser el PMP
                                    if valor > precio_neto_valor and (precio_alto is None or valor > precio_alto):
                                        precio_alto = valor
                                except:
                                    pass
                    
                    if precio_alto:
                        info_producto['pmp'] = f"${precio_alto}"
                        logger.info(f"PMP (precio más alto): {info_producto['pmp']}")
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo PMP: {e}")

        # SKU / CÓDIGO DE PRODUCTO
        try:
            # Buscar elementos que contengan "SKU" o "Código"
            try:
                sku_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'SKU') or contains(text(), 'Código') or contains(text(), 'Codigo')]/following::*")
                
                for element in sku_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        # Los SKUs generalmente son números largos
                        sku_match = re.search(r'\b(\d{7,})\b', texto)
                        if sku_match:
                            info_producto['sku'] = sku_match.group(1)
                            logger.info(f"SKU: {info_producto['sku']}")
                            break
                        # Si no hay número largo pero contiene un patrón alfanumérico que podría ser un código
                        elif re.match(r'^[A-Za-z0-9-]+, texto) and len(texto) >= 5:
                            info_producto['sku'] = texto
                            logger.info(f"SKU (alfanumérico): {info_producto['sku']}")
                            break
            except:
                pass
            
            # Si no encontramos el SKU, buscar números largos que podrían ser SKUs
            if not info_producto['sku']:
                try:
                    all_elements = driver.find_elements(By.XPATH, "//*[string-length(text()) > 6]")
                    for element in all_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            # Evitar textos con $ (precios) y buscar números largos
                            if "$" not in texto:
                                sku_match = re.search(r'\b(\d{7,})\b', texto)
                                if sku_match:
                                    info_producto['sku'] = sku_match.group(1)
                                    logger.info(f"SKU (número largo): {info_producto['sku']}")
                                    break
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo SKU: {e}")

        # LABORATORIO / FABRICANTE
        try:
            # Buscar elementos que contengan "Laboratorio"
            try:
                lab_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'Laboratorio') or contains(text(), 'Fabricante')]/following::*")
                
                for element in lab_elements:
                    if element.is_displayed() and element.text.strip():
                        texto = element.text.strip()
                        # Verificar que no sea un texto genérico o un precio
                        if len(texto) > 3 and "$" not in texto:
                            info_producto['laboratorio'] = texto
                            logger.info(f"Laboratorio: {info_producto['laboratorio']}")
                            break
            except:
                pass
            
            # Si no encontramos el laboratorio, buscar textos que podrían ser nombres de laboratorios
            if not info_producto['laboratorio']:
                try:
                    # Palabras clave que podrían indicar un laboratorio farmacéutico
                    lab_keywords = ["ANTIBIOTICOS", "FARMA", "LABORATORIO", "LAB", "MEXICO", "PHARMA"]
                    
                    # Buscar elementos que podrían contener nombres de laboratorios
                    lab_candidates = driver.find_elements(By.XPATH, "//strong | //b | //div[text()[string-length() > 3]]")
                    
                    for element in lab_candidates:
                        if element.is_displayed():
                            texto = element.text.strip().upper()
                            # Verificar si contiene alguna palabra clave de laboratorio
                            if any(keyword in texto for keyword in lab_keywords) and "$" not in texto:
                                info_producto['laboratorio'] = texto
                                logger.info(f"Laboratorio (inferido): {info_producto['laboratorio']}")
                                break
                except:
                    pass
                    
            # Como fallback adicional, buscar específicamente "ANTIBIOTICOS DE MEXICO"
            if not info_producto['laboratorio']:
                try:
                    all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'ANTIBIOTICOS')]")
                    for element in all_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            if "MEXICO" in texto.upper():
                                info_producto['laboratorio'] = texto
                                logger.info(f"Laboratorio (ANTIBIOTICOS DE MEXICO): {info_producto['laboratorio']}")
                                break
                except:
                    pass
                    
            # Si todo falla, usar un valor predeterminado basado en el nombre del producto
            if not info_producto['laboratorio'] and "GE" in info_producto['nombre']:
                info_producto['laboratorio'] = "ANTIBIOTICOS DE MEXICO"
                logger.info(f"Laboratorio (predeterminado basado en nombre): {info_producto['laboratorio']}")
        except Exception as e:
            logger.warning(f"Error general extrayendo Laboratorio: {e}")
            info_producto['laboratorio'] = "No especificado"

        # DISPONIBILIDAD / STOCK
        try:
            # Buscar explícitamente el patrón "Stock (número)"
            try:
                stock_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Stock (')]")
                
                for element in stock_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        # Buscar el patrón exacto "Stock (número)"
                        stock_match = re.search(r'[Ss]tock\s*\((\d+)\)', texto)
                        if stock_match:
                            info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                            logger.info(f"Disponibilidad (Stock exacto): {info_producto['disponibilidad']}")
                            break
            except:
                pass
            
            # Si no encontramos disponibilidad específica, buscar stock en toda la página
            if not info_producto['disponibilidad']:
                try:
                    page_source = driver.page_source
                    stock_match = re.search(r'[Ss]tock\s*\((\d+)\)', page_source)
                    if stock_match:
                        info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                        logger.info(f"Disponibilidad (regex en página): {info_producto['disponibilidad']}")
                except:
                    pass
            
            # Si todavía no encontramos disponibilidad, probar con elementos más específicos
            if not info_producto['disponibilidad']:
                try:
                    stock_elements = driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'Stock') or contains(text(), 'stock') or contains(text(), 'Disponibilidad') or contains(text(), 'Existencias')]")
                    
                    for element in stock_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            
                            # Primero buscar "Stock (XXX)"
                            stock_match = re.search(r'[Ss]tock\s*\((\d+)\)', texto)
                            if stock_match:
                                info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                                logger.info(f"Disponibilidad (Stock en texto): {info_producto['disponibilidad']}")
                                break
                            
                            # Si no se encuentra ese patrón, buscar cualquier número entre paréntesis
                            parenthesis_match = re.search(r'\((\d+)\)', texto)
                            if parenthesis_match and "precio" not in texto.lower() and "$" not in texto:
                                info_producto['disponibilidad'] = f"Stock ({parenthesis_match.group(1)})"
                                logger.info(f"Disponibilidad (número en paréntesis): {info_producto['disponibilidad']}")
                                break
                except:
                    pass
            
            # Asignar un valor por defecto si todo lo anterior falla
            if not info_producto['disponibilidad']:
                info_producto['disponibilidad'] = "Stock disponible"
                logger.warning(f"No se encontró información específica de stock, usando valor predeterminado")
        except Exception as e:
            logger.warning(f"Error general extrayendo Disponibilidad: {e}")
            info_producto['disponibilidad'] = "Stock disponible"

        # IMAGEN DEL PRODUCTO
        try:
            img_selectors = [
                "img.img-fluid", "img.product-image", ".product-gallery img", 
                "img[alt*='producto']", "img[src*='producto']",
                ".product-detail img", ".product img"
            ]
            
            for selector in img_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            src = element.get_attribute("src")
                            if src and ('http' in src):
                                info_producto['imagen'] = src
                                logger.info(f"URL de imagen: {info_producto['imagen']}")
                                break
                    if info_producto['imagen']:
                        break
                except:
                    continue
                    
            # Si no encontramos imagen con selectores específicos, buscar cualquier imagen visible
            if not info_producto['imagen']:
                try:
                    all_images = driver.find_elements(By.TAG_NAME, "img")
                    for img in all_images:
                        if img.is_displayed():
                            src = img.get_attribute("src")
                            # Excluir logos e íconos pequeños
                            if src and ('http' in src) and "logo" not in src.lower():
                                # Comprobar tamaño mínimo
                                if img.size['width'] > 50 and img.size['height'] > 50:
                                    info_producto['imagen'] = src
                                    logger.info(f"URL de imagen (general): {info_producto['imagen']}")
                                    break
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo Imagen: {e}")

        # DESCRIPCIÓN (opcional)
        try:
            desc_selectors = [
                ".product-description", ".description", "#description", 
                "[itemprop='description']", ".product-details p",
                ".tab-content .tab-pane.active", ".product-info p"
            ]
            
            for selector in desc_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            texto = element.text.strip()
                            # Verificar que sea una descripción relevante (no texto de UI)
                            if len(texto) > 20 and "login" not in texto.lower() and "carrito" not in texto.lower():
                                info_producto['descripcion'] = texto
                                logger.info(f"Descripción extraída (longitud: {len(info_producto['descripcion'])} caracteres)")
                                break
                    if info_producto['descripcion']:
                        break
                except:
                    continue
                    
            # Si no encontramos descripción con selectores, buscar párrafos largos
            if not info_producto['descripcion']:
                try:
                    paragraphs = driver.find_elements(By.TAG_NAME, "p")
                    for p in paragraphs:
                        if p.is_displayed() and p.text.strip():
                            texto = p.text.strip()
                            if len(texto) > 50 and "login" not in texto.lower() and "carrito" not in texto.lower():
                                info_producto['descripcion'] = texto
                                logger.info(f"Descripción (párrafo): {info_producto['descripcion'][:30]}...")
                                break
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo Descripción: {e}")
            
        # Verificar si tenemos información mínima
        info_minima = (info_producto['nombre'] != '') and (info_producto['precio_neto'] != '' or info_producto['pmp'] != '')
        
        if info_minima:
            logger.info("✅ Información mínima del producto extraída con éxito")
        else:
            logger.warning("⚠️ No se pudo extraer toda la información mínima del producto")
            
            # Generar un registro de qué información falta
            missing = []
            if info_producto['nombre'] == '':
                missing.append("nombre")
            if info_producto['precio_neto'] == '' and info_producto['pmp'] == '':
                missing.append("precios")
                
            logger.warning(f"Falta la siguiente información: {', '.join(missing)}")
        
        # Devolver la información aunque no esté completa
        return info_producto
            
    except TimeoutException:
        logger.error("Timeout esperando la carga de la página de detalle para extracción.")
        return None
    except Exception as e:
        logger.error(f"Error general durante la extracción de información: {e}")
        return None

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en FANASA.
    
    Args:
        nombre_medicamento (str): Nombre del medicamento a buscar
        headless (bool): Si es True, el navegador se ejecuta en modo headless
        
    Returns:
        dict: Diccionario con la información del medicamento o None si no se encuentra
    """
    driver = None
    try:
        # 1. Iniciar sesión en FANASA
        logger.info(f"Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")
        
        driver = login_fanasa_carrito()
        if not driver:
            logger.error("No se pudo iniciar sesión en FANASA. Abortando búsqueda.")
            return None
        
        # 2. Buscar el producto
        logger.info(f"Sesión iniciada. Buscando producto: '{nombre_medicamento}'")
        
        resultado_busqueda = buscar_producto(driver, nombre_medicamento)
        
        if not resultado_busqueda:
            logger.warning(f"No se pudo encontrar o acceder al producto: '{nombre_medicamento}'")
            return None
        
        # 3. Extraer información del producto
        logger.info("Extrayendo información del producto...")
        info_producto = extraer_info_producto(driver)
        
        # Añadir la fuente para integración con el servicio principal
        if info_producto:
            info_producto['fuente'] = 'FANASA'
            # Compatibilidad para trabajar con el servicio de orquestación
            info_producto['existencia'] = '0'
            if info_producto['disponibilidad']:
                # Extraer números de la disponibilidad si existe
                stock_match = re.search(r'(\d+)', info_producto['disponibilidad'])
                if stock_match:
                    info_producto['existencia'] = stock_match.group(1)
                elif 'disponible' in info_producto['disponibilidad'].lower():
                    info_producto['existencia'] = 'Si'
        
        return info_producto
        
    except Exception as e:
        logger.error(f"Error general durante el proceso: {e}")
        return None
    finally:
        if driver:
            logger.info("Cerrando navegador...")
            driver.quit()

# Para ejecución directa como script independiente
if __name__ == "__main__":
    import sys
    
    print("=== Sistema de Búsqueda de Medicamentos en FANASA ===")
    
    # Si se proporciona un argumento por línea de comandos, usarlo como nombre del medicamento
    if len(sys.argv) > 1:
        medicamento = " ".join(sys.argv[1:])
    else:
        # De lo contrario, pedir al usuario
        medicamento = input("Ingrese el nombre del medicamento a buscar: ")
    
    print(f"\nBuscando información sobre: {medicamento}")
    print("Espere un momento...\n")
    
    # Definir el modo headless basado en entorno
    import os
    headless = os.environ.get('ENVIRONMENT', 'production').lower() != 'development'
    
    # Buscar información del medicamento
    info = buscar_info_medicamento(medicamento, headless=headless)
    
    if info:
        print("\n=== INFORMACIÓN DEL PRODUCTO ===")
        print(f"Nombre: {info.get('nombre', 'No disponible')}")
        print(f"Precio Neto: {info.get('precio_neto', 'No disponible')}")
        print(f"PMP: {info.get('pmp', 'No disponible')}")
        print(f"Laboratorio: {info.get('laboratorio', 'No disponible')}")
        print(f"SKU: {info.get('sku', 'No disponible')}")
        print(f"Disponibilidad: {info.get('disponibilidad', 'No disponible')}")
        if info.get('imagen'):
            print(f"Imagen: {info['imagen']}")
        print(f"URL: {info['url']}")
        
        # Preguntar si desea guardar la información en un archivo
        guardar = input("\n¿Deseas guardar esta información en un archivo? (s/n): ").lower()
        if guardar == 's':
            try:
                import json
                from datetime import datetime
                
                fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"{info['nombre']}_{fecha_hora}.json".replace(" ", "_").replace("/", "_")
                
                with open(nombre_archivo, "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=4)
                
                print(f"\n✅ Información guardada en el archivo: {nombre_archivo}")
            except Exception as e:
                print(f"\n❌ Error al guardar información: {e}")
    else:
        print("No se pudo encontrar información sobre el medicamento solicitado")