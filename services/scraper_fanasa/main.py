#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import re
import os # Para la recuperación de logs en disponibilidad (opcional)
import json # Para guardar en JSON
from datetime import datetime # Para el nombre de archivo

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager # Descomenta si usas webdriver-manager


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
USERNAME = "ventas@insumosjip.com"  # Usuario para FANASA
PASSWORD = "210407"                  # Contraseña para FANASA
LOGIN_URL = "https://carrito.fanasa.com/login"  # URL correcta del portal de carrito
WEBDRIVER_TIMEOUT = 20               # Tiempo de espera para elementos (segundos) (Renombrado desde TIMEOUT)

def inicializar_navegador(headless=False):
    """
    Inicializa el navegador Chrome con opciones configuradas.
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu") # A menudo necesario para headless en algunos sistemas

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox") # Necesario para algunos entornos (ej. Docker)
    options.add_argument("--disable-dev-shm-usage") # Necesario para algunos entornos (ej. Docker)
    options.add_argument("--log-level=3") # Reducir logs de Chrome/ChromeDriver en consola
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # Para logs de Chrome

    try:
        # Opción 1: Usar webdriver-manager (recomendado para facilidad)
        # Descomenta la siguiente línea y la importación de ChromeDriverManager si lo tienes instalado
        # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # Opción 2: Especificar la ruta a chromedriver (si no usas webdriver-manager)
        # Asegúrate de que chromedriver esté en tu PATH o proporciona la ruta aquí:
        # driver_path = "/path/to/your/chromedriver" # ¡CAMBIA ESTO!
        # service = ChromeService(executable_path=driver_path)
        # driver = webdriver.Chrome(service=service, options=options)

        # Opción 3: Asumir que chromedriver está en el PATH (como lo tenías)
        driver = webdriver.Chrome(options=options)

        logger.info("Navegador Chrome inicializado correctamente")
        return driver
    except Exception as e:
        logger.error(f"Error al inicializar el navegador: {e}")
        return None

def login_fanasa_carrito():
    """
    Realiza el proceso de login en el portal de carrito de FANASA.
    """
    driver = inicializar_navegador(headless=False)  # False para ver el proceso visualmente
    if not driver:
        logger.error("No se pudo inicializar el navegador. Abortando.")
        return None

    try:
        logger.info(f"Navegando a la página de login: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        WebDriverWait(driver, WEBDRIVER_TIMEOUT).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='Usuario o correo']"))
        )
        driver.save_screenshot("01_fanasa_carrito_login_inicio.png")
        logger.info("Captura de pantalla guardada: 01_fanasa_carrito_login_inicio.png")

        username_field = None
        username_selectors = [
            "input[placeholder='Usuario o correo']",
            "#email",
            "input[type='email']",
        ]
        for selector in username_selectors:
            try:
                field = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                if field.is_displayed():
                    username_field = field
                    logger.info(f"Campo de usuario encontrado con selector: {selector}")
                    break
            except TimeoutException:
                logger.debug(f"Selector de usuario no encontrado o no visible: {selector}")
                continue
        
        if not username_field: # Intento más genérico si fallan los específicos
            try:
                logger.info("Intentando encontrar campo de usuario genérico (primer input de texto visible)...")
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
                for inp in inputs:
                    if inp.is_displayed():
                        username_field = inp
                        logger.info("Campo de usuario encontrado como primer input de texto/email visible.")
                        break
            except Exception as e_gen_user:
                 logger.warning(f"Error buscando campo de usuario genérico: {e_gen_user}")


        if not username_field:
            logger.error("No se pudo encontrar el campo de usuario")
            driver.save_screenshot("error_no_campo_usuario.png")
            driver.quit()
            return None

        username_field.clear()
        username_field.send_keys(USERNAME)
        logger.info(f"Usuario ingresado: {USERNAME}")
        time.sleep(0.5) # Pequeña pausa
        driver.save_screenshot("02_fanasa_carrito_usuario_ingresado.png")

        password_field = None
        password_selectors = [
            "input[placeholder='Contraseña']",
            "#password",
            "input[type='password']",
        ]
        for selector in password_selectors:
            try:
                field = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                if field.is_displayed():
                    password_field = field
                    logger.info(f"Campo de contraseña encontrado con selector: {selector}")
                    break
            except TimeoutException:
                logger.debug(f"Selector de contraseña no encontrado o no visible: {selector}")
                continue
        
        if not password_field: # Intento más genérico
            try:
                logger.info("Intentando encontrar campo de contraseña genérico (primer input de password visible)...")
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                for inp in inputs:
                    if inp.is_displayed():
                        password_field = inp
                        logger.info("Campo de contraseña encontrado como primer input de password visible.")
                        break
            except Exception as e_gen_pass:
                logger.warning(f"Error buscando campo de contraseña genérico: {e_gen_pass}")

        if not password_field:
            logger.error("No se pudo encontrar el campo de contraseña")
            driver.save_screenshot("error_no_campo_password.png")
            driver.quit()
            return None

        password_field.clear()
        password_field.send_keys(PASSWORD)
        logger.info("Contraseña ingresada")
        time.sleep(0.5)
        driver.save_screenshot("03_fanasa_carrito_password_ingresado.png")

        login_button = None
        # Usar XPath para buscar por texto, ya que :contains no es estándar CSS
        button_xpaths = [
            "//button[contains(translate(., 'INICIARSESÓN', 'iniciarsesón'), 'iniciar sesión')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'btn-primary') and (contains(translate(., 'INICIARSESÓN', 'iniciarsesón'), 'iniciar') or contains(translate(., 'ENTRAR', 'entrar'), 'entrar'))]"
        ]
        for xpath in button_xpaths:
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                if button.is_displayed():
                    login_button = button
                    logger.info(f"Botón 'Iniciar sesión' encontrado con XPath: {xpath}")
                    break
            except TimeoutException:
                logger.debug(f"Botón de login no encontrado o no clickeable con XPath: {xpath}")
                continue
        
        if not login_button:
            logger.warning("No se encontró botón de inicio de sesión específico. Intentando enviar formulario con Enter desde el campo de contraseña.")
            try:
                password_field.send_keys(Keys.RETURN)
                time.sleep(3) # Esperar a que la página reaccione
                driver.save_screenshot("04_fanasa_carrito_enviado_con_enter.png")
            except Exception as e_enter:
                logger.error(f"Error al intentar enviar con Enter: {e_enter}")
                driver.save_screenshot("error_submit_enter.png")
                driver.quit()
                return None
        else:
            try:
                driver.execute_script("arguments[0].style.border='2px solid red'", login_button)
                driver.save_screenshot("04a_fanasa_carrito_boton_resaltado.png")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_button)
                time.sleep(0.5)
                login_button.click()
                logger.info("Clic en botón 'Iniciar sesión' realizado")
            except ElementClickInterceptedException:
                logger.warning("Clic interceptado. Intentando con JavaScript.")
                driver.execute_script("arguments[0].click();", login_button)
                logger.info("Clic en botón realizado con JavaScript")
            except Exception as e_click:
                logger.error(f"Error al hacer clic en el botón de login: {e_click}")
                driver.save_screenshot("error_clic_boton_login.png")
                driver.quit()
                return None
            time.sleep(3) # Esperar a que se procese el login
            driver.save_screenshot("04b_fanasa_carrito_despues_clic.png")

        current_url_after_login = driver.current_url
        logger.info(f"URL actual después del intento de login: {current_url_after_login}")
        with open("fanasa_carrito_despues_login.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("HTML después del login guardado para análisis")

        login_exitoso = "/login" not in current_url_after_login.lower()
        
        # Verificación adicional de login exitoso (ej. buscar "Cerrar sesión" o nombre de usuario)
        if not login_exitoso:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(translate(., 'CERRARSIN', 'cerrarsin'), 'cerrar sesión') or contains(translate(., 'MICUENTA', 'micuenta'), 'mi cuenta')]"))
                )
                logger.info("Indicador de sesión iniciada encontrado (Cerrar Sesión / Mi Cuenta).")
                login_exitoso = True
            except TimeoutException:
                logger.warning("No se encontró indicador claro de sesión iniciada (Cerrar Sesión / Mi Cuenta).")


        has_error_message = False
        try:
            error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'alert-danger') or contains(@class, 'text-danger')]")
            for error_el in error_elements:
                if error_el.is_displayed() and error_el.text.strip():
                    logger.error(f"Mensaje de error en página de login: {error_el.text.strip()}")
                    has_error_message = True
                    break
        except Exception:
            pass # No es crítico si no se pueden buscar mensajes de error

        if login_exitoso and not has_error_message:
            logger.info("┌─────────────────────────────────────┐")
            logger.info("│ ¡LOGIN EXITOSO EN FANASA CARRITO!   │")
            logger.info("└─────────────────────────────────────┘")
            driver.save_screenshot("05_fanasa_carrito_login_exitoso.png")
            return driver
        else:
            logger.error("┌─────────────────────────────────────┐")
            logger.error("│ ERROR: Login en FANASA Carrito fallido │")
            logger.error("└─────────────────────────────────────┘")
            if has_error_message:
                 logger.error("Se detectaron mensajes de error en la página, o la URL sigue siendo la de login.")
            elif not login_exitoso:
                logger.error("La URL no cambió o no se encontraron indicadores de sesión exitosa.")

            driver.save_screenshot("error_login_fallido_final.png")
            driver.quit()
            return None

    except Exception as e:
        logger.error(f"Error fatal durante el proceso de login: {e}", exc_info=True)
        if driver:
            driver.save_screenshot("error_general_login_fatal.png")
            driver.quit()
        return None

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en el sitio una vez que estamos logueados.
    """
    if not driver:
        logger.error("No se proporcionó un navegador válido para buscar producto")
        return False

    try:
        logger.info(f"Buscando producto: {nombre_producto}")
        # Esperar a que la página principal (post-login) cargue algún elemento distintivo
        try:
            WebDriverWait(driver, WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.search_input, input[placeholder*='Nombre'], input[type='search']")) # Un campo de búsqueda común
            )
            logger.info("Página principal (post-login) parece cargada.")
        except TimeoutException:
            logger.warning("Timeout esperando elemento distintivo de la página principal post-login. Continuando de todas formas...")
            # No es fatal, intentaremos buscar igualmente
        
        time.sleep(1) # Pequeña pausa adicional
        with open("pagina_principal_busqueda.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("pagina_principal_antes_busqueda.png")

        search_field = None
        search_selectors_css = [
            "input.search_input", # El que identificaste
            "input[placeholder='Nombre, laboratorio, sal, código de barras o Categoria']",
            "input.input-src",
            "input[type='search']",
            "input[name='q']",
            "#search"
        ]

        for i, selector in enumerate(search_selectors_css):
            try:
                logger.info(f"Intentando encontrar campo de búsqueda con CSS: {selector}")
                field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if field.is_displayed():
                    search_field = field
                    logger.info(f"Campo de búsqueda encontrado con CSS selector: {selector}")
                    break
            except TimeoutException:
                logger.debug(f"Campo de búsqueda no encontrado/clickeable con CSS: {selector}")
            except Exception as e_css_search:
                logger.warning(f"Excepción buscando campo con CSS {selector}: {e_css_search}")
        
        if not search_field:
             logger.warning("No se encontró el campo de búsqueda con selectores CSS comunes. Revisar 'pagina_principal_busqueda.html'.")
             # Intentar un XPath más genérico como último recurso para el campo
             try:
                logger.info("Intentando XPath genérico para campo de búsqueda...")
                search_field = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@type='text' and (@placeholder[contains(.,'buscar')] or @aria-label[contains(.,'buscar')])] | //input[@type='search']"))
                )
                if search_field.is_displayed():
                    logger.info("Campo de búsqueda encontrado con XPath genérico.")
             except Exception as e_xpath_search:
                 logger.error(f"No se pudo encontrar el campo de búsqueda con XPath genérico: {e_xpath_search}")
                 driver.save_screenshot("error_no_campo_busqueda.png")
                 return False


        if not search_field:
            logger.error("FALLO CRÍTICO: No se pudo encontrar el campo de búsqueda en la página.")
            driver.save_screenshot("error_fatal_no_campo_busqueda.png")
            return False

        driver.execute_script("arguments[0].style.border='3px solid red';", search_field)
        driver.save_screenshot("campo_busqueda_resaltado.png")
        
        logger.info(f"Intentando ingresar texto '{nombre_producto}' en el campo de búsqueda.")
        # Limpiar e ingresar texto usando JavaScript para mayor robustez
        driver.execute_script("arguments[0].value = ''; arguments[0].focus();", search_field) # Limpia y enfoca
        time.sleep(0.5)
        driver.execute_script("arguments[0].value = arguments[1];", search_field, nombre_producto)
        time.sleep(0.5)
        # Disparar evento input para que Angular/React detecten el cambio si es necesario
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_field)
        time.sleep(0.5)

        valor_ingresado = search_field.get_attribute("value")
        logger.info(f"Valor actual en el campo de búsqueda: '{valor_ingresado}'")
        
        if nombre_producto.lower() not in valor_ingresado.lower():
            logger.warning(f"El texto no parece haberse ingresado correctamente en el campo de búsqueda. Valor: '{valor_ingresado}'. Intentando send_keys.")
            search_field.clear() # Intentar clear normal
            search_field.send_keys(nombre_producto)
            time.sleep(0.5)
            valor_ingresado = search_field.get_attribute("value")
            logger.info(f"Valor después de send_keys: '{valor_ingresado}'")


        # Enviar la búsqueda
        try:
            logger.info("Enviando búsqueda con Keys.RETURN...")
            search_field.send_keys(Keys.RETURN)
        except Exception as e_return:
            logger.warning(f"Error enviando Keys.RETURN: {e_return}. Intentando clic en botón de búsqueda...")
            # Buscar un botón de búsqueda (lupa o similar)
            search_button_xpaths = [
                "//button[@type='submit' and (contains(.,'Buscar') or .//i[contains(@class,'search')])]",
                "//button[contains(@aria-label,'Buscar') or contains(@title,'Buscar')]",
                "//form[.//input[@value='{nombre_producto}']]//button[@type='submit']" # Botón submit dentro del form del input
            ]
            search_button_found_and_clicked = False
            for xpath in search_button_xpaths:
                try:
                    button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath.replace('{nombre_producto}', nombre_producto))))
                    logger.info(f"Botón de búsqueda encontrado con XPath: {xpath}. Haciendo clic...")
                    driver.execute_script("arguments[0].click();", button) # Clic con JS
                    search_button_found_and_clicked = True
                    break
                except:
                    logger.debug(f"Botón de búsqueda no encontrado con XPath: {xpath}")
            if not search_button_found_and_clicked:
                logger.error("No se pudo enviar la búsqueda (ni con Enter ni con botón).")
                driver.save_screenshot("error_envio_busqueda.png")
                return False
        
        logger.info("Búsqueda enviada. Esperando resultados...")
        time.sleep(3) # Esperar a que la página de resultados cargue
        driver.save_screenshot("resultados_busqueda_pagina.png")
        with open("resultados_busqueda.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # Verificar si hay resultados (esto es muy dependiente del sitio)
        # Aquí podrías buscar un contenedor de resultados o un mensaje de "No se encontraron productos"
        try:
            WebDriverWait(driver, WEBDRIVER_TIMEOUT).until(
                lambda d: "No se encontraron productos que concuerden con la búsqueda" not in d.page_source or \
                          d.find_elements(By.CSS_SELECTOR, ".product-item, .product-card, .item-producto") # Selectores comunes de items de producto
            )
        except TimeoutException:
            logger.warning("Timeout esperando resultados de búsqueda o mensaje de 'no resultados'.")
            # Podría ser que la página no cambió o tardó demasiado

        if "No se encontraron productos que concuerden con la búsqueda" in driver.page_source or \
           "No se pudo encontrar el producto" in driver.page_source: # Añadido de tu código
            logger.warning(f"Mensaje 'No se encontraron productos' detectado para: '{nombre_producto}'")
            return False

        # Si hay resultados, intentar hacer clic en el primero o en "Ver detalle"
        # Tu lógica para hacer clic en "Ver detalle" es muy completa, la adaptaré aquí.
        ver_detalle_selectors_css = [ # Cambiado a CSS donde sea posible
            "button.btn-outline-primary", # Como en tu imagen
            "a.ver-detalle",
            ".btn-ver-detalle"
        ]
        ver_detalle_xpaths = [
            "//button[contains(translate(., 'VERDETAL', 'verdetal'), 'ver detalle')]",
            "//a[contains(translate(., 'VERDETAL', 'verdetal'), 'ver detalle')]",
        ]

        detail_button_found_and_clicked = False
        # Primero CSS
        for selector in ver_detalle_selectors_css:
            try:
                detail_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in detail_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        logger.info(f"Botón/enlace 'Ver detalle' encontrado con CSS: {selector}")
                        driver.execute_script("arguments[0].style.border='3px solid lime';", btn)
                        driver.save_screenshot("boton_ver_detalle_resaltado.png")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", btn)
                        logger.info("Clic en 'Ver detalle' realizado con JavaScript.")
                        detail_button_found_and_clicked = True
                        break
                if detail_button_found_and_clicked: break
            except Exception as e_detail_css:
                logger.debug(f"Error con selector CSS para 'Ver detalle' {selector}: {e_detail_css}")
        
        # Luego XPath si CSS falló
        if not detail_button_found_and_clicked:
            for xpath in ver_detalle_xpaths:
                try:
                    detail_buttons = driver.find_elements(By.XPATH, xpath)
                    for btn in detail_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            logger.info(f"Botón/enlace 'Ver detalle' encontrado con XPath: {xpath}")
                            driver.execute_script("arguments[0].style.border='3px solid lime';", btn)
                            driver.save_screenshot("boton_ver_detalle_resaltado_xpath.png")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", btn)
                            logger.info("Clic en 'Ver detalle' realizado con JavaScript.")
                            detail_button_found_and_clicked = True
                            break
                    if detail_button_found_and_clicked: break
                except Exception as e_detail_xpath:
                    logger.debug(f"Error con selector XPath para 'Ver detalle' {xpath}: {e_detail_xpath}")

        if not detail_button_found_and_clicked:
            # Como último recurso, si no hay "Ver detalle", intentar hacer clic en el nombre del producto del primer resultado
            logger.warning("No se encontró botón/enlace 'Ver detalle'. Intentando clic en el nombre del primer producto.")
            product_link_selectors = [
                ".product-item-link", ".product-name a", ".woocommerce-LoopProduct-link",
                ".product-card .card-title a", ".item-producto .nombre a"
            ]
            for selector in product_link_selectors:
                try:
                    product_links = driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in product_links:
                        if link.is_displayed() and link.is_enabled() and link.text.strip():
                            logger.info(f"Enlace de producto encontrado: '{link.text.strip()}' con selector {selector}. Haciendo clic.")
                            driver.execute_script("arguments[0].click();", link)
                            detail_button_found_and_clicked = True
                            break
                    if detail_button_found_and_clicked: break
                except:
                    pass
            
        if not detail_button_found_and_clicked:
            logger.error("No se pudo hacer clic en ningún resultado de producto o botón 'Ver detalle'.")
            driver.save_screenshot("error_no_clic_resultado.png")
            return False

        # Esperar a que la página de detalle del producto cargue
        # (verificar por un elemento que DEBE estar en la página de detalle)
        try:
            WebDriverWait(driver, WEBDRIVER_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-name, .product-title, .product_view")) # Ajusta este selector
            )
            logger.info("Página de detalle del producto cargada.")
            driver.save_screenshot("pagina_detalle_producto_cargada.png")
            with open("pagina_detalle_producto.html", "w", encoding="utf-8") as f_detail:
                f_detail.write(driver.page_source)
            return True
        except TimeoutException:
            logger.error("Timeout esperando que cargue la página de detalle del producto después del clic.")
            driver.save_screenshot("error_timeout_pagina_detalle.png")
            return False

    except Exception as e:
        logger.error(f"Error general durante la búsqueda del producto '{nombre_producto}': {e}", exc_info=True)
        driver.save_screenshot(f"error_busqueda_general_{nombre_producto.replace(' ','_')}.png")
        return False


def extraer_info_producto(driver):
    """
    Extrae información detallada del producto de la página actual.
    (Esta es la versión más completa que proporcionaste)
    """
    if not driver:
        logger.error("No se proporcionó un navegador válido para extraer_info_producto")
        return None
    
    logger.info(f"Iniciando extracción de información desde: {driver.current_url}")
    # Esperar un momento para asegurar que todo el contenido dinámico haya cargado
    time.sleep(2) # Considera usar esperas explícitas para elementos específicos si es posible

    # Guardar HTML y captura para depuración
    try:
        with open("detalle_producto_para_extraccion.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("detalle_producto_para_extraccion.png")
        logger.info("HTML y captura de pantalla de la página de detalle guardados.")
    except Exception as e_io:
        logger.warning(f"No se pudo guardar HTML/captura de detalle: {e_io}")


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
            "h1.page-title span.base", # Magento
            "h1.product-name", "h1.product_title", "h1[itemprop='name']", # Comunes
            ".product-info-main .page-title-wrapper .page-title .base", # Magento
            "h1" # Genérico
        ]
        for selector in nombre_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        text = element.text.strip()
                        if len(text) > 3 and not any(stop_word in text.lower() for stop_word in ["detalle", "producto", "login", "carrito"]):
                            info_producto['nombre'] = text
                            logger.info(f"Nombre del producto: {info_producto['nombre']} (Selector: {selector})")
                            # driver.execute_script("arguments[0].style.border='3px solid green'", element) # Descomentar para debug visual
                            break
                if info_producto['nombre']: break
            except Exception as e_nombre_sel:
                logger.debug(f"Error con selector de nombre '{selector}': {e_nombre_sel}")
    except Exception as e_nombre:
        logger.warning(f"Error general extrayendo nombre: {e_nombre}")

    # PRECIO NETO
    try:
        # Estrategia 1: Buscar explícitamente "Precio Neto"
        precio_neto_xpath = [
            "//*[contains(translate(., 'PRECONIT', 'preconit'), 'precio neto')]/following::*[1][contains(text(),'$')]",
            "//*[contains(translate(., 'PRECONIT', 'preconit'), 'precio neto')]/ancestor::div[1]//*[contains(text(),'$')]"
        ]
        for xpath in precio_neto_xpath:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        match = re.search(r'\$\s*([\d,]+\.?\d*)', element.text)
                        if match:
                            info_producto['precio_neto'] = f"${match.group(1)}"
                            logger.info(f"Precio Neto (explícito XPath: {xpath}): {info_producto['precio_neto']}")
                            break
                if info_producto['precio_neto']: break
            except Exception: continue
        
        # Estrategia 2: Buscar precios que no sean PMP
        if not info_producto['precio_neto']:
            all_prices_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'$')]")
            candidate_net_prices = []
            for el in all_prices_elements:
                if el.is_displayed():
                    text_content = el.text.lower()
                    parent_text = ""
                    try: parent_text = el.find_element(By.XPATH, "..").text.lower()
                    except: pass

                    if "pmp" not in text_content and "público" not in text_content and \
                       "pmp" not in parent_text and "público" not in parent_text:
                        match = re.search(r'\$\s*([\d,]+\.?\d*)', el.text)
                        if match:
                            try:
                                candidate_net_prices.append(float(match.group(1).replace(",","")))
                            except ValueError: continue
            if candidate_net_prices:
                info_producto['precio_neto'] = f"${min(candidate_net_prices):.2f}"
                logger.info(f"Precio Neto (inferido, no PMP): {info_producto['precio_neto']}")

    except Exception as e_precio_n:
        logger.warning(f"Error extrayendo Precio Neto: {e_precio_n}")

    # PMP
    try:
        pmp_xpath = [
            "//*[contains(translate(., 'PMPÚBLICO', 'pmpúblico'), 'pmp')]/following::*[1][contains(text(),'$')]",
            "//*[contains(translate(., 'PMPÚBLICO', 'pmpúblico'), 'precio público')]/following::*[1][contains(text(),'$')]",
            "//*[contains(translate(., 'PMPÚBLICO', 'pmpúblico'), 'pmp')]/ancestor::div[1]//*[contains(text(),'$')]"
        ]
        for xpath in pmp_xpath:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed():
                        match = re.search(r'\$\s*([\d,]+\.?\d*)', element.text)
                        if match:
                            # Asegurarse de que no sea el mismo que el precio neto si ya se encontró
                            current_pmp_val = f"${match.group(1)}"
                            if current_pmp_val != info_producto.get('precio_neto', ''):
                                info_producto['pmp'] = current_pmp_val
                                logger.info(f"PMP (explícito XPath: {xpath}): {info_producto['pmp']}")
                                break
                if info_producto['pmp']: break
            except Exception: continue

        # Estrategia 2 PMP: si hay precio neto, PMP es el precio más alto diferente al neto
        if not info_producto['pmp'] and info_producto['precio_neto']:
            all_prices_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'$')]")
            candidate_pmp_prices = []
            net_price_float = float(info_producto['precio_neto'].replace("$","").replace(",",""))
            for el in all_prices_elements:
                 if el.is_displayed():
                    match = re.search(r'\$\s*([\d,]+\.?\d*)', el.text)
                    if match:
                        try:
                            val_float = float(match.group(1).replace(",",""))
                            if abs(val_float - net_price_float) > 0.01: # que sea diferente al neto
                                candidate_pmp_prices.append(val_float)
                        except ValueError: continue
            if candidate_pmp_prices:
                info_producto['pmp'] = f"${max(candidate_pmp_prices):.2f}"
                logger.info(f"PMP (inferido, precio más alto != neto): {info_producto['pmp']}")

    except Exception as e_pmp:
        logger.warning(f"Error extrayendo PMP: {e_pmp}")

    # SKU
    try:
        sku_xpaths = [
            "//*[contains(translate(., 'SKUCÓDIG', 'skucódig'), 'sku')]/following-sibling::*[1]",
            "//*[contains(translate(., 'SKUCÓDIG', 'skucódig'), 'código')]/following-sibling::*[1]",
            "//div[contains(@class,'sku') or contains(@class,'code') or @itemprop='sku']",
            "//span[contains(@class,'sku') or contains(@class,'code') or @itemprop='sku']"
        ]
        for xpath in sku_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        text = element.text.strip()
                        match = re.search(r'\b([A-Za-z0-9-]{5,20})\b', text) # Alfanumérico, 5-20 chars
                        if match and '$' not in text:
                            info_producto['sku'] = match.group(1)
                            logger.info(f"SKU (XPath: {xpath}): {info_producto['sku']}")
                            break
                if info_producto['sku']: break
            except Exception: continue
        
        if not info_producto['sku']: # Buscar números largos en general
            elements = driver.find_elements(By.XPATH, "//*[not(self::script) and not(self::style) and string-length(normalize-space(text())) > 6 and string-length(normalize-space(text())) < 20]")
            for el in elements:
                if el.is_displayed():
                    text = el.text.strip()
                    if '$' not in text and '%' not in text and re.search(r'^\d+$', text.replace("-","")): # que sea principalmente numérico
                        if len(text) >= 7: # Código de barras EAN-13 o similar
                           info_producto['sku'] = text
                           logger.info(f"SKU (número largo genérico): {info_producto['sku']}")
                           break
            if info_producto['sku']: pass


    except Exception as e_sku:
        logger.warning(f"Error extrayendo SKU: {e_sku}")


    # LABORATORIO
    try:
        lab_xpaths = [
            "//*[contains(translate(., 'LABORITFC', 'laboritfc'), 'laboratorio')]/following-sibling::*[1]",
            "//*[contains(translate(., 'LABORITFC', 'laboritfc'), 'fabricante')]/following-sibling::*[1]",
            "//div[contains(@class,'brand') or contains(@class,'manufacturer') or contains(@itemprop,'brand') or contains(@itemprop,'manufacturer')]",
            "//a[contains(@href,'brand') or contains(@href,'manufacturer')]"
        ]
        for xpath in lab_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        text = element.text.strip()
                        if len(text) > 2 and '$' not in text and not any(stop_word in text.lower() for stop_word in ["agregar", "opiniones", "reseñas", "ver más"]):
                            info_producto['laboratorio'] = text
                            logger.info(f"Laboratorio (XPath: {xpath}): {info_producto['laboratorio']}")
                            break
                if info_producto['laboratorio']: break
            except Exception: continue
        
        if not info_producto['laboratorio'] and info_producto.get('nombre', ''):
            if "GE " in info_producto['nombre'].upper() or "ANTIBIOTICOS" in info_producto['nombre'].upper():
                 info_producto['laboratorio'] = "ANTIBIOTICOS DE MEXICO" # Asunción
                 logger.info(f"Laboratorio (inferido por nombre): {info_producto['laboratorio']}")


    except Exception as e_lab:
        logger.warning(f"Error extrayendo Laboratorio: {e_lab}")

    # DISPONIBILIDAD
    try:
        stock_xpaths = [
            "//*[contains(translate(., 'STOCKDISPEX', 'stockdispex'), 'stock (')]", # Tu patrón "Stock (10,090)"
            "//*[contains(translate(., 'STOCKDISPEX', 'stockdispex'), 'disponible')]",
            "//*[contains(translate(., 'STOCKDISPEX', 'stockdispex'), 'existencia')]",
            "//div[contains(@class,'stock') or contains(@class,'availability')]",
            "//p[contains(@class,'stock') or contains(@class,'availability')]",
            "//span[contains(@class,'stock') or contains(@class,'availability')]"
        ]
        for xpath in stock_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        text = element.text.strip()
                        match_stock_num = re.search(r'[Ss]tock\s*\((\s*[\d,]+\s*)\)', text) # Captura número con comas
                        match_disponible_num = re.search(r'[Dd]isponibles?:\s*(\s*[\d,]+\s*)', text)
                        match_parenthesis_num = re.search(r'\((\s*[\d,]+\s*)\)', text) # Número entre paréntesis

                        if match_stock_num:
                            num = match_stock_num.group(1).replace(",","").strip()
                            info_producto['disponibilidad'] = f"Stock ({num})"
                        elif match_disponible_num:
                            num = match_disponible_num.group(1).replace(",","").strip()
                            info_producto['disponibilidad'] = f"Disponibles: {num}"
                        elif "agotado" in text.lower() or "no disponible" in text.lower():
                            info_producto['disponibilidad'] = "Agotado"
                        elif match_parenthesis_num and "precio" not in text.lower() and "$" not in text : # Evitar precios como (oferta)
                            num = match_parenthesis_num.group(1).replace(",","").strip()
                            info_producto['disponibilidad'] = f"Stock ({num})" # Asumir que es stock
                        elif "disponible" in text.lower():
                            info_producto['disponibilidad'] = "Disponible" # Genérico
                        
                        if info_producto['disponibilidad']:
                            logger.info(f"Disponibilidad (XPath: {xpath}): {info_producto['disponibilidad']}")
                            break
                if info_producto['disponibilidad']: break
            except Exception: continue

        if not info_producto['disponibilidad']: # Fallback: buscar botón de agregar al carrito
            try:
                add_cart_button = driver.find_element(By.XPATH, "//button[contains(translate(., 'AGRCITO', 'agrcito'), 'agregar al carrito') or contains(translate(., 'AÑDCAR', 'añdcar'), 'añadir al carrito')]")
                if add_cart_button.is_displayed() and add_cart_button.is_enabled():
                    info_producto['disponibilidad'] = "Disponible (botón agregar carrito)"
                    logger.info(f"Disponibilidad (botón agregar carrito): {info_producto['disponibilidad']}")
            except:
                 info_producto['disponibilidad'] = "No confirmada" # Si no hay nada, es no confirmada
                 logger.warning("Disponibilidad no confirmada.")


    except Exception as e_disp:
        logger.warning(f"Error extrayendo Disponibilidad: {e_disp}")
        info_producto['disponibilidad'] = "No confirmada"


    # IMAGEN
    try:
        img_selectors_css = [
            ".product-image-gallery img", "img.fotorama__img", # Magento
            "img.img-fluid.product-image", ".product-gallery__image img",
            ".woocommerce-product-gallery__image img" # WooCommerce
        ]
        img_xpaths = [
            "//div[contains(@class,'product-img-box')]//img",
            "//img[@itemprop='image']"
        ]
        
        found_image = False
        for selector in img_selectors_css:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        src = el.get_attribute("src")
                        if src and src.startswith("http"):
                            info_producto['imagen'] = src
                            logger.info(f"Imagen (CSS: {selector}): {src}")
                            found_image = True; break
                if found_image: break
            except: continue
        
        if not found_image:
            for xpath in img_xpaths:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    for el in elements:
                        if el.is_displayed():
                            src = el.get_attribute("src")
                            if src and src.startswith("http"):
                                info_producto['imagen'] = src
                                logger.info(f"Imagen (XPath: {xpath}): {src}")
                                found_image = True; break
                    if found_image: break
                except: continue
        
        if not found_image: # Fallback a imagen más grande visible
            all_imgs = driver.find_elements(By.TAG_NAME, "img")
            best_img_src = ""
            max_area = 0
            for img in all_imgs:
                if img.is_displayed():
                    src = img.get_attribute("src")
                    if src and src.startswith("http") and not any(skip in src.lower() for skip in ["logo", "icon", "avatar", ".svg"]):
                        try:
                            w, h = img.size['width'], img.size['height']
                            if w * h > max_area and w > 50 and h > 50:
                                max_area = w * h
                                best_img_src = src
                        except: continue # Ignorar si no se puede obtener tamaño
            if best_img_src:
                info_producto['imagen'] = best_img_src
                logger.info(f"Imagen (Fallback, más grande visible): {best_img_src}")


    except Exception as e_img:
        logger.warning(f"Error extrayendo Imagen: {e_img}")

    # DESCRIPCIÓN
    try:
        desc_selectors_css = [
            ".product.attribute.description .value", # Magento
            ".product-description", ".description", "[itemprop='description']"
        ]
        desc_xpaths = [
            "//div[@id='description']//p",
            "//div[contains(@class,'product-info')]//p[string-length(text()) > 50]"
        ]

        found_desc = False
        for selector in desc_selectors_css:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed() and el.text.strip():
                        text = el.text.strip()
                        if len(text) > 20 and not any(skip in text.lower() for skip in ["reseñas", "opiniones", "valoraciones"]):
                            info_producto['descripcion'] = text
                            logger.info(f"Descripción (CSS: {selector}, {len(text)} chars)")
                            found_desc = True; break
                if found_desc: break
            except: continue
        
        if not found_desc:
            for xpath in desc_xpaths:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    combined_text = "\n".join([el.text.strip() for el in elements if el.is_displayed() and el.text.strip()])
                    if combined_text and len(combined_text) > 20:
                         info_producto['descripcion'] = combined_text
                         logger.info(f"Descripción (XPath: {xpath}, {len(combined_text)} chars)")
                         found_desc = True; break
                    if found_desc: break
                except: continue
        
        if not found_desc: # Fallback a párrafos largos
            all_p = driver.find_elements(By.TAG_NAME, "p")
            candidate_descs = []
            for p_el in all_p:
                if p_el.is_displayed():
                    text = p_el.text.strip()
                    if len(text) > 100 and not any(skip in text.lower() for skip in ["copyright", "todos los derechos", "login", "carrito", "$"]):
                        candidate_descs.append(text)
            if candidate_descs:
                info_producto['descripcion'] = max(candidate_descs, key=len)
                logger.info(f"Descripción (Fallback, párrafo más largo, {len(info_producto['descripcion'])} chars)")

    except Exception as e_desc:
        logger.warning(f"Error extrayendo Descripción: {e_desc}")


    # --- Verificación final y retorno ---
    info_minima_presente = bool(info_producto.get('nombre')) and \
                           (bool(info_producto.get('precio_neto')) or bool(info_producto.get('pmp')))

    if info_minima_presente:
        logger.info("✅ Información mínima (Nombre y Precio) extraída con éxito.")
    else:
        missing_fields = []
        if not info_producto.get('nombre'): missing_fields.append('nombre')
        if not info_producto.get('precio_neto') and not info_producto.get('pmp'): missing_fields.append('precio')
        logger.warning(f"⚠️ No se pudo extraer información mínima. Falta: {', '.join(missing_fields) if missing_fields else 'datos desconocidos'}.")

    logger.info(f"Información final extraída: {json.dumps({k: v for k, v in info_producto.items() if v}, indent=2, ensure_ascii=False)}")
    return info_producto


# --- Bloque Principal ---
if __name__ == "__main__":
    print("=== Script de Login y Scraping para FANASA Carrito ===")
    print(f"Iniciando sesión con el usuario: {USERNAME}")

    driver_instance = login_fanasa_carrito()

    if driver_instance:
        print("\n✅ ¡Login exitoso en FANASA Carrito!")
        
        while True: # Bucle para múltiples búsquedas
            nombre_medicamento_buscar = input("\nIngresa el nombre del producto a buscar (o 'salir' para terminar): ").strip()
            if not nombre_medicamento_buscar:
                print("No ingresaste un nombre. Intenta de nuevo.")
                continue
            if nombre_medicamento_buscar.lower() == 'salir':
                break

            if buscar_producto(driver_instance, nombre_medicamento_buscar):
                print(f"\n✅ Navegación a la página del producto '{nombre_medicamento_buscar}' parece exitosa.")
                
                info_obtenida = extraer_info_producto(driver_instance)
                
                if info_obtenida:
                    print("\n" + "="*50)
                    print("        INFORMACIÓN DEL PRODUCTO        ")
                    print("="*50)
                    for key, value in info_obtenida.items():
                        if value: # Solo mostrar campos con información
                            print(f"{(key.replace('_',' ').capitalize() + ':'):<20} {value}")
                    print("="*50)

                    guardar = input("\n¿Deseas guardar esta información en un archivo JSON? (s/n): ").lower()
                    if guardar == 's':
                        try:
                            fecha_hora_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                            nombre_base_archivo = re.sub(r'[^\w\s-]', '', info_obtenida.get('nombre', nombre_medicamento_buscar)).strip().replace(' ', '_')
                            nombre_archivo_json = f"{nombre_base_archivo}_{fecha_hora_str}.json"
                            
                            with open(nombre_archivo_json, "w", encoding="utf-8") as f_json:
                                json.dump(info_obtenida, f_json, ensure_ascii=False, indent=4)
                            print(f"\n✅ Información guardada en: {nombre_archivo_json}")
                        except Exception as e_json:
                            print(f"\n❌ Error al guardar información en JSON: {e_json}")
                else:
                    print("\n❌ No se pudo extraer información detallada del producto.")
            else:
                print(f"\n❌ No se pudo encontrar o acceder a la página del producto: '{nombre_medicamento_buscar}'")
        
        print("\nSaliendo del bucle de búsqueda.")
        input("\nPresiona Enter para cerrar el navegador... ")
        driver_instance.quit()
        print("Navegador cerrado. Proceso finalizado.")
    else:
        print("\n❌ Error durante el login en FANASA Carrito. No se puede continuar.")
        print("Revisa las capturas de pantalla y los logs para identificar el problema.")
