import re
import sys
import os
import json
import logging
from datetime import datetime

# Imports de Selenium (asegúrate de tener Selenium instalado: pip install selenium)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager # Descomenta si usas webdriver-manager

# Configuración básica del logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# --- STUBS PARA FUNCIONES NO PROPORCIONADAS ---
# Debes implementar la lógica real para estas funciones.

def login_fanasa_carrito(headless=True):
    """
    Maneja el inicio de sesión en FANASA.
    Debe devolver una instancia del driver de Selenium después de iniciar sesión.
    """
    logger.info("Intentando iniciar sesión en FANASA...")
    # Ejemplo de cómo podrías iniciar el driver:
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu") # Recomendado para headless
        options.add_argument("--window-size=1920x1080") # Puede ayudar con algunos sitios
    options.add_argument("--no-sandbox") # Necesario en algunos entornos como Docker
    options.add_argument("--disable-dev-shm-usage") # Necesario en algunos entornos como Docker

    # Descomenta la siguiente línea y comenta la que usa un path si tienes webdriver-manager
    # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    # O especifica el path a tu chromedriver si no usas webdriver-manager:
    # driver_path = "/path/to/your/chromedriver" # Cambia esto por la ruta real
    # service = ChromeService(executable_path=driver_path)
    # driver = webdriver.Chrome(service=service, options=options)

    # ----- INICIO DE LÓGICA DE EJEMPLO (DEBES REEMPLAZARLA) -----
    # Simulación: crea un driver y navega a una página de ejemplo
    # Esta es solo una simulación. Debes implementar el login real.
    try:
        # Para este ejemplo, usaremos un driver sin path específico (asume que está en el PATH o gestionado)
        driver = webdriver.Chrome(options=options)
        # driver.get("https://www.fanasa.com.mx/carrito") # URL de ejemplo para el login
        # Aquí iría la lógica para encontrar campos de usuario/contraseña, llenarlos y hacer clic en login.
        # Ejemplo:
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username_field_id"))).send_keys("tu_usuario")
        # driver.find_element(By.ID, "password_field_id").send_keys("tu_contraseña")
        # driver.find_element(By.ID, "login_button_id").click()
        # WebDriverWait(driver, 10).until(EC.url_contains("alguna_url_post_login")) # Esperar a que el login sea exitoso
        logger.info("Simulación de login exitosa.")
        return driver
    except Exception as e:
        logger.error(f"Error en la simulación de login_fanasa_carrito: {e}")
        if 'driver' in locals() and driver:
            driver.quit()
        return None
    # ----- FIN DE LÓGICA DE EJEMPLO -----


def buscar_producto(driver, nombre_medicamento):
    """
    Busca un producto en FANASA usando el driver proporcionado.
    Debe navegar a la página del producto si lo encuentra.
    Devuelve True si el producto se encontró y se accedió a su página, False en caso contrario.
    """
    logger.info(f"Buscando producto: '{nombre_medicamento}' en FANASA.")
    # ----- INICIO DE LÓGICA DE EJEMPLO (DEBES REEMPLAZARLA) -----
    # Simulación: intenta buscar y hacer clic en un resultado.
    # Esta es solo una simulación. Debes implementar la búsqueda real.
    try:
        # driver.get("https://www.fanasa.com.mx/") # O la URL base para la búsqueda
        # search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search_input_id")))
        # search_box.send_keys(nombre_medicamento)
        # search_box.submit() # O hacer clic en un botón de búsqueda
        # Esperar a que aparezcan los resultados de búsqueda
        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item-link"))) # Selector de ejemplo
        # results = driver.find_elements(By.CSS_SELECTOR, ".product-item-link") # Selector de ejemplo
        # if results:
        #     logger.info(f"Producto encontrado, navegando a la página del primer resultado.")
        #     results[0].click() # Hacer clic en el primer resultado
        #     WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-info-main"))) # Esperar a que cargue la página del producto
        #     return True
        # else:
        #     logger.warning(f"No se encontraron resultados para '{nombre_medicamento}'.")
        #     return False
        logger.info("Simulación de búsqueda de producto. Asumiendo que se encontró y se navegó.")
        # Para que el resto del script funcione, simularemos que estamos en una página de producto
        # driver.get("URL_DE_PRODUCTO_DE_EJEMPLO_O_DEJAR_QUE_EL_LOGIN_LO_HAGA_SI_ES_EL_CASO")
        return True # Asumir éxito para la simulación
    except Exception as e:
        logger.error(f"Error en la simulación de buscar_producto: {e}")
        return False
    # ----- FIN DE LÓGICA DE EJEMPLO -----

# --- FIN DE STUBS ---


def extraer_info_producto(driver):
    """
    Extrae la información detallada de un producto desde la página actual del driver.
    """
    info_producto = {
        'nombre': '',
        'precio_neto': '',
        'pmp': '',
        'sku': '',
        'laboratorio': '',
        'disponibilidad': '',
        'imagen': '',
        'descripcion': '',
        'url': '' # Se llenará al final si es posible
    }

    try:
        # Esperar un poco a que la página de detalle del producto cargue completamente
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body")) # Esperar a que el body esté presente
        )
        info_producto['url'] = driver.current_url
        logger.info(f"Extrayendo información de: {info_producto['url']}")

        # NOMBRE DEL PRODUCTO
        try:
            # Intentar con selectores comunes para el nombre del producto
            name_selectors = [
                "h1.page-title span.base",  # Común en Magento
                ".product-name",
                ".product_title",
                "h1[itemprop='name']",
                ".product-info-main .page-title-wrapper .page-title .base",
                "h1" # Genérico, como último recurso
            ]
            for selector in name_selectors:
                try:
                    nombre_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if nombre_element.is_displayed() and nombre_element.text.strip():
                        info_producto['nombre'] = nombre_element.text.strip()
                        logger.info(f"Nombre: {info_producto['nombre']}")
                        break
                except NoSuchElementException:
                    continue
            if not info_producto['nombre']:
                 logger.warning("No se pudo extraer el nombre del producto con selectores CSS específicos.")
        except Exception as e:
            logger.warning(f"Error extrayendo Nombre: {e}")

        # PRECIO NETO
        # Si no encontramos precio específico, buscar otros valores monetarios
        if not info_producto['precio_neto']:
            try:
                precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
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
            except Exception as e_precio_inferido:
                logger.warning(f"Error en lógica de precio neto inferido: {e_precio_inferido}")
                pass

        # Si todavía no encontramos precio, usar la estrategia del precio más bajo
        if not info_producto['precio_neto']:
            try:
                precios = []
                precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
                for element in precio_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto)
                        if precio_match:
                            try:
                                valor = float(precio_match.group(1).replace(',', ''))
                                precios.append((valor, f"${precio_match.group(1)}"))
                            except ValueError: # Captura el error si la conversión a float falla
                                pass
                # Ordenar por valor y tomar el más bajo (típicamente el precio neto)
                if precios:
                    precios.sort()
                    info_producto['precio_neto'] = precios[0][1]
                    logger.info(f"Precio Neto (precio más bajo): {info_producto['precio_neto']}")
            except Exception as e_precio_bajo:
                logger.warning(f"Error en lógica de precio neto más bajo: {e_precio_bajo}")
                pass

        # PMP (PRECIO MÁXIMO PÚBLICO)
        try:
            # Buscar elementos que contengan "PMP"
            try:
                pmp_elements = driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'PMP')]/following::*[contains(text(), '$')] | //*[contains(text(), 'PMP')]//following-sibling::*[contains(text(), '$')] | //*[contains(text(), 'Precio Público')]//following-sibling::*[contains(text(), '$')] | //*[contains(translate(text(), 'PÚBLICO', 'público'), 'público')]/following::*[contains(text(), '$')] | //*[contains(translate(text(), 'PÚBLICO', 'público'), 'público')]//following-sibling::*[contains(text(), '$')]")
                for element in pmp_elements:
                    if element.is_displayed():
                        texto_pmp = element.text.strip()
                        pmp_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto_pmp)
                        if pmp_match:
                            info_producto['pmp'] = f"${pmp_match.group(1)}"
                            logger.info(f"PMP: {info_producto['pmp']}")
                            break
            except Exception as e_pmp_directo:
                logger.warning(f"Error buscando PMP directamente: {e_pmp_directo}")
                pass

            # Si no encontramos PMP específico pero tenemos precio neto, buscar el precio más alto
            if not info_producto['pmp'] and info_producto['precio_neto']:
                try:
                    precio_neto_valor_str = info_producto['precio_neto'].replace('$', '').replace(',', '')
                    if precio_neto_valor_str: # Asegurarse que no esté vacío
                        precio_neto_valor = float(precio_neto_valor_str)
                        precio_alto = None
                        precio_alto_str = None # Para guardar el string original del precio más alto
                        precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
                        for element in precio_elements:
                            if element.is_displayed():
                                texto = element.text.strip()
                                precio_match = re.search(r'\$\s*([\d,]+\.?\d*)', texto)
                                if precio_match:
                                    try:
                                        valor_str = precio_match.group(1).replace(',', '')
                                        if valor_str: # Asegurarse que no esté vacío
                                            valor = float(valor_str)
                                            # Si es mayor que el precio neto, podría ser el PMP
                                            if valor > precio_neto_valor and (precio_alto is None or valor > precio_alto):
                                                precio_alto = valor
                                                precio_alto_str = f"${precio_match.group(1)}"
                                    except ValueError:
                                        pass
                        if precio_alto_str:
                            info_producto['pmp'] = precio_alto_str
                            logger.info(f"PMP (precio más alto): {info_producto['pmp']}")
                except Exception as e_pmp_alto:
                    logger.warning(f"Error buscando PMP como precio más alto: {e_pmp_alto}")
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo PMP: {e}")

        # SKU / CÓDIGO DE PRODUCTO
        try:
            # Buscar elementos que contengan "SKU" o "Código"
            try:
                sku_elements = driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'SKU') or contains(text(), 'Código') or contains(text(), 'Codigo')]/following::* | //*[contains(text(), 'SKU:')]/../following-sibling::div | //div[contains(@class, 'sku')]//span | //span[contains(@class, 'sku')]")
                for element in sku_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        # Los SKUs generalmente son números largos o alfanuméricos
                        sku_match = re.search(r'\b(\d{5,})\b', texto) # Ajustado a 5+ para más flexibilidad
                        if sku_match and "$" not in texto: # Evitar que tome un precio como SKU
                            info_producto['sku'] = sku_match.group(1)
                            logger.info(f"SKU: {info_producto['sku']}")
                            break
                        # Si no hay número largo pero contiene un patrón alfanumérico que podría ser un código
                        elif re.match(r'^[A-Za-z0-9-]+$', texto) and len(texto) >= 4 and "$" not in texto and len(texto) < 20 : # Condición más específica
                            info_producto['sku'] = texto
                            logger.info(f"SKU (alfanumérico): {info_producto['sku']}")
                            break
                if info_producto['sku']: raise StopIteration # Salir si ya se encontró
            except StopIteration:
                pass
            except Exception as e_sku_directo:
                logger.warning(f"Error buscando SKU directamente: {e_sku_directo}")
                pass

            # Si no encontramos el SKU, buscar números largos que podrían ser SKUs
            if not info_producto['sku']:
                try:
                    all_elements = driver.find_elements(By.XPATH, "//*[string-length(normalize-space(text())) > 4 and string-length(normalize-space(text())) < 20]") # Longitud razonable para SKU
                    for element in all_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            # Evitar textos con $ (precios) y buscar números largos o alfanuméricos
                            if "$" not in texto and not re.search(r'[a-z]{3,}', texto.lower()): # Evitar frases
                                sku_match_numeric = re.search(r'\b(\d{5,})\b', texto)
                                sku_match_alphanumeric = re.match(r'^[A-Za-z0-9-]+$', texto)

                                if sku_match_numeric:
                                    info_producto['sku'] = sku_match_numeric.group(1)
                                    logger.info(f"SKU (número largo): {info_producto['sku']}")
                                    break
                                elif sku_match_alphanumeric and len(texto) >=4 :
                                    info_producto['sku'] = texto
                                    logger.info(f"SKU (alfanumérico general): {info_producto['sku']}")
                                    break
                except Exception as e_sku_largo:
                    logger.warning(f"Error buscando SKU como número largo: {e_sku_largo}")
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo SKU: {e}")

        # LABORATORIO / FABRICANTE
        try:
            # Buscar elementos que contengan "Laboratorio"
            try:
                lab_elements = driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'Laboratorio') or contains(text(), 'Fabricante')]/following::*[1] | //*[contains(text(), 'Laboratorio:')]/../following-sibling::div | //div[contains(@class,'brand')]//a | //a[contains(@href,'brand')]")
                for element in lab_elements:
                    if element.is_displayed() and element.text.strip():
                        texto = element.text.strip()
                        # Verificar que no sea un texto genérico o un precio
                        if len(texto) > 2 and "$" not in texto and "agregar" not in texto.lower() and "opiniones" not in texto.lower():
                            info_producto['laboratorio'] = texto
                            logger.info(f"Laboratorio: {info_producto['laboratorio']}")
                            break
                if info_producto['laboratorio']: raise StopIteration
            except StopIteration:
                pass
            except Exception as e_lab_directo:
                logger.warning(f"Error buscando Laboratorio directamente: {e_lab_directo}")
                pass

            # Si no encontramos el laboratorio, buscar textos que podrían ser nombres de laboratorios
            if not info_producto['laboratorio']:
                try:
                    lab_keywords = ["ANTIBIOTICOS", "FARMA", "LABORATORIO", "LAB", "MEXICO", "PHARMA", "S.A.", "DE C.V.", "HEALTHCARE"]
                    lab_candidates = driver.find_elements(By.XPATH, "//strong | //b | //div[text()[string-length() > 3 and string-length() < 30]] | //a[text()[string-length() > 3 and string-length() < 30]]")
                    for element in lab_candidates:
                        if element.is_displayed():
                            texto = element.text.strip().upper()
                            # Verificar si contiene alguna palabra clave de laboratorio
                            if any(keyword in texto for keyword in lab_keywords) and "$" not in texto and "CARRITO" not in texto and "ENVÍO" not in texto and "PRODUCTO" not in texto :
                                info_producto['laboratorio'] = element.text.strip() # Guardar el texto original
                                logger.info(f"Laboratorio (inferido): {info_producto['laboratorio']}")
                                break
                    if info_producto['laboratorio']: raise StopIteration
                except StopIteration:
                    pass
                except Exception as e_lab_inferido:
                    logger.warning(f"Error buscando Laboratorio inferido: {e_lab_inferido}")
                    pass

            # Como fallback adicional, buscar específicamente "ANTIBIOTICOS DE MEXICO"
            if not info_producto['laboratorio']:
                try:
                    all_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ANTIBIOTICOS', 'antibioticos'), 'antibioticos')]")
                    for element in all_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            if "MEXICO" in texto.upper():
                                info_producto['laboratorio'] = texto
                                logger.info(f"Laboratorio (ANTIBIOTICOS DE MEXICO): {info_producto['laboratorio']}")
                                break
                    if info_producto['laboratorio']: raise StopIteration
                except StopIteration:
                    pass
                except Exception as e_lab_anti:
                    logger.warning(f"Error buscando ANTIBIOTICOS DE MEXICO: {e_lab_anti}")
                    pass

            # Si todo falla, usar un valor predeterminado basado en el nombre del producto
            if not info_producto['laboratorio'] and info_producto['nombre'] and "GE" in info_producto['nombre'].upper():
                info_producto['laboratorio'] = "ANTIBIOTICOS DE MEXICO" # O el nombre que corresponda a "GE"
                logger.info(f"Laboratorio (predeterminado basado en nombre 'GE'): {info_producto['laboratorio']}")
        except Exception as e:
            logger.warning(f"Error general extrayendo Laboratorio: {e}")
            if not info_producto['laboratorio']: # Asegurar que no quede vacío si hay error general
                 info_producto['laboratorio'] = "No especificado"


        # DISPONIBILIDAD / STOCK
        try:
            # Buscar explícitamente el patrón "Stock (número)" o "Disponibles: número"
            try:
                stock_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Stock (') or contains(text(), 'Disponibles:') or contains(@class, 'stock') or contains(@class, 'availability')]")
                for element in stock_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        stock_match = re.search(r'[Ss]tock\s*\((\d+)\)|[Dd]isponibles?:\s*(\d+)', texto)
                        if stock_match:
                            numero_stock = stock_match.group(1) if stock_match.group(1) else stock_match.group(2)
                            info_producto['disponibilidad'] = f"Stock ({numero_stock})"
                            logger.info(f"Disponibilidad (Stock exacto): {info_producto['disponibilidad']}")
                            break
                if info_producto['disponibilidad']: raise StopIteration
            except StopIteration:
                pass
            except Exception as e_stock_directo:
                logger.warning(f"Error buscando Stock directamente: {e_stock_directo}")
                pass

            # Si no encontramos disponibilidad específica, buscar stock en toda la página
            if not info_producto['disponibilidad']:
                try:
                    page_source = driver.page_source
                    stock_match = re.search(r'[Ss]tock\s*\((\d+)\)|[Dd]isponibles?:\s*(\d+)', page_source)
                    if stock_match:
                        numero_stock = stock_match.group(1) if stock_match.group(1) else stock_match.group(2)
                        info_producto['disponibilidad'] = f"Stock ({numero_stock})"
                        logger.info(f"Disponibilidad (regex en página): {info_producto['disponibilidad']}")
                        raise StopIteration
                except StopIteration:
                    pass
                except Exception as e_stock_pagina:
                    logger.warning(f"Error buscando Stock en regex de página: {e_stock_pagina}")
                    pass

            # Si todavía no encontramos disponibilidad, probar con elementos más específicos
            if not info_producto['disponibilidad']:
                try:
                    stock_elements = driver.find_elements(By.XPATH,
                        "//*[contains(text(), 'Stock') or contains(text(), 'stock') or contains(text(), 'Disponibilidad') or contains(text(), 'Existencias')]")
                    for element in stock_elements:
                        if element.is_displayed():
                            texto = element.text.strip()
                            # Primero buscar "Stock (XXX)" o "Disponibles: XXX"
                            stock_match = re.search(r'[Ss]tock\s*\((\d+)\)|[Dd]isponibles?:\s*(\d+)', texto)
                            if stock_match:
                                numero_stock = stock_match.group(1) if stock_match.group(1) else stock_match.group(2)
                                info_producto['disponibilidad'] = f"Stock ({numero_stock})"
                                logger.info(f"Disponibilidad (Stock en texto): {info_producto['disponibilidad']}")
                                break
                            # Si no se encuentra ese patrón, buscar cualquier número entre paréntesis
                            parenthesis_match = re.search(r'\((\d+)\)', texto)
                            if parenthesis_match and "precio" not in texto.lower() and "$" not in texto:
                                info_producto['disponibilidad'] = f"Stock ({parenthesis_match.group(1)})"
                                logger.info(f"Disponibilidad (número en paréntesis): {info_producto['disponibilidad']}")
                                break
                    if info_producto['disponibilidad']: raise StopIteration
                except StopIteration:
                    pass
                except Exception as e_stock_especifico:
                    logger.warning(f"Error buscando Stock específico: {e_stock_especifico}")
                    pass

            # Asignar un valor por defecto si todo lo anterior falla
            if not info_producto['disponibilidad']:
                # Intentar buscar "Agotado" o "No disponible"
                try:
                    agotado_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'AGOTADOINDSPBLE', 'agotadoindspble'), 'agotado') or contains(translate(text(), 'AGOTADOINDSPBLE', 'agotadoindspble'), 'no disponible')]")
                    for el in agotado_elements:
                        if el.is_displayed():
                            info_producto['disponibilidad'] = "Agotado"
                            logger.info("Disponibilidad: Agotado")
                            break
                    if info_producto['disponibilidad'] == "Agotado": raise StopIteration
                except StopIteration:
                    pass
                except Exception:
                    pass

            if not info_producto['disponibilidad']:
                # Buscar "Agregar al carrito" como indicio de disponibilidad
                try:
                    add_to_cart_button = driver.find_element(By.XPATH, "//button[contains(translate(@title, 'AGRC', 'agrc'), 'agregar al carrito') or contains(translate(text(), 'AGRC', 'agrc'), 'agregar al carrito')]")
                    if add_to_cart_button.is_displayed() and add_to_cart_button.is_enabled():
                        info_producto['disponibilidad'] = "Stock disponible"
                        logger.info("Disponibilidad (botón 'Agregar al carrito' presente): Stock disponible")
                    else:
                         info_producto['disponibilidad'] = "Stock no confirmado" # Si está deshabilitado o no visible
                         logger.warning(f"No se encontró información específica de stock, y botón de carrito no confirma. Usando valor: {info_producto['disponibilidad']}")
                except NoSuchElementException:
                    info_producto['disponibilidad'] = "Stock no confirmado"
                    logger.warning(f"No se encontró información específica de stock ni botón de carrito. Usando valor: {info_producto['disponibilidad']}")
                except Exception as e_stock_carrito:
                    logger.warning(f"Error buscando disponibilidad por botón de carrito: {e_stock_carrito}")
                    if not info_producto['disponibilidad']:
                        info_producto['disponibilidad'] = "Stock no confirmado"

        except Exception as e:
            logger.warning(f"Error general extrayendo Disponibilidad: {e}")
            if not info_producto['disponibilidad']:
                info_producto['disponibilidad'] = "Stock no confirmado"


        # IMAGEN DEL PRODUCTO
        try:
            img_selectors = [
                "img.fotorama__img", # Fotorama es común en Magento
                ".product-image-gallery img",
                "img.img-fluid", "img.product-image", ".product-gallery img",
                "img[alt*='producto']", "img[src*='producto']",
                ".product-detail img", ".product img",
                ".product-info-main .product-image-photo", # Magento
                ".woocommerce-product-gallery__image img" # WooCommerce
            ]
            for selector in img_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            src = element.get_attribute("src")
                            if src and ('http' in src) and not src.endswith(".svg"): # Evitar SVGs pequeños
                                # Comprobar tamaño si es posible (a veces no está disponible directamente)
                                width = element.size.get('width', 0) if element.size else 0
                                height = element.size.get('height', 0) if element.size else 0
                                if width > 50 and height > 50:
                                    info_producto['imagen'] = src
                                    logger.info(f"URL de imagen: {info_producto['imagen']}")
                                    break
                                elif not info_producto['imagen']: # Tomar la primera válida si el tamaño no es concluyente
                                    info_producto['imagen'] = src
                                    logger.info(f"URL de imagen (sin tamaño confirmado): {info_producto['imagen']}")
                                    break
                    if info_producto['imagen']:
                        break
                except Exception: # Continuar con el siguiente selector
                    continue

            # Si no encontramos imagen con selectores específicos, buscar cualquier imagen visible grande
            if not info_producto['imagen']:
                try:
                    all_images = driver.find_elements(By.TAG_NAME, "img")
                    candidate_images = []
                    for img in all_images:
                        if img.is_displayed():
                            src = img.get_attribute("src")
                            if src and ('http' in src) and "logo" not in src.lower() and "icon" not in src.lower() and not src.endswith(".svg"):
                                try:
                                    width = img.size.get('width', 0)
                                    height = img.size.get('height', 0)
                                    if width > 100 and height > 100: # Umbral más alto para imágenes generales
                                        candidate_images.append({'src': src, 'area': width * height})
                                except Exception: # Si no se puede obtener el tamaño, considerar de todas formas
                                    if 'product' in src.lower() or info_producto.get('nombre','').split(' ')[0].lower() in src.lower():
                                         candidate_images.append({'src': src, 'area': 5001}) # Darle prioridad media

                    if candidate_images:
                        # Ordenar por área descendente para obtener la más grande
                        candidate_images.sort(key=lambda x: x['area'], reverse=True)
                        info_producto['imagen'] = candidate_images[0]['src']
                        logger.info(f"URL de imagen (general, más grande): {info_producto['imagen']}")

                except Exception as e_img_general:
                    logger.warning(f"Error buscando imagen general: {e_img_general}")
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo Imagen: {e}")

        # DESCRIPCIÓN (opcional)
        try:
            desc_selectors = [
                ".product.attribute.description .value", # Magento
                ".product-description", ".description", "#description",
                "[itemprop='description']", ".product-details p",
                ".tab-content .tab-pane.active", ".product-info p",
                ".woocommerce-product-details__short-description", # WooCommerce
                "#tab-description" # WooCommerce
            ]
            for selector in desc_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            texto = element.text.strip()
                            # Verificar que sea una descripción relevante (no texto de UI)
                            if len(texto) > 20 and "login" not in texto.lower() and "carrito" not in texto.lower() and "reseñas" not in texto.lower():
                                info_producto['descripcion'] = texto
                                logger.info(f"Descripción extraída (longitud: {len(info_producto['descripcion'])} caracteres)")
                                break
                    if info_producto['descripcion']:
                        break
                except Exception:
                    continue

            # Si no encontramos descripción con selectores, buscar párrafos largos
            if not info_producto['descripcion']:
                try:
                    paragraphs = driver.find_elements(By.TAG_NAME, "p")
                    candidate_descs = []
                    for p_element in paragraphs:
                        if p_element.is_displayed() and p_element.text.strip():
                            texto = p_element.text.strip()
                            if len(texto) > 50 and "login" not in texto.lower() and "carrito" not in texto.lower() and "$" not in texto:
                                # Evitar párrafos que parezcan ser parte del header/footer
                                try:
                                    parent = p_element.find_element(By.XPATH, "..")
                                    if "footer" not in parent.tag_name.lower() and "header" not in parent.tag_name.lower():
                                        candidate_descs.append(texto)
                                except Exception:
                                     candidate_descs.append(texto) # Si no se puede verificar el padre, añadir de todas formas

                    if candidate_descs:
                        # Tomar la descripción más larga
                        info_producto['descripcion'] = max(candidate_descs, key=len)
                        logger.info(f"Descripción (párrafo más largo): {info_producto['descripcion'][:50]}...")
                except Exception as e_desc_parrafo:
                    logger.warning(f"Error buscando descripción en párrafos: {e_desc_parrafo}")
                    pass
        except Exception as e:
            logger.warning(f"Error general extrayendo Descripción: {e}")

        # Verificar si tenemos información mínima
        info_minima = (info_producto['nombre'] != '') and \
                      (info_producto['precio_neto'] != '' or info_producto['pmp'] != '')

        if info_minima:
            logger.info("✅ Información mínima del producto extraída con éxito")
        else:
            logger.warning("⚠️ No se pudo extraer toda la información mínima del producto")
            missing = []
            if info_producto['nombre'] == '':
                missing.append("nombre")
            if info_producto['precio_neto'] == '' and info_producto['pmp'] == '':
                missing.append("precios")
            if missing:
                logger.warning(f"Falta la siguiente información esencial: {', '.join(missing)}")

        return info_producto

    except TimeoutException:
        logger.error("Timeout esperando la carga de la página de detalle para extracción.")
        return None # o info_producto parcial si prefieres
    except Exception as e:
        logger.error(f"Error general durante la extracción de información en extraer_info_producto: {e}")
        return None # o info_producto parcial


def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en FANASA.
    """
    driver = None
    try:
        logger.info(f"Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")

        driver = login_fanasa_carrito(headless=headless)
        if not driver:
            logger.error("No se pudo iniciar sesión o inicializar el driver en FANASA. Abortando búsqueda.")
            return None

        logger.info(f"Sesión iniciada (o driver listo). Buscando producto: '{nombre_medicamento}'")
        resultado_busqueda = buscar_producto(driver, nombre_medicamento)

        if not resultado_busqueda:
            logger.warning(f"No se pudo encontrar o acceder al producto: '{nombre_medicamento}'")
            return None

        logger.info("Extrayendo información del producto...")
        info_producto = extraer_info_producto(driver)

        if info_producto:
            info_producto['fuente'] = 'FANASA'
            info_producto['existencia'] = '0' # Valor por defecto
            if info_producto.get('disponibilidad'):
                stock_match = re.search(r'\((\d+)\)', info_producto['disponibilidad']) # Busca número entre ( )
                if stock_match:
                    info_producto['existencia'] = stock_match.group(1)
                elif 'disponible' in info_producto['disponibilidad'].lower() and 'no disponible' not in info_producto['disponibilidad'].lower():
                    info_producto['existencia'] = 'Si' # Si dice "disponible" pero no un número exacto
                elif 'agotado' in info_producto['disponibilidad'].lower() or 'no disponible' in info_producto['disponibilidad'].lower():
                     info_producto['existencia'] = 'No'
        return info_producto

    except Exception as e:
        logger.error(f"Error general durante el proceso en buscar_info_medicamento: {e}", exc_info=True)
        return None
    finally:
        if driver:
            logger.info("Cerrando navegador...")
            driver.quit()


if __name__ == "__main__":
    print("=== Sistema de Búsqueda de Medicamentos en FANASA ===")

    if len(sys.argv) > 1:
        medicamento_a_buscar = " ".join(sys.argv[1:])
    else:
        medicamento_a_buscar = input("Ingrese el nombre del medicamento a buscar: ")

    if not medicamento_a_buscar.strip():
        print("No se ingresó un nombre de medicamento. Saliendo.")
        sys.exit(1)

    print(f"\nBuscando información sobre: {medicamento_a_buscar}")
    print("Espere un momento...\n")

    # Definir el modo headless basado en entorno o por defecto True
    run_headless = os.environ.get('ENVIRONMENT', 'production').lower() != 'development'
    # run_headless = False # Descomenta para forzar la visualización del navegador durante el desarrollo

    info_resultado = buscar_info_medicamento(medicamento_a_buscar, headless=run_headless)

    if info_resultado:
        print("\n=== INFORMACIÓN DEL PRODUCTO ===")
        print(f"Nombre: {info_resultado.get('nombre', 'No disponible')}")
        print(f"Precio Neto: {info_resultado.get('precio_neto', 'No disponible')}")
        print(f"PMP: {info_resultado.get('pmp', 'No disponible')}")
        print(f"Laboratorio: {info_resultado.get('laboratorio', 'No disponible')}")
        print(f"SKU: {info_resultado.get('sku', 'No disponible')}")
        print(f"Disponibilidad (texto): {info_resultado.get('disponibilidad', 'No disponible')}")
        print(f"Existencia (calculada): {info_resultado.get('existencia', 'No disponible')}")
        if info_resultado.get('imagen'):
            print(f"Imagen: {info_resultado['imagen']}")
        print(f"URL: {info_resultado.get('url', 'No disponible')}")
        print(f"Fuente: {info_resultado.get('fuente', 'No disponible')}")


        guardar = input("\n¿Deseas guardar esta información en un archivo JSON? (s/n): ").lower()
        if guardar == 's':
            try:
                fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_base = re.sub(r'[^\w\s-]', '', info_resultado.get('nombre', 'producto_desconocido')).strip().replace(' ', '_')
                nombre_archivo = f"{nombre_base}_{fecha_hora}.json"

                with open(nombre_archivo, "w", encoding="utf-8") as f:
                    json.dump(info_resultado, f, ensure_ascii=False, indent=4)
                print(f"\n✅ Información guardada en el archivo: {nombre_archivo}")
            except Exception as e:
                print(f"\n❌ Error al guardar información: {e}")
    else:
        print(f"No se pudo encontrar información para el medicamento: '{medicamento_a_buscar}'")
