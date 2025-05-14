#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .settings import TIMEOUT, logger

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en el sitio de Difarmer y navega a los detalles del producto.
   
    Args:
        driver (webdriver.Chrome): Instancia del navegador con sesión iniciada
        nombre_producto (str): Nombre del producto a buscar
       
    Returns:
        bool: True si se encontró y accedió al detalle del producto, False en caso contrario
    """

    if not driver:
        logger.error("No se proporcionó un navegador válido")
        return False
   
    try:
        logger.info(f"Buscando producto: '{nombre_producto}'")
       
        # Buscar el campo de búsqueda
        search_field = None
        search_selectors = [
            "input[placeholder='¿Qué producto buscas?']",
            "input[type='search']",
            ".search-input",
            "input.form-control"
        ]
       
        for selector in search_selectors:
            fields = driver.find_elements(By.CSS_SELECTOR, selector)
            if fields and fields[0].is_displayed():
                search_field = fields[0]
                logger.info(f"Campo de búsqueda encontrado con selector: {selector}")
                break
       
        if not search_field:
            logger.error("No se pudo encontrar el campo de búsqueda")
            driver.save_screenshot("error_no_campo_busqueda.png")
            return False
       
        # Limpiar campo de búsqueda y escribir el nombre del producto
        search_field.clear()
        search_field.send_keys(nombre_producto)
      
        # Enviar la búsqueda presionando Enter
        search_field.send_keys(Keys.RETURN)
        logger.info(f"Búsqueda enviada para: '{nombre_producto}'")
       
        # Esperar a que carguen los resultados
        time.sleep(3)
      
        # Guardar captura de los resultados de búsqueda
        driver.save_screenshot("resultados_busqueda.png")
       
        # NUEVO: Guardar HTML de la página de resultados para análisis
        with open("resultados_busqueda.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("HTML de resultados guardado para análisis")
       
        # MODIFICADO: Buscar y hacer clic en elementos del producto
        # Basado en la Imagen 3 que muestra que los productos tienen imágenes clickeables
      
        # 1. Intentar encontrar nombres de productos en los resultados
        productos_encontrados = driver.find_elements(
            By.XPATH,
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '" +
            nombre_producto.lower() + "')]"
        )
       
        # También buscar por términos parciales
        if not productos_encontrados:
            for palabra in nombre_producto.lower().split():
                if len(palabra) > 3:  # Ignorar palabras muy cortas
                    productos_parciales = driver.find_elements(
                        By.XPATH,
                        "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '" +
                        palabra + "')]"
                    )
                    if productos_parciales:
                        productos_encontrados.extend(productos_parciales)
       
        # 2. Si encontramos textos que coinciden, intentar encontrar el elemento clickeable más cercano
        if productos_encontrados:
            logger.info(f"Se encontraron {len(productos_encontrados)} elementos de texto que coinciden con el producto")
           
            for elemento in productos_encontrados:
                try:
                    # Tomar capturas para ver qué elementos estamos procesando
                    driver.execute_script("arguments[0].style.border='2px solid red'", elemento)
                    driver.save_screenshot(f"elemento_producto_{productos_encontrados.index(elemento)}.png")
                   
                    # Prioridad 1: Buscar un enlace "Detalle de producto" cercano
                    try:
                        detalle_link = elemento.find_element(By.XPATH, ".//ancestor::*[5]//a[contains(text(), 'Detalle de producto')]")
                        logger.info("Encontrado enlace 'Detalle de producto' cercano al texto")
                        detalle_link.click()
                        time.sleep(3)
                        driver.save_screenshot("despues_clic_detalle.png")
                        return True
                    except:
                        pass
                   
                    # Prioridad 2: Buscar la imagen del producto o un enlace con imagen
                    try:
                        imagen = elemento.find_element(By.XPATH, ".//ancestor::*[5]//img")
                        logger.info("Encontrada imagen cercana al texto del producto")
                        # Verificar si la imagen está dentro de un enlace
                        try:
                            enlace = imagen.find_element(By.XPATH, "./ancestor::a")
                            logger.info("La imagen está dentro de un enlace, haciendo clic en el enlace")
                            enlace.click()
                        except:
                            logger.info("Haciendo clic directamente en la imagen")
                            imagen.click()
                        time.sleep(3)
                        driver.save_screenshot("despues_clic_imagen.png")
                        return True
                    except:
                        pass
                   
                    # Prioridad 3: Buscar cualquier enlace cercano
                    try:
                        enlaces = elemento.find_elements(By.XPATH, ".//ancestor::*[5]//a")
                        if enlaces:
                            logger.info(f"Encontrados {len(enlaces)} enlaces cercanos al texto")
                            # Filtrar enlaces que parezcan más relevantes
                            enlaces_filtrados = [e for e in enlaces if "detalle" in e.get_attribute("href").lower() or
                                               nombre_producto.lower() in e.get_attribute("href").lower() or
                                               "producto" in e.get_attribute("href").lower()]
                           
                            enlace_a_usar = enlaces_filtrados[0] if enlaces_filtrados else enlaces[0]
                            logger.info(f"Haciendo clic en enlace: {enlace_a_usar.get_attribute('href')}")
                            enlace_a_usar.click()
                            time.sleep(3)
                            driver.save_screenshot("despues_clic_enlace.png")
                            return True
                    except:
                        pass
                   
                    # Prioridad 4: Hacer clic directamente en el elemento
                    try:
                        logger.info("Intentando hacer clic directamente en el elemento de texto")
                        elemento.click()
                        time.sleep(3)
                        driver.save_screenshot("despues_clic_texto.png")
                        return True
                    except:
                        pass
                   
                except Exception as e:
                    logger.warning(f"Error al procesar elemento: {e}")
                    continue
       
        # 3. Si no encontramos textos que coincidan, buscar productos por su estructura
        logger.info("Buscando productos por estructura en la página...")
       
        # Buscar elementos que parezcan tarjetas de productos (basado en la Imagen 3)
        producto_elementos = []
       
        # a) Buscar divs que contengan "Laboratorio:" y "Colectivo:"
        producto_divs = driver.find_elements(
            By.XPATH,
            "//div[contains(., 'Laboratorio:') and contains(., 'Colectivo:')]"
        )
        if producto_divs:
            logger.info(f"Encontrados {len(producto_divs)} divs de productos por texto")
            producto_elementos.extend(producto_divs)
           
        # b) Buscar divs con imágenes de productos
        imagen_divs = driver.find_elements(By.XPATH, "//div[.//img]")
        if imagen_divs:
            # Filtrar para quedarnos solo con los que parecen tarjetas de productos
            for div in imagen_divs:
                if div.text and any(palabra in div.text.lower() for palabra in
                                   ["laboratorio", "colectivo", "existencia", "precio", "mg", "tabs"]):
                    producto_elementos.append(div)
                   
        logger.info(f"Se encontraron {len(producto_elementos)} elementos de productos por estructura")
       
        for elemento in producto_elementos:
            try:
                # Tomar capturas para ver qué elementos estamos procesando
                driver.execute_script("arguments[0].style.border='2px solid blue'", elemento)
                driver.save_screenshot(f"elemento_estructura_{producto_elementos.index(elemento)}.png")
               
                # Buscar enlaces "Detalle de producto" dentro del elemento
                detalle_links = elemento.find_elements(By.XPATH, ".//a[contains(text(), 'Detalle de producto')]")
                if detalle_links:
                    logger.info("Encontrado enlace 'Detalle de producto' en estructura")
                    detalle_links[0].click()
                    time.sleep(3)
                    driver.save_screenshot("despues_clic_detalle_estructura.png")
                    return True
               
                # Buscar imágenes clickeables
                imagenes = elemento.find_elements(By.TAG_NAME, "img")
                if imagenes:
                    # Verificar si la imagen está dentro de un enlace
                    try:
                        enlace = imagenes[0].find_element(By.XPATH, "./ancestor::a")
                        logger.info("Encontrada imagen dentro de un enlace")
                        enlace.click()
                        time.sleep(3)
                        driver.save_screenshot("despues_clic_imagen_estructura.png")
                        return True
                    except:
                        logger.info("Intentando hacer clic directamente en la imagen")
                        imagenes[0].click()
                        time.sleep(3)
                        driver.save_screenshot("despues_clic_imagen_directo.png")
                        return True
               
                # Buscar cualquier enlace dentro del elemento
                enlaces = elemento.find_elements(By.TAG_NAME, "a")
                if enlaces:
                    logger.info("Encontrado enlace en estructura de producto")
                    enlaces[0].click()
                    time.sleep(3)
                    driver.save_screenshot("despues_clic_enlace_estructura.png")
                    return True
               
                # Como último recurso, hacer clic en el elemento mismo
                logger.info("Haciendo clic directamente en el elemento de estructura")
                elemento.click()
                time.sleep(3)
                driver.save_screenshot("despues_clic_estructura.png")
                return True
               
            except Exception as e:
                logger.warning(f"Error al procesar elemento de estructura: {e}")
                continue
               
        # 4. Como último intento, buscar cualquier imagen o texto que contenga el nombre del producto
        logger.info("Último intento: buscando imágenes o enlaces por palabras clave...")
       
        # a) Buscar imágenes por atributo alt
        imagenes_alt = driver.find_elements(
            By.XPATH,
            f"//img[contains(@alt, '{nombre_producto}')]"
        )
       
        for img in imagenes_alt:
            try:
                logger.info("Encontrada imagen con alt que contiene el nombre del producto")
                img.click()
                time.sleep(3)
                driver.save_screenshot("despues_clic_imagen_alt.png")
                return True
            except:
                continue
       
        # b) Buscar enlaces que contengan el nombre del producto en href
        enlaces_href = driver.find_elements(
            By.XPATH,
            f"//a[contains(@href, '{nombre_producto}')]"
        )
       
        for enlace in enlaces_href:
            try:
                logger.info("Encontrado enlace con href que contiene el nombre del producto")
                enlace.click()
                time.sleep(3)
                driver.save_screenshot("despues_clic_enlace_href.png")
                return True
            except:
                continue
       
        # Si llegamos aquí, no pudimos hacer clic en ningún producto
        logger.warning(f"No se pudo encontrar o hacer clic en ningún producto para: '{nombre_producto}'")
        return False
       
    except Exception as e:
        logger.error(f"Error durante la búsqueda del producto: {e}")
        driver.save_screenshot("error_busqueda.png")
        return False
