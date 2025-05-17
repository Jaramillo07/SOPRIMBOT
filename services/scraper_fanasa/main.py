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
    driver = None
    try:
        driver = inicializar_navegador(headless=True)  # Usar True para entorno de producción
        if not driver:
            logger.error("No se pudo inicializar el navegador. Abortando.")
            return None
        
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
            ".btn-primary",
            ".btn-login"
        ]
        
        for selector in button_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed():
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
        time.sleep(10)  # Aumentamos el tiempo de espera inicial
        
        # Guardar HTML de la página principal para análisis
        with open("pagina_principal.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("HTML de la página principal guardado para análisis")
        
        # Capturar la página principal
        driver.save_screenshot("pagina_principal.png")
        
        # MÉTODO 1: Buscar directamente por clase específica de la imagen
        max_retries = 3
        for retry in range(max_retries):
            try:
                logger.info(f"Intento #{retry+1} de buscar el campo de búsqueda")
                
                # Refrescar la lista de inputs para evitar referencia obsoleta
                inputs = driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Número de inputs encontrados: {len(inputs)}")
                
                # Imprimir info de inputs para debug
                for i, inp in enumerate(inputs):
                    try:
                        tipo = inp.get_attribute("type")
                        placeholder = inp.get_attribute("placeholder")
                        id_elem = inp.get_attribute("id")
                        clase = inp.get_attribute("class")
                        visible = inp.is_displayed()
                        logger.info(f"Input {i}: type={tipo}, placeholder={placeholder}, id={id_elem}, class={clase}, visible={visible}")
                    except:
                        logger.warning(f"No se pudo obtener atributos del input {i}")
                
                # Buscar específicamente por la clase identificada en la imagen
                search_field = None
                try:
                    # Usar el selector específico basado en el input #1 que vimos en los logs
                    search_field = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input.search_input"))
                    )
                    logger.info("Campo de búsqueda encontrado por clase 'search_input'")
                except:
                    logger.warning("No se pudo encontrar el campo con clase 'search_input'")
                
                # Si no funciona, intentar con otros selectores más específicos
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
                    
                    # Tomar una captura antes de interactuar
                    driver.save_screenshot(f"campo_busqueda_encontrado_intento{retry+1}.png")
                    
                    # Enfocarse en el campo antes de interactuar
                    driver.execute_script("arguments[0].focus();", search_field)
                    time.sleep(1)
                    
                    # Resaltar para verificación visual
                    driver.execute_script("arguments[0].style.border='3px solid red';", search_field)
                    driver.save_screenshot(f"campo_resaltado_intento{retry+1}.png")
                    
                    # CRÍTICO: Interactuar con JavaScript para evitar errores de stale element
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
                    
                    # Tomar captura después de la búsqueda
                    driver.save_screenshot(f"resultados_busqueda_intento{retry+1}.png")
                    
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
                                # Buscar específicamente botones "Ver detalle" como en la imagen
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
                                        # Usar FindElements para no causar excepción si no hay resultados
                                        detail_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                                        for btn in detail_buttons:
                                            if btn.is_displayed():
                                                logger.info(f"Botón 'Ver detalle' encontrado con selector: {selector}")
                                                # Tomar captura antes de hacer clic
                                                driver.execute_script("arguments[0].style.border='3px solid red';", btn)
                                                driver.save_screenshot("boton_ver_detalle_encontrado.png")
                                                
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
                                                driver.save_screenshot("pagina_detalle_producto.png")
                                                # Guardar HTML para análisis
                                                with open("detalle_producto.html", "w", encoding="utf-8") as f:
                                                    f.write(driver.page_source)
                                                return True
                                    except Exception as e:
                                        logger.warning(f"Error con selector {selector}: {e}")
                                
                                # Si no encontramos botones específicos de detalle, buscar por texto
                                if not detail_button_found:
                                    try:
                                        # Intentar encontrar por XPath texto exacto "Ver detalle"
                                        xpath_buttons = driver.find_elements(By.XPATH, "//*[text()='Ver detalle']")
                                        for btn in xpath_buttons:
                                            if btn.is_displayed():
                                                logger.info("Botón 'Ver detalle' encontrado por XPath texto exacto")
                                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                                time.sleep(1)
                                                driver.execute_script("arguments[0].click();", btn)
                                                time.sleep(3)
                                                driver.save_screenshot("detalle_xpath_texto.png")
                                                return True
                                    except Exception as e:
                                        logger.warning(f"Error al buscar por XPath texto: {e}")
                                
                                # Si llegamos hasta aquí, intentar interactuar con la tarjeta del producto
                                product_card_selectors = [
                                    ".product-item", ".product-card", ".col-lg-12", 
                                    ".owl-item", ".producto", ".card"
                                ]
                                
                                for selector in product_card_selectors:
                                    try:
                                        cards = driver.find_elements(By.CSS_SELECTOR, selector)
                                        for card in cards:
                                            if card.is_displayed():
                                                # Buscar el botón "Ver detalle" dentro de la tarjeta
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
                                                    logger.info("Botón 'Ver detalle' encontrado dentro de tarjeta de producto")
                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ver_detalle_btn)
                                                    time.sleep(1)
                                                    driver.execute_script("arguments[0].click();", ver_detalle_btn)
                                                    time.sleep(3)
                                                    driver.save_screenshot("detalle_desde_tarjeta.png")
                                                    return True
                                                else:
                                                    # Si no encontramos el botón específico, guardar una lista de todos los elementos interactivos
                                                    clickable_elements = card.find_elements(By.CSS_SELECTOR, "a, button")
                                                    for i, elem in enumerate(clickable_elements):
                                                        try:
                                                            if elem.is_displayed():
                                                                logger.info(f"Elemento clickeable {i} en tarjeta: texto='{elem.text}', clase='{elem.get_attribute('class')}'")
                                                        except:
                                                            pass
                                                    
                                                    # Intentar hacer clic en el último botón visible (suele ser "Ver detalle")
                                                    visible_buttons = [btn for btn in detail_btns if btn.is_displayed()]
                                                    if visible_buttons:
                                                        last_button = visible_buttons[-1]
                                                        logger.info(f"Haciendo clic en último botón visible: '{last_button.text}'")
                                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", last_button)
                                                        time.sleep(1)
                                                        driver.execute_script("arguments[0].click();", last_button)
                                                        time.sleep(3)
                                                        driver.save_screenshot("detalle_ultimo_boton.png")
                                                        return True
                                    except Exception as e:
                                        logger.warning(f"Error al interactuar con tarjeta de producto {selector}: {e}")
                            except Exception as e:
                                logger.warning(f"Error al intentar hacer clic en resultados: {e}")
                            
                            # Incluso si no podemos hacer clic, consideramos exitosa la búsqueda si hay resultados
                            return True
                    else:
                        logger.warning(f"No se encontró evidencia de que la búsqueda '{nombre_producto}' se procesara")
                        
                    # Si llegamos aquí, intentamos otra vez con otro enfoque
                    logger.info("Intentando otro enfoque para la búsqueda...")
                else:
                    logger.warning("Campo de búsqueda no encontrado o no visible en este intento")
            
            except Exception as e:
                logger.error(f"Error en intento #{retry+1}: {e}")
                driver.save_screenshot(f"error_intento_{retry+1}.png")
            
            # Esperar antes del siguiente intento
            time.sleep(2)
        
        # PLAN B: Si todos los intentos anteriores fallaron, intentar con un enfoque completamente diferente
        logger.info("Intentando enfoque alternativo de búsqueda...")
        
        try:
            # Verificar si estamos en la página principal
            if "carrito.fanasa.com" in driver.current_url and "/login" not in driver.current_url:
                logger.info("Estamos en la página principal, intentando interactuar directamente")
                
                # Método 1: Ejecutar JavaScript para simular una búsqueda directa
                try:
                    logger.info("Intentando buscar con JavaScript directo...")
                    # Este script busca el primer campo de texto visible y lo usa para buscar
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
                    driver.save_screenshot("busqueda_js_directa.png")
                except Exception as e:
                    logger.warning(f"Error en búsqueda JS: {e}")
                
                # Método 2: Usar coordenadas basadas en la imagen
                try:
                    logger.info("Intentando clic en coordenadas específicas del campo de búsqueda...")
                    # Basado en la imagen, el campo está aproximadamente en estas coordenadas
                    actions = webdriver.ActionChains(driver)
                    actions.move_by_offset(500, 100).click().perform()
                    time.sleep(1)
                    actions.send_keys(nombre_producto).perform()
                    time.sleep(1)
                    actions.send_keys(Keys.RETURN).perform()
                    logger.info("Búsqueda enviada por coordenadas")
                    time.sleep(3)
                    driver.save_screenshot("busqueda_por_coordenadas.png")
                except Exception as e:
                    logger.warning(f"Error en búsqueda por coordenadas: {e}")
                
                # Método 3: Intentar navegar directamente a la URL de búsqueda
                try:
                    logger.info("Navegando directamente a URL de búsqueda...")
                    # Intentar construir una URL de búsqueda basada en patrones comunes
                    base_url = driver.current_url.split('?')[0]
                    search_url = f"{base_url}?q={nombre_producto}"
                    logger.info(f"Navegando a: {search_url}")
                    driver.get(search_url)
                    time.sleep(3)
                    driver.save_screenshot("busqueda_directa_url.png")
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
        driver.save_screenshot("error_busqueda_general.png")
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
            'disponibilidad': 'Stock disponible',
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
        except Exception as e:
            logger.warning(f"Error extrayendo nombre: {e}")

        # PRECIO NETO
        try:
            precio_neto_elements = driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Precio Neto')]/following::*[contains(text(), '$')]")
            
            for element in precio_neto_elements:
                if element.is_displayed():
                    texto_precio = element.text.strip()
                    precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto_precio)
                    if precio_match:
                        info_producto['precio_neto'] = f"${precio_match.group(1)}"
                        logger.info(f"Precio Neto: {info_producto['precio_neto']}")
                        break
        except Exception as e:
            logger.warning(f"Error extrayendo precio: {e}")

        # LABORATORIO / FABRICANTE
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
        except Exception as e:
            logger.warning(f"Error extrayendo laboratorio: {e}")

        # IMAGEN DEL PRODUCTO
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
                            logger.info(f"URL de imagen: {info_producto['imagen']}")
                            break
        except Exception as e:
            logger.warning(f"Error extrayendo imagen: {e}")
            
        return info_producto
            
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
        dict: Diccionario con la información del medicamento o diccionario con error si no se encuentra
    """
    driver = None
    try:
        # 1. Iniciar sesión en FANASA
        logger.info(f"Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")
        
        driver = login_fanasa_carrito()
        if not driver:
            logger.error("No se pudo iniciar sesión en FANASA. Abortando búsqueda.")
            return {
                "error": "error_login", 
                "mensaje": "No se pudo iniciar sesión en FANASA",
                "estado": "error",
                "fuente": "FANASA"
            }
        
        # 2. Buscar el producto
        logger.info(f"Sesión iniciada. Buscando producto: '{nombre_medicamento}'")
        
        resultado_busqueda = buscar_producto(driver, nombre_medicamento)
        
        if not resultado_busqueda:
            logger.warning(f"No se pudo encontrar o acceder al producto: '{nombre_medicamento}'")
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
        logger.info("Extrayendo información del producto...")
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
            
            return info_producto
        else:
            # Si no se pudo extraer información, devolver respuesta estructurada
            return {
                "nombre": nombre_medicamento,
                "mensaje": f"No se pudo extraer información para {nombre_medicamento} en FANASA",
                "estado": "error_extraccion",
                "fuente": "FANASA",
                "disponibilidad": "Desconocida",
                "existencia": "0"
            }
        
    except Exception as e:
        logger.error(f"Error general durante el proceso: {e}")
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
            logger.info("Cerrando navegador...")
            driver.quit()

# Función para enviar mensajes a WhatsApp a través de Twilio
def enviar_whatsapp(mensaje, numero_destino="+5214778150806"):
    """
    Envía un mensaje a WhatsApp usando la API de Twilio.
    
    Args:
        mensaje (str): Mensaje a enviar
        numero_destino (str): Número de teléfono de destino con código de país
        
    Returns:
        bool: True si el mensaje se envió correctamente, False si hubo error
    """
    try:
        from twilio.rest import Client
        
        # Credenciales de Twilio (asegúrate de tenerlas configuradas en variables de entorno)
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID', 'AC82a4a1a2fcfb6c6eb8bae97258424166')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '1df91deab6d73e7ef8cace26d50cd9a8')
        twilio_whatsapp = os.environ.get('TWILIO_WHATSAPP', 'whatsapp:+14155238886')
        
        # Asegurarse de que el número de destino tenga el formato correcto
        if not numero_destino.startswith('whatsapp:'):
            numero_destino = f'whatsapp:{numero_destino}'
        
        # Inicializar cliente de Twilio
        client = Client(account_sid, auth_token)
        
        # Enviar mensaje
        message = client.messages.create(
            body=mensaje,
            from_=twilio_whatsapp,
            to=numero_destino
        )
        
        logger.info(f"Mensaje enviado a whatsapp:{numero_destino}. SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar mensaje WhatsApp: {e}")
        return False

# Para ejecutar como script independiente o como parte de un servicio
def main():
    import argparse
    import json
    import os
    
    # Configuración de argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Buscar información de medicamentos en FANASA')
    parser.add_argument('--medicamento', type=str, help='Nombre del medicamento a buscar')
    parser.add_argument('--output', type=str, help='Archivo de salida para los resultados (JSON)')
    parser.add_argument('--headless', action='store_true', help='Ejecutar en modo headless (sin interfaz gráfica)')
    parser.add_argument('--whatsapp', type=str, help='Número de WhatsApp para enviar resultados (+521XXXXXXXXXX)')
    
    args = parser.parse_args()
    
    # Si no se especifica medicamento, solicitar entrada manual
    if not args.medicamento:
        medicamento = input("Ingrese el nombre del medicamento a buscar: ")
    else:
        medicamento = args.medicamento
    
    # Buscar información del medicamento
    print(f"\nBuscando información sobre: {medicamento}")
    print("Espere un momento...\n")
    
    info = buscar_info_medicamento(medicamento, headless=args.headless)
    
    # Determinar estado del resultado
    estado = info.get('estado', 'desconocido')
    
    # Crear mensaje según el estado
    if estado == 'encontrado':
        mensaje = f"✅ Producto encontrado en FANASA: {info.get('nombre', medicamento)}\n"
        mensaje += f"💊 Precio Neto: {info.get('precio_neto', 'No disponible')}\n"
        mensaje += f"📦 Disponibilidad: {info.get('disponibilidad', 'No especificada')}\n"
        mensaje += f"🏭 Laboratorio: {info.get('laboratorio', 'No especificado')}\n"
        
        # Mostrar en consola
        print("\n=== INFORMACIÓN DEL PRODUCTO ===")
        print(f"Nombre: {info.get('nombre', 'No disponible')}")
        print(f"Precio Neto: {info.get('precio_neto', 'No disponible')}")
        print(f"PMP: {info.get('pmp', 'No disponible')}")
        print(f"Laboratorio: {info.get('laboratorio', 'No disponible')}")
        print(f"SKU: {info.get('sku', 'No disponible')}")
        print(f"Disponibilidad: {info.get('disponibilidad', 'No disponible')}")
        if info.get('imagen'):
            print(f"Imagen: {info['imagen']}")
        print(f"URL: {info.get('url', 'No disponible')}")
        
        # Resultado para procesamiento
        resultado = "producto_encontrado"
    else:
        # Casos de error o producto no encontrado
        mensaje = f"❌ {info.get('mensaje', f'No se encontró información para {medicamento} en FANASA')}"
        
        # Mostrar en consola
        print("\n⚠️ " + mensaje)
        
        # Resultado para procesamiento
        resultado = "producto_no_encontrado"
    
    # Guardar resultados en archivo JSON si se especificó
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=4)
            print(f"\nResultados guardados en: {args.output}")
        except Exception as e:
            print(f"\n❌ Error al guardar resultados: {e}")
    
    # Enviar notificación por WhatsApp si se especificó un número
    if args.whatsapp:
        print(f"\nEnviando notificación a WhatsApp: {args.whatsapp}")
        enviar_whatsapp(mensaje, args.whatsapp)
    
    return resultado, info

if __name__ == "__main__":
    main()
