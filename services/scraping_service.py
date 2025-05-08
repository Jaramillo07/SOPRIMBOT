"""
Servicio de scraping para buscar información de productos farmacéuticos.
Este servicio integra la funcionalidad de scraping ya implementada,
pero ahora usa webdriver-manager para alinear ChromeDriver automáticamente.
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    
    def __init__(self, headless: bool = HEADLESS_BROWSER):
        self.headless = headless
    
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
                "precio": None  # No es necesario por ahora
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
                            lab_elements = driver.find_elements(By.XPATH, "//dt[contains(text(), 'Laboratorio')]/following-sibling::dd[1] | //td[contains(text(), 'Laboratorio')]/following-sibling::td[1]")
                            if lab_elements:
                                info_producto["laboratorio"] = lab_elements[0].text.strip()
                                logger.info(f"Laboratorio extraído por XPath: {info_producto['laboratorio']}")
                        except:
                            pass
                    
                    # Xpath para código de barras
                    if not info_producto["codigo_barras"]:
                        try:
                            barcode_elements = driver.find_elements(By.XPATH, "//dt[contains(text(), 'Código de barras')]/following-sibling::dd[1] | //td[contains(text(), 'Código de barras')]/following-sibling::td[1]")
                            if barcode_elements:
                                info_producto["codigo_barras"] = barcode_elements[0].text.strip()
                                logger.info(f"Código de barras extraído por XPath: {info_producto['codigo_barras']}")
                        except:
                            pass
                    
                    # Xpath para registro sanitario
                    if not info_producto["registro_sanitario"]:
                        try:
                            reg_elements = driver.find_elements(By.XPATH, "//dt[contains(text(), 'Registro sanitario')]/following-sibling::dd[1] | //td[contains(text(), 'Registro sanitario')]/following-sibling::td[1]")
                            if reg_elements:
                                info_producto["registro_sanitario"] = reg_elements[0].text.strip()
                                logger.info(f"Registro sanitario extraído por XPath: {info_producto['registro_sanitario']}")
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Error en búsqueda XPath: {e}")
            
            # Método 4: Buscar por texto en todo el HTML como último recurso
            if not (info_producto["laboratorio"] and info_producto["codigo_barras"] and info_producto["registro_sanitario"]):
                logger.info("Buscando información en el texto completo de la página...")
                
                # Obtener el texto completo de la página
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                
                # Buscar por patrones específicos
                if not info_producto["laboratorio"]:
                    patrones_lab = ["laboratorio: ", "laboratorio ", "fabricante: ", "fabricante "]
                    for patron in patrones_lab:
                        if patron in page_text:
                            inicio = page_text.find(patron) + len(patron)
                            fin = page_text.find("\n", inicio)
                            if fin == -1:
                                fin = inicio + 50  # Si no hay salto de línea, tomar 50 caracteres
                            valor = page_text[inicio:fin].strip()
                            if valor:
                                info_producto["laboratorio"] = valor
                                logger.info(f"Laboratorio extraído de texto: {valor}")
                                break
                                
                if not info_producto["codigo_barras"]:
                    patrones_codigo = ["código de barras: ", "codigo de barras: ", "ean: ", "código: "]
                    for patron in patrones_codigo:
                        if patron in page_text:
                            inicio = page_text.find(patron) + len(patron)
                            fin = page_text.find("\n", inicio)
                            if fin == -1:
                                fin = inicio + 50
                            valor = page_text[inicio:fin].strip()
                            if valor and any(c.isdigit() for c in valor):  # Verificar que al menos contenga números
                                info_producto["codigo_barras"] = valor
                                logger.info(f"Código de barras extraído de texto: {valor}")
                                break
                                
                if not info_producto["registro_sanitario"]:
                    patrones_registro = ["registro sanitario: ", "registro: ", "reg. sanitario: ", "no. registro: "]
                    for patron in patrones_registro:
                        if patron in page_text:
                            inicio = page_text.find(patron) + len(patron)
                            fin = page_text.find("\n", inicio)
                            if fin == -1:
                                fin = inicio + 50
                            valor = page_text[inicio:fin].strip()
                            if valor:
                                info_producto["registro_sanitario"] = valor
                                logger.info(f"Registro sanitario extraído de texto: {valor}")
                                break
            
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
