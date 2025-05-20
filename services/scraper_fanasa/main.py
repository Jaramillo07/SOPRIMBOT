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
TIMEOUT = 20                       # Tiempo de espera para elementos (segundos)



def inicializar_navegador(headless=False):
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
    driver = inicializar_navegador(headless=False)  # Usar False para ver el proceso visualmente
    if not driver:
        logger.error("No se pudo inicializar el navegador. Abortando.")
        return None
    
    try:
        # 1. Navegar a la página de login
        logger.info(f"Navegando a la página de login: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        time.sleep(5)  # Esperar a que cargue la página
        
        # Tomar captura de pantalla inicial
        driver.save_screenshot("01_fanasa_carrito_login_inicio.png")
        logger.info("Captura de pantalla guardada: 01_fanasa_carrito_login_inicio.png")
        
        # 2. Buscar campo de usuario
        logger.info("Buscando campo de usuario...")
        
        # Basado en la captura, el campo tiene una etiqueta "Usuario o correo"
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
            driver.save_screenshot("error_no_campo_usuario.png")
            return None
        
        # Limpiar e ingresar el usuario
        username_field.clear()
        username_field.send_keys(USERNAME)
        logger.info(f"Usuario ingresado: {USERNAME}")
        time.sleep(1)
        
        # Tomar captura después de ingresar el usuario
        driver.save_screenshot("02_fanasa_carrito_usuario_ingresado.png")
        
        # 3. Buscar campo de contraseña
        logger.info("Buscando campo de contraseña...")
        
        # Basado en la captura, es un campo con etiqueta "Contraseña"
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
            driver.save_screenshot("error_no_campo_password.png")
            return None
        
        # Limpiar e ingresar la contraseña
        password_field.clear()
        password_field.send_keys(PASSWORD)
        logger.info("Contraseña ingresada")
        time.sleep(1)
        
        # Tomar captura después de ingresar la contraseña
        driver.save_screenshot("03_fanasa_carrito_password_ingresado.png")
        
        # 4. Buscar botón de inicio de sesión (basado en la captura es un botón azul)
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
            driver.save_screenshot("04_fanasa_carrito_enviado_con_enter.png")
        else:
            # Hacer clic en el botón
            try:
                # Resaltar el botón para identificarlo en la captura
                driver.execute_script("arguments[0].style.border='2px solid red'", login_button)
                driver.save_screenshot("04a_fanasa_carrito_boton_resaltado.png")
                
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
            driver.save_screenshot("04b_fanasa_carrito_despues_clic.png")
        
        # 5. Verificar si el login fue exitoso
        current_url = driver.current_url
        logger.info(f"URL actual después del intento de login: {current_url}")
        
        # Guardar HTML para análisis
        with open("fanasa_carrito_despues_login.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("HTML después del login guardado para análisis")
        
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
            logger.info("┌─────────────────────────────────────┐")
            logger.info("│ ¡LOGIN EXITOSO EN FANASA CARRITO!   │")
            logger.info("└─────────────────────────────────────┘")
            
            # Tomar una última captura después del login exitoso
            driver.save_screenshot("05_fanasa_carrito_login_exitoso.png")
            
            return driver
        else:
            logger.error("┌─────────────────────────────────────┐")
            logger.error("│ ERROR: Login en FANASA Carrito fallido │")
            logger.error("└─────────────────────────────────────┘")
            
            if has_error:
                logger.error("Se detectaron mensajes de error en la página")
            
            driver.save_screenshot("error_login_fallido.png")
            driver.quit()
            return None
        
    except Exception as e:
        logger.error(f"Error durante el proceso de login: {e}")
        if driver:
            driver.save_screenshot("error_general_login.png")
            driver.quit()
        return None

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en FANASA.
    
    Args:
        driver: WebDriver con sesión iniciada
        nombre_producto: Nombre del producto a buscar
        
    Returns:
        bool: True si se encontraron resultados
    """
    if not driver:
        logger.error("❌ Driver no válido para búsqueda")
        return False
    
    try:
        logger.info(f"🔍 Iniciando búsqueda de producto: {nombre_producto}")
        
        # Esperar a que la página principal esté cargada
        time.sleep(3)
        driver.save_screenshot("pagina_principal.png")
        
        # Buscar el input de búsqueda por varios selectores posibles
        search_field = None
        search_selectors = [
            "input[placeholder*='Nombre, laboratorio']",
            "input[placeholder*='nombre']",
            "input.search_input",
            "input[name='parametro1']",
            ".search input"
        ]
        
        for selector in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        search_field = element
                        logger.info(f"Campo de búsqueda encontrado con selector: {selector}")
                        break
                if search_field:
                    break
            except:
                continue
        
        if not search_field:
            # Si no se encuentra con CSS, intentar con XPath
            try:
                search_field = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Nombre') or contains(@placeholder, 'nombre')]")
                logger.info("Campo de búsqueda encontrado con XPath")
            except:
                pass
        
        # Si todavía no lo encuentra, buscar en el DOM por atributos
        if not search_field:
            try:
                # Buscar mediante navegación desde el formulario
                forms = driver.find_elements(By.TAG_NAME, "form")
                for form in forms:
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.is_displayed() and inp.get_attribute("type") == "text":
                            search_field = inp
                            logger.info("Campo de búsqueda encontrado dentro de formulario")
                            break
                    if search_field:
                        break
            except:
                pass
        
        # Como último recurso, probar con cualquier input visible
        if not search_field:
            try:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in all_inputs:
                    if inp.is_displayed() and inp.get_attribute("type") != "hidden":
                        search_field = inp
                        logger.info("Usando primer campo input visible como campo de búsqueda")
                        break
            except:
                pass
        
        if not search_field:
            logger.error("No se pudo encontrar el campo de búsqueda")
            driver.save_screenshot("error_no_campo_busqueda.png")
            return False
        
        # Resaltar el campo de búsqueda en la captura
        driver.execute_script("arguments[0].style.border='3px solid red'", search_field)
        driver.save_screenshot("campo_busqueda_encontrado.png")
        
        # Limpiar e ingresar el término de búsqueda
        search_field.clear()
        search_field.send_keys(nombre_producto)
        logger.info(f"Texto '{nombre_producto}' ingresado en campo de búsqueda")
        
        # Esperar un momento para que se registre el texto
        time.sleep(2)
        
        # Método 1: Presionar Enter para enviar la búsqueda
        search_field.send_keys(Keys.RETURN)
        logger.info("Búsqueda enviada con tecla Enter")
        
        # Esperar a que se carguen los resultados
        time.sleep(5)
        
        # Tomar captura de la página de resultados
        driver.save_screenshot("resultados_busqueda.png")
        
        # Verificar la presencia de productos en la página
        # Buscar elementos que indiquen productos
        product_indicators = [
            "//h4[contains(text(), 'ZOLADEX') or contains(text(), 'PARACETAMOL') or contains(text(), '" + nombre_producto.upper() + "')]",
            "//div[contains(@class, 'card')]",
            "//div[contains(@class, 'producto')]",
            "//button[contains(text(), 'Agregar a carrito')]",
            "//div[contains(text(), 'Precio Neto')]",
            "//div[contains(text(), 'Precio Público')]"
        ]
        
        for indicator in product_indicators:
            elements = driver.find_elements(By.XPATH, indicator)
            if elements and any(e.is_displayed() for e in elements):
                logger.info(f"✅ Productos encontrados mediante indicador: {indicator}")
                return True
        
        # Si no se encuentran indicadores específicos, verificar si hay resultados en general
        if nombre_producto.lower() in driver.page_source.lower():
            logger.info("✅ El término de búsqueda aparece en la página de resultados")
            return True
        else:
            logger.warning("⚠️ No se encontraron productos que coincidan con la búsqueda")
            return False
            
    except Exception as e:
        logger.error(f"⚠️ Error durante la búsqueda: {e}")
        driver.save_screenshot("error_busqueda.png")
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
        logger.error("No se proporcionó un navegador válido")
        return None
    
    try:
        logger.info(f"Extrayendo información del producto #{numero_producto}")
        
        # Guardar página para análisis
        driver.save_screenshot(f"pagina_resultados_producto_{numero_producto}.png")
        
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
            cards = driver.find_elements(By.XPATH, selector)
            visible_cards = [card for card in cards if card.is_displayed()]
            if visible_cards:
                product_cards = visible_cards
                logger.info(f"Encontradas {len(product_cards)} tarjetas de productos con selector: {selector}")
                break
        
        if not product_cards:
            logger.warning("No se encontraron tarjetas de productos. Intentando extraer de toda la página.")
            # Si no hay tarjetas, intentar extraer de la página completa
            product_card = driver.find_element(By.TAG_NAME, "body")
        else:
            # Seleccionar la tarjeta según el índice proporcionado
            if numero_producto < len(product_cards):
                product_card = product_cards[numero_producto]
                logger.info(f"Seleccionando producto #{numero_producto}")
                # Resaltar el producto seleccionado
                driver.execute_script("arguments[0].style.border='3px solid green'", product_card)
                driver.save_screenshot(f"tarjeta_producto_{numero_producto}_seleccionada.png")
            else:
                logger.warning(f"Índice {numero_producto} fuera de rango. Solo hay {len(product_cards)} productos. Usando el primero.")
                product_card = product_cards[0]
        
        # Extraer NOMBRE del producto
        try:
            nombre_elements = product_card.find_elements(By.XPATH, 
                ".//h4 | .//h2 | .//h3 | .//h5[contains(@class, 'Name-product')] | .//h5[contains(@class, 'name-product')] | .//h5[contains(@class, 'mb-2')] | .//div[contains(@class, 'name-product')] | .//div[contains(@class, 'product-name')] | .//strong[contains(text(), 'PARACETAMOL')] | .//strong[contains(text(), 'ZOLADEX')]")
            
            for element in nombre_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    if texto and len(texto) > 5 and "regresar" not in texto.lower():
                        info_producto['nombre'] = texto
                        logger.info(f"Nombre del producto: {info_producto['nombre']}")
                        break
            
            # Si no encontramos el nombre con los selectores anteriores, intentar con clases específicas
            if not info_producto['nombre']:
                nombre_class_elements = product_card.find_elements(By.CSS_SELECTOR, 
                    ".name-product, .product-name, .mb-2, .Name-product, h5.font-weight-bold")
                
                for element in nombre_class_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        if texto and len(texto) > 5 and "regresar" not in texto.lower():
                            info_producto['nombre'] = texto
                            logger.info(f"Nombre del producto (por clase): {info_producto['nombre']}")
                            break
                            
            # Si todavía no tenemos nombre, intentar con el texto visible más largo
            if not info_producto['nombre']:
                visible_texts = []
                all_elements = product_card.find_elements(By.XPATH, ".//*")
                for element in all_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        if texto and len(texto) > 10 and "precio" not in texto.lower() and "$" not in texto:
                            visible_texts.append((len(texto), texto))
                
                if visible_texts:
                    # Ordenar por longitud (el texto más largo primero)
                    visible_texts.sort(reverse=True)
                    info_producto['nombre'] = visible_texts[0][1]
                    logger.info(f"Nombre del producto (texto más largo): {info_producto['nombre']}")
        except Exception as e:
            logger.warning(f"Error extrayendo nombre: {e}")
        
        # Extraer PRECIOS
        try:
            # Buscar Precio Neto
            precio_neto_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Precio Neto')]/following-sibling::* | .//h5[contains(text(), 'Precio Neto')]/following-sibling::*")
            
            for element in precio_neto_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    precio_match = re.search(r'\$?([\d,]+\.?\d*)', texto)
                    if precio_match:
                        info_producto['precio_neto'] = f"${precio_match.group(1)}"
                        logger.info(f"Precio Neto: {info_producto['precio_neto']}")
                        break
            
            # Si no encontramos precio neto con el texto explícito, buscar por posición o por clase
            if not info_producto['precio_neto']:
                precio_elements = product_card.find_elements(By.XPATH, ".//*[contains(text(), '$')]")
                for element in precio_elements:
                    if element.is_displayed():
                        parent = element.find_element(By.XPATH, "..")
                        if "neto" in parent.text.lower():
                            precio_match = re.search(r'\$?([\d,]+\.?\d*)', element.text)
                            if precio_match:
                                info_producto['precio_neto'] = f"${precio_match.group(1)}"
                                logger.info(f"Precio Neto (desde elemento): {info_producto['precio_neto']}")
                                break
            
            # Extraer Precio PMP
            pmp_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'PMP')]/following-sibling::* | .//h6[contains(text(), 'PMP')]/following-sibling::*")
            
            for element in pmp_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    precio_match = re.search(r'\$?([\d,]+\.?\d*)', texto)
                    if precio_match:
                        info_producto['pmp'] = f"${precio_match.group(1)}"
                        logger.info(f"PMP: {info_producto['pmp']}")
                        break
            
            # Extraer Precio Público
            precio_publico_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Precio Público')]/following-sibling::* | .//h5[contains(text(), 'Precio Público')]/following-sibling::* | .//h6[contains(text(), 'Precio Público')]")
            
            for element in precio_publico_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    if not texto:  # Si el elemento no tiene texto, buscar en su siguiente hermano
                        try:
                            next_sibling = element.find_element(By.XPATH, "following-sibling::*")
                            texto = next_sibling.text.strip()
                        except:
                            continue
                    
                    precio_match = re.search(r'\$?([\d,]+\.?\d*)', texto)
                    if precio_match:
                        info_producto['precio_publico'] = f"${precio_match.group(1)}"
                        logger.info(f"Precio Público: {info_producto['precio_publico']}")
                        break
            
            # Extraer Precio Farmacia
            precio_farmacia_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Precio Farmacia')]/following-sibling::* | .//h5[contains(text(), 'Precio Farmacia')]/following-sibling::* | .//h6[contains(text(), 'Precio Farmacia')]")
            
            for element in precio_farmacia_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    if not texto:  # Si el elemento no tiene texto, buscar en su siguiente hermano
                        try:
                            next_sibling = element.find_element(By.XPATH, "following-sibling::*")
                            texto = next_sibling.text.strip()
                        except:
                            continue
                    
                    precio_match = re.search(r'\$?([\d,]+\.?\d*)', texto)
                    if precio_match:
                        info_producto['precio_farmacia'] = f"${precio_match.group(1)}"
                        logger.info(f"Precio Farmacia: {info_producto['precio_farmacia']}")
                        break
        except Exception as e:
            logger.warning(f"Error extrayendo precios: {e}")
        
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
                        info_producto['sku'] = codigo_match.group(0)  # Usar mismo valor para sku
                        logger.info(f"Código/SKU: {info_producto['codigo']}")
                        break
            
            # Si no encontramos con el método anterior, buscar elementos con números largos
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
                                logger.info(f"Código/SKU (de elemento genérico): {info_producto['codigo']}")
                                break
        except Exception as e:
            logger.warning(f"Error extrayendo código/SKU: {e}")
        
        # Extraer LABORATORIO
        try:
            # Buscar explícitamente por texto "Laboratorio:"
            lab_elements = product_card.find_elements(By.XPATH, 
                ".//div[contains(text(), 'Laboratorio')]/following-sibling::* | .//div[contains(text(), 'LABORATORIO')]")
            
            for element in lab_elements:
                if element.is_displayed():
                    texto = element.text.strip()
                    # Si es el elemento que contiene "Laboratorio:", extraer solo la parte del laboratorio
                    if "laboratorio:" in texto.lower():
                        lab_match = re.search(r'laboratorio:?\s*(.+)', texto, re.IGNORECASE)
                        if lab_match:
                            info_producto['laboratorio'] = lab_match.group(1).strip()
                            logger.info(f"Laboratorio: {info_producto['laboratorio']}")
                            break
                    elif len(texto) > 3 and "$" not in texto:
                        info_producto['laboratorio'] = texto
                        logger.info(f"Laboratorio: {info_producto['laboratorio']}")
                        break
        except Exception as e:
            logger.warning(f"Error extrayendo laboratorio: {e}")
        
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
                            logger.info(f"Disponibilidad: {info_producto['disponibilidad']}")
                            break
                        elif "stock" in texto.lower() or "existencias" in texto.lower():
                            info_producto['disponibilidad'] = texto
                            logger.info(f"Disponibilidad (texto completo): {info_producto['disponibilidad']}")
                            break
            
            # Si no encontramos stock específico, buscar en toda la tarjeta
            if not info_producto['disponibilidad']:
                card_text = product_card.text.lower()
                if "disponibles" in card_text:
                    stock_match = re.search(r'(\d+)\s*disponibles', card_text)
                    if stock_match:
                        info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                        logger.info(f"Disponibilidad (de texto de tarjeta): {info_producto['disponibilidad']}")
                elif "stock" in card_text:
                    stock_match = re.search(r'stock[:\s]*(\d+)', card_text)
                    if stock_match:
                        info_producto['disponibilidad'] = f"Stock ({stock_match.group(1)})"
                        logger.info(f"Disponibilidad (stock en texto): {info_producto['disponibilidad']}")
                else:
                    # Usar valor predeterminado
                    info_producto['disponibilidad'] = "Stock disponible"
                    logger.info("Usando valor predeterminado para disponibilidad")
        except Exception as e:
            logger.warning(f"Error extrayendo disponibilidad: {e}")
            info_producto['disponibilidad'] = "Stock disponible"
        
        # Extraer IMAGEN del producto
        try:
            img_elements = product_card.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                if img.is_displayed():
                    src = img.get_attribute("src")
                    if src and ("http" in src) and img.size['width'] > 50 and img.size['height'] > 50:
                        info_producto['imagen'] = src
                        logger.info(f"URL de imagen: {info_producto['imagen']}")
                        break
        except Exception as e:
            logger.warning(f"Error extrayendo imagen: {e}")
        
        # Verificar información mínima
        info_minima = (info_producto['precio_neto'] or info_producto['precio_publico'] or info_producto['precio_farmacia'] or info_producto['pmp']) and info_producto['codigo']

        if info_minima:
            # Si tenemos precios y código pero no nombre, usar un nombre genérico
            if not info_producto['nombre'] and info_producto['codigo']:
                info_producto['nombre'] = f"Producto {info_producto['codigo']}"
                logger.info(f"Usando código como nombre: {info_producto['nombre']}")
            
            logger.info("✅ Información mínima del producto extraída con éxito")
            return info_producto
        else:
            logger.warning("⚠️ No se pudo extraer información mínima de precios o código")
            return info_producto
    
    except Exception as e:
        logger.error(f"Error general extrayendo información: {e}")
        driver.save_screenshot("error_extraccion_general.png")
        return None

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en FANASA.
    Adaptada para integrarse con el servicio de scraping.
    
    Args:
        nombre_medicamento (str): Nombre del medicamento a buscar
        headless (bool): Si es True, el navegador se ejecuta en modo headless
        
    Returns:
        dict: Diccionario con la información del medicamento en formato compatible
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

if __name__ == "__main__":
    print("=== Script de Login y Scraping para FANASA Carrito ===")
    print(f"Iniciando sesión con el usuario: {USERNAME}")
    
    # Ejecutar el login
    driver = login_fanasa_carrito()
    
    if driver:
        print("\n✅ ¡Login exitoso en FANASA Carrito!")
        
        # Preguntar si se desea buscar un producto
        buscar = input("\n¿Deseas buscar un producto? (s/n): ").lower()
        
        if buscar == 's':
            nombre_producto = input("Ingresa el nombre del producto a buscar: ")
            
            if buscar_producto(driver, nombre_producto):
                print(f"\n✅ Búsqueda realizada para: {nombre_producto}")
                
                # Extraer información del PRIMER producto automáticamente (índice 0)
                info = extraer_info_productos(driver, 0)
                
                if info:
                    print("\n" + "="*50)
                    print("         INFORMACIÓN DEL PRODUCTO")
                    print("="*50)
                    
                    # Mostrar información en un formato más ordenado
                    if info['nombre']:
                        print(f"\n🏷️  NOMBRE: {info['nombre']}")
                    
                    print("\n💰 PRECIOS:")
                    if info['precio_neto']:
                        print(f"   ▪ Precio Neto: {info['precio_neto']}")
                    if info['pmp']:
                        print(f"   ▪ PMP: {info['pmp']}")
                    if info['precio_publico']:
                        print(f"   ▪ Precio Público: {info['precio_publico']}")
                    if info['precio_farmacia']:
                        print(f"   ▪ Precio Farmacia: {info['precio_farmacia']}")
                    
                    if info['sku'] or info['codigo']:
                        print(f"\n🔢 SKU/CÓDIGO: {info['sku'] or info['codigo']}")
                    
                    if info['laboratorio']:
                        print(f"\n🏭 LABORATORIO: {info['laboratorio']}")
                    
                    if info['disponibilidad']:
                        print(f"\n📦 DISPONIBILIDAD: {info['disponibilidad']}")
                    
                    if info['imagen']:
                        print(f"\n🖼️  URL DE IMAGEN: {info['imagen']}")
                    
                    print(f"\n🔗 URL DEL PRODUCTO: {info['url']}")
                    
                    print("\n" + "="*50)
                    
                    # Preguntar si desea guardar la información en un archivo
                    guardar = input("\n¿Deseas guardar esta información en un archivo? (s/n): ").lower()
                    if guardar == 's':
                        try:
                            import json
                            from datetime import datetime
                            
                            # Crear un nombre de archivo basado en el nombre del producto y fecha
                            fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            nombre_archivo = f"{info['nombre'] if info['nombre'] else nombre_producto}_{fecha_hora}.json"
                            nombre_archivo = nombre_archivo.replace(" ", "_").replace("/", "_").replace("\\", "_")
                            
                            # Guardar como JSON
                            with open(nombre_archivo, "w", encoding="utf-8") as f:
                                json.dump(info, f, ensure_ascii=False, indent=4)
                            
                            print(f"\n✅ Información guardada en el archivo: {nombre_archivo}")
                        except Exception as e:
                            print(f"\n❌ Error al guardar información: {e}")
                else:
                    print("\n❌ No se pudo extraer información del producto.")
                    print("Revisa las capturas de pantalla y los logs para identificar el problema.")
            else:
                print(f"\n❌ No se pudo encontrar el producto: {nombre_producto}")
        
        # Preguntar si desea realizar otra búsqueda
        otra_busqueda = input("\n¿Deseas buscar otro producto? (s/n): ").lower()
        while otra_busqueda == 's':
            nombre_producto = input("\nIngresa el nombre del producto a buscar: ")
            
            if buscar_producto(driver, nombre_producto):
                print(f"\n✅ Búsqueda realizada para: {nombre_producto}")
                
                # Extraer información del PRIMER producto automáticamente (índice 0)
                info = extraer_info_productos(driver, 0)
                
                if info:
                    print("\n" + "="*50)
                    print("         INFORMACIÓN DEL PRODUCTO")
                    print("="*50)
                    
                    # Mostrar información en un formato más ordenado
                    if info['nombre']:
                        print(f"\n🏷️  NOMBRE: {info['nombre']}")
                    
                    print("\n💰 PRECIOS:")
                    if info['precio_neto']:
                        print(f"   ▪ Precio Neto: {info['precio_neto']}")
                    if info['pmp']:
                        print(f"   ▪ PMP: {info['pmp']}")
                    if info['precio_publico']:
                        print(f"   ▪ Precio Público: {info['precio_publico']}")
                    if info['precio_farmacia']:
                        print(f"   ▪ Precio Farmacia: {info['precio_farmacia']}")
                    
                    if info['sku'] or info['codigo']:
                        print(f"\n🔢 SKU/CÓDIGO: {info['sku'] or info['codigo']}")
                    
                    if info['laboratorio']:
                        print(f"\n🏭 LABORATORIO: {info['laboratorio']}")
                    
                    if info['disponibilidad']:
                        print(f"\n📦 DISPONIBILIDAD: {info['disponibilidad']}")
                    
                    if info['imagen']:
                        print(f"\n🖼️  URL DE IMAGEN: {info['imagen']}")
                    
                    print(f"\n🔗 URL DEL PRODUCTO: {info['url']}")
                    
                    print("\n" + "="*50)
                    
                    # Preguntar si desea guardar la información
                    guardar = input("\n¿Deseas guardar esta información en un archivo? (s/n): ").lower()
                    if guardar == 's':
                        try:
                            import json
                            from datetime import datetime
                            
                            # Crear nombre de archivo
                            fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                            nombre_archivo = f"{info['nombre'] if info['nombre'] else nombre_producto}_{fecha_hora}.json"
                            nombre_archivo = nombre_archivo.replace(" ", "_").replace("/", "_").replace("\\", "_")
                            
                            # Guardar como JSON
                            with open(nombre_archivo, "w", encoding="utf-8") as f:
                                json.dump(info, f, ensure_ascii=False, indent=4)
                            
                            print(f"\n✅ Información guardada en el archivo: {nombre_archivo}")
                        except Exception as e:
                            print(f"\n❌ Error al guardar información: {e}")
                else:
                    print("\n❌ No se pudo extraer información del producto.")
            else:
                print(f"\n❌ No se pudo encontrar el producto: {nombre_producto}")
            
            otra_busqueda = input("\n¿Deseas buscar otro producto? (s/n): ").lower()
        
        # Mantener el navegador abierto para inspección manual
        input("\nPresiona Enter para cerrar el navegador... ")
        driver.quit()
        print("Navegador cerrado. Proceso finalizado.")
    else:
        print("\n❌ Error durante el login en FANASA Carrito.")
        print("Revisa las capturas de pantalla y los logs para identificar el problema.")
