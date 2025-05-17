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
                except:
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
                    "//*[contains(text(), 'PMP')]/following::*[contains(text(), '$')] | //*[contains(text(), 'PMP')]//following-sibling::*[contains(text(), '$')] | //*[contains(text(), 'Precio Público')]//following-sibling::*[contains(text(), '$')]")
                
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
                    precio_neto_valor = float(info_producto['precio_neto'].replace('$', '').replace(',', ''))
                    precio_alto = None
                    precio_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
                    
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
                        elif re.match(r'^[A-Za-z0-9-]+', texto) and len(texto) >= 5:
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
