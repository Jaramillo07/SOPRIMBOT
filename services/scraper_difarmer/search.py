#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .settings import TIMEOUT, logger

def extraer_concentracion(texto):
    """
    Extrae concentración del texto (200mg/5ml, 500mg, etc.)
    
    Args:
        texto (str): Texto del cual extraer concentración
        
    Returns:
        str: Concentración normalizada o None
    """
    if not texto:
        return None
    
    texto_lower = texto.lower()
    
    # Patrones para detectar concentraciones
    patrones = [
        r'(\d+(?:\.\d+)?)\s*mg\s*/\s*(\d+(?:\.\d+)?)\s*ml',  # 200mg/5ml
        r'(\d+(?:\.\d+)?)\s*mg\s*/\s*(\d+(?:\.\d+)?)\s*ml',  # 200 MG/5 ML
        r'(\d+(?:\.\d+)?)\s*mg',  # 500mg
        r'(\d+(?:\.\d+)?)\s*g',   # 1g
        r'(\d+(?:\.\d+)?)\s*mcg', # 100mcg
    ]
    
    for patron in patrones:
        match = re.search(patron, texto_lower)
        if match:
            if '/ml' in patron:
                # Formato mg/ml
                mg = match.group(1)
                ml = match.group(2)
                return f"{mg}mg/{ml}ml"
            else:
                # Formato simple
                valor = match.group(1)
                if 'mg' in patron:
                    return f"{valor}mg"
                elif 'g' in patron:
                    return f"{valor}g"
                elif 'mcg' in patron:
                    return f"{valor}mcg"
    
    return None

def extraer_forma_farmaceutica(texto):
    """
    Extrae la forma farmacéutica del texto.
    
    Args:
        texto (str): Texto del cual extraer forma
        
    Returns:
        set: Conjunto de formas farmacéuticas detectadas
    """
    if not texto:
        return set()
    
    texto_lower = texto.lower()
    formas_detectadas = set()
    
    # Mapeo de formas farmacéuticas y sus variantes
    formas_map = {
        'inyectable': ['inyectable', 'iny', 'inj', 'sol. iny', 'solucion inyectable'],
        'tableta': ['tableta', 'tabletas', 'tab', 'tabs', 'comprimidos', 'comps'],
        'capsula': ['capsula', 'capsulas', 'cap', 'caps', 'cápsula', 'cápsulas'],
        'solucion': ['solucion', 'solución', 'sol'],
        'jarabe': ['jarabe', 'suspension', 'suspensión'],
        'crema': ['crema', 'gel', 'ungüento', 'pomada'],
        'ampolla': ['ampolla', 'ampollas', 'ampolleta', 'ampolletas', 'amptas'],
        'gotas': ['gotas', 'drops'],
    }
    
    for forma_base, variantes in formas_map.items():
        for variante in variantes:
            if variante in texto_lower:
                formas_detectadas.add(forma_base)
                break
    
    return formas_detectadas

def normalizar_texto_simple(texto):
    """
    Normalización simple para comparación de palabras.
    """
    if not texto:
        return ""
    
    texto_norm = texto.lower().strip()
    # Eliminar caracteres especiales pero mantener espacios
    texto_norm = re.sub(r'[^\w\s]', ' ', texto_norm)
    texto_norm = re.sub(r'\s+', ' ', texto_norm).strip()
    
    return texto_norm

def extraer_info_completa_tarjeta(tarjeta_elemento):
    """
    Extrae información completa de la tarjeta de Difarmer basada en la estructura HTML real.
    CORREGIDO: Extracción más precisa usando las clases CSS específicas de Difarmer.
    
    Args:
        tarjeta_elemento: Elemento de la tarjeta del producto
        
    Returns:
        dict: Información completa extraída
    """
    info_completa = {
        'nombre_principal': '',
        'principio_activo': '',
        'laboratorio': '',
        'texto_completo': '',
        'nombres_para_comparar': []  # Lista de todos los nombres/textos a comparar
    }
    
    try:
        # Obtener todo el texto de la tarjeta
        texto_completo = tarjeta_elemento.text if tarjeta_elemento else ""
        info_completa['texto_completo'] = texto_completo
        
        logger.info(f"📋 Extrayendo info completa de tarjeta Difarmer:")
        logger.info(f"   Texto completo: {texto_completo}")
        
        # ✅ MÉTODO 1: Extracción por clases CSS específicas de Difarmer
        
        # 1. NOMBRE PRINCIPAL: font-weight-bold font-poppins
        try:
            elementos_nombre_principal = tarjeta_elemento.find_elements(By.CSS_SELECTOR, 
                ".font-weight-bold.font-poppins")
            
            for elem in elementos_nombre_principal:
                if elem.is_displayed() and elem.text.strip():
                    nombre_texto = elem.text.strip()
                    # Verificar que sea un nombre de producto válido (no precio, no código)
                    if (len(nombre_texto) > 10 and 
                        not '$' in nombre_texto and 
                        not nombre_texto.isdigit() and
                        not nombre_texto.startswith('Código:')):
                        
                        info_completa['nombre_principal'] = nombre_texto
                        info_completa['nombres_para_comparar'].append(nombre_texto)
                        logger.info(f"✅ Nombre principal extraído: '{nombre_texto}'")
                        break
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo nombre principal: {e}")
        
        # 2. PRINCIPIO ACTIVO: font-weight-bolder ml-2  
        try:
            elementos_principio_activo = tarjeta_elemento.find_elements(By.CSS_SELECTOR, 
                ".font-weight-bolder.ml-2")
            
            for elem in elementos_principio_activo:
                if elem.is_displayed() and elem.text.strip():
                    principio_texto = elem.text.strip()
                    # Verificar que sea un principio activo válido
                    if (len(principio_texto) > 2 and 
                        not '$' in principio_texto and 
                        not ':' in principio_texto and
                        not principio_texto.isdigit()):
                        
                        info_completa['principio_activo'] = principio_texto
                        info_completa['nombres_para_comparar'].append(principio_texto)
                        logger.info(f"✅ Principio activo extraído: '{principio_texto}'")
                        break
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo principio activo: {e}")
        
        # 3. LABORATORIO: font-poppins ml-2 (con "Laboratorio:")
        try:
            elementos_laboratorio = tarjeta_elemento.find_elements(By.CSS_SELECTOR, 
                ".font-poppins.ml-2")
            
            for elem in elementos_laboratorio:
                if elem.is_displayed() and elem.text.strip():
                    lab_texto = elem.text.strip()
                    # Buscar texto que contenga "Laboratorio:"
                    if 'laboratorio:' in lab_texto.lower():
                        # Extraer solo el nombre del laboratorio
                        lab_nombre = lab_texto.replace('Laboratorio:', '').replace('laboratorio:', '').strip()
                        if lab_nombre:
                            info_completa['laboratorio'] = lab_nombre
                            logger.info(f"✅ Laboratorio extraído: '{lab_nombre}'")
                        break
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo laboratorio: {e}")
        
        # ✅ MÉTODO 2: Fallback usando selectores más amplios si no funcionó el Método 1
        if not info_completa['nombre_principal'] and not info_completa['principio_activo']:
            logger.info("🔄 Método 1 no exitoso, usando fallback con selectores amplios...")
            
            # Buscar cualquier elemento con font-weight-bold
            try:
                elementos_bold = tarjeta_elemento.find_elements(By.CSS_SELECTOR, 
                    ".font-weight-bold, .font-weight-bolder")
                
                for elem in elementos_bold:
                    if elem.is_displayed() and elem.text.strip():
                        texto = elem.text.strip()
                        if (len(texto) > 5 and 
                            not '$' in texto and 
                            not texto.isdigit() and
                            not ':' in texto):
                            
                            # Si es largo, probablemente sea nombre principal
                            if len(texto) > 15 and not info_completa['nombre_principal']:
                                info_completa['nombre_principal'] = texto
                                info_completa['nombres_para_comparar'].append(texto)
                                logger.info(f"✅ Nombre principal (fallback): '{texto}'")
                            
                            # Si es corto, probablemente sea principio activo
                            elif len(texto) <= 15 and not info_completa['principio_activo']:
                                info_completa['principio_activo'] = texto
                                info_completa['nombres_para_comparar'].append(texto)
                                logger.info(f"✅ Principio activo (fallback): '{texto}'")
                            
                            # Si ya tenemos ambos, parar
                            if info_completa['nombre_principal'] and info_completa['principio_activo']:
                                break
                                
            except Exception as e:
                logger.warning(f"⚠️ Error en fallback: {e}")
        
        # ✅ MÉTODO 3: Análisis por líneas si aún no tenemos información
        if not info_completa['nombres_para_comparar']:
            logger.info("🔄 Métodos anteriores fallaron, analizando por líneas...")
            
            lineas = texto_completo.split('\n')
            logger.info(f"📝 Analizando {len(lineas)} líneas de texto:")
            
            for i, linea in enumerate(lineas):
                linea_limpia = linea.strip()
                if not linea_limpia or len(linea_limpia) < 3:
                    continue
                    
                logger.info(f"   Línea {i}: '{linea_limpia}'")
                
                # Filtrar líneas que no son nombres de productos
                if (any(x in linea_limpia for x in ['$', ':', 'León', 'CEDIS', 'Otros', 'Existencia', 'Colectivo']) or
                    linea_limpia.isdigit() or
                    re.match(r'^\d+$', linea_limpia)):
                    continue
                
                # Si contiene características de medicamento, es probable que sea nombre
                if re.search(r'[A-Z]{3,}.*(?:MG|ML|TABS|TAB|CAP|SOL|INY|COMP)', linea_limpia.upper()):
                    info_completa['nombres_para_comparar'].append(linea_limpia)
                    if not info_completa['nombre_principal']:
                        info_completa['nombre_principal'] = linea_limpia
                    logger.info(f"✅ Nombre de medicamento (línea): '{linea_limpia}'")
                
                # Si es corto y contiene solo letras, puede ser principio activo
                elif (3 <= len(linea_limpia) <= 20 and
                      re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', linea_limpia) and
                      not info_completa['principio_activo']):
                    info_completa['principio_activo'] = linea_limpia
                    info_completa['nombres_para_comparar'].append(linea_limpia)
                    logger.info(f"✅ Posible principio activo (línea): '{linea_limpia}'")
        
        # ✅ MÉTODO 4: Si aún no tenemos nada, usar líneas significativas como último recurso
        if not info_completa['nombres_para_comparar']:
            logger.info("🔄 Último recurso: usando líneas significativas...")
            
            lineas_significativas = []
            for linea in texto_completo.split('\n'):
                linea_limpia = linea.strip()
                if (linea_limpia and 
                    len(linea_limpia) > 3 and
                    not '$' in linea_limpia and
                    not linea_limpia.isdigit() and
                    not any(x in linea_limpia for x in ['León:', 'CEDIS:', 'Existencia:'])):
                    lineas_significativas.append(linea_limpia)
            
            # Tomar las primeras 3 líneas significativas
            info_completa['nombres_para_comparar'] = lineas_significativas[:3]
            logger.info(f"🔄 Fallback final - líneas significativas: {info_completa['nombres_para_comparar']}")
        
        # ✅ LOG FINAL DEL RESULTADO
        logger.info(f"📊 EXTRACCIÓN FINAL COMPLETADA:")
        logger.info(f"   Nombre principal: '{info_completa['nombre_principal']}'")
        logger.info(f"   Principio activo: '{info_completa['principio_activo']}'")
        logger.info(f"   Laboratorio: '{info_completa['laboratorio']}'")
        logger.info(f"   Nombres para comparar ({len(info_completa['nombres_para_comparar'])}): {info_completa['nombres_para_comparar']}")
        
        return info_completa
        
    except Exception as e:
        logger.error(f"❌ Error general extrayendo info completa: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return info_completa

def calcular_similitud_individual(busqueda, texto_comparar):
    """
    Calcula similitud entre búsqueda y un texto específico.
    
    Args:
        busqueda (str): Término buscado por el usuario  
        texto_comparar (str): Texto individual a comparar
        
    Returns:
        float: Puntuación de similitud (0.0 a 1.0)
    """
    if not busqueda or not texto_comparar:
        return 0.0
    
    logger.info(f"🔬 Calculando similitud individual:")
    logger.info(f"   Búsqueda: '{busqueda}'")
    logger.info(f"   Comparar: '{texto_comparar}'")
    
    puntuacion_total = 0.0
    
    # ✅ 1. COMPARAR CONCENTRACIONES (peso: 40%)
    conc_busqueda = extraer_concentracion(busqueda)
    conc_texto = extraer_concentracion(texto_comparar)
    
    puntuacion_concentracion = 0.0
    if conc_busqueda and conc_texto:
        if conc_busqueda == conc_texto:
            puntuacion_concentracion = 1.0
            logger.info(f"✅ CONCENTRACIONES IDÉNTICAS: {conc_busqueda}")
        else:
            # Comparar solo la parte numérica si las unidades son diferentes
            nums_busq = re.findall(r'\d+(?:\.\d+)?', conc_busqueda)
            nums_texto = re.findall(r'\d+(?:\.\d+)?', conc_texto)
            if nums_busq and nums_texto and nums_busq[0] == nums_texto[0]:
                puntuacion_concentracion = 0.7
                logger.info(f"✅ VALORES NUMÉRICOS COINCIDEN: {nums_busq[0]}")
    elif conc_busqueda or conc_texto:
        puntuacion_concentracion = 0.0
    else:
        puntuacion_concentracion = 0.5  # Neutral
    
    puntuacion_total += puntuacion_concentracion * 0.40
    
    # ✅ 2. COMPARAR FORMAS FARMACÉUTICAS (peso: 30%)
    formas_busqueda = extraer_forma_farmaceutica(busqueda)
    formas_texto = extraer_forma_farmaceutica(texto_comparar)
    
    puntuacion_forma = 0.0
    if formas_busqueda and formas_texto:
        coincidencias_forma = formas_busqueda.intersection(formas_texto)
        if coincidencias_forma:
            puntuacion_forma = len(coincidencias_forma) / max(len(formas_busqueda), len(formas_texto))
            logger.info(f"✅ FORMAS COINCIDENTES: {coincidencias_forma}")
    elif not formas_busqueda and not formas_texto:
        puntuacion_forma = 0.5  # Neutral
    else:
        puntuacion_forma = 0.3  # Penalización leve
    
    puntuacion_total += puntuacion_forma * 0.30
    
    # ✅ 3. COMPARAR PALABRAS DEL NOMBRE (peso: 30%)
    busq_norm = normalizar_texto_simple(busqueda)
    texto_norm = normalizar_texto_simple(texto_comparar)
    
    # Eliminar palabras de concentración y forma para obtener nombre "limpio"
    if conc_busqueda:
        busq_norm = busq_norm.replace(conc_busqueda.lower(), "")
    if conc_texto:
        texto_norm = texto_norm.replace(conc_texto.lower(), "")
    
    # Eliminar palabras comunes de formas farmacéuticas
    palabras_ignorar = ['sol', 'iny', 'tabletas', 'tab', 'caps', 'mg', 'ml', 'amptas', 'con', 'c', 'comps']
    
    palabras_busq = [p for p in busq_norm.split() if p and p not in palabras_ignorar and len(p) > 2]
    palabras_texto = [p for p in texto_norm.split() if p and p not in palabras_ignorar and len(p) > 2]
    
    puntuacion_nombre = 0.0
    if palabras_busq and palabras_texto:
        palabras_busq_set = set(palabras_busq)
        palabras_texto_set = set(palabras_texto)
        
        coincidencias_nombre = palabras_busq_set.intersection(palabras_texto_set)
        if coincidencias_nombre:
            puntuacion_nombre = len(coincidencias_nombre) / len(palabras_busq_set)
            logger.info(f"✅ PALABRAS COINCIDENTES: {coincidencias_nombre}")
        else:
            # Verificar coincidencias parciales (subcadenas)
            for p_busq in palabras_busq:
                for p_texto in palabras_texto:
                    if len(p_busq) > 3 and (p_busq in p_texto or p_texto in p_busq):
                        puntuacion_nombre += 0.3
                        logger.info(f"✅ COINCIDENCIA PARCIAL: '{p_busq}' ~ '{p_texto}'")
                        break
            puntuacion_nombre = min(puntuacion_nombre, 1.0)
    else:
        puntuacion_nombre = 0.2  # Penalización si no hay palabras claras
    
    puntuacion_total += puntuacion_nombre * 0.30
    
    # ✅ BONIFICACIONES ESPECIALES
    
    # Bonificación si concentración + forma coinciden
    if puntuacion_concentracion >= 0.7 and puntuacion_forma >= 0.7:
        bonificacion = 0.2
        puntuacion_total += bonificacion
        logger.info(f"🎯 BONIFICACIÓN concentración + forma: +{bonificacion}")
    
    # Bonificación por coincidencia al inicio
    if texto_norm.startswith(busq_norm[:min(5, len(busq_norm))]) and len(busq_norm) > 3:
        bonificacion = 0.1
        puntuacion_total += bonificacion
        logger.info(f"🎯 BONIFICACIÓN inicio: +{bonificacion}")
    
    # Asegurar que esté entre 0 y 1
    puntuacion_final = max(0.0, min(puntuacion_total, 1.0))
    
    logger.info(f"📊 Similitud individual: {puntuacion_final:.3f}")
    
    return puntuacion_final

def calcular_similitud_producto_mejorada(busqueda, info_completa_tarjeta):
    """
    Calcula similitud comparando búsqueda contra TODOS los datos de la tarjeta:
    - Nombre principal 
    - Principio activo
    - Cualquier otro texto relevante
    
    Toma la MEJOR similitud encontrada.
    
    Args:
        busqueda (str): Término buscado por el usuario  
        info_completa_tarjeta (dict): Info completa extraída de la tarjeta
        
    Returns:
        float: Puntuación de similitud (0.0 a 1.0)
    """
    if not busqueda or not info_completa_tarjeta.get('nombres_para_comparar'):
        return 0.0
    
    logger.info(f"🔬 SIMILITUD MEJORADA (comparación múltiple):")
    logger.info(f"   Búsqueda: '{busqueda}'")
    
    mejor_similitud = 0.0
    mejor_coincidencia = ""
    
    # Comparar contra todos los textos extraídos de la tarjeta
    for texto_comparar in info_completa_tarjeta['nombres_para_comparar']:
        if not texto_comparar:
            continue
            
        similitud = calcular_similitud_individual(busqueda, texto_comparar)
        
        logger.info(f"   vs '{texto_comparar}': {similitud:.3f}")
        
        if similitud > mejor_similitud:
            mejor_similitud = similitud
            mejor_coincidencia = texto_comparar
    
    logger.info(f"🏆 MEJOR SIMILITUD: {mejor_similitud:.3f}")
    logger.info(f"🏆 MEJOR COINCIDENCIA: '{mejor_coincidencia}'")
    
    return mejor_similitud

# ✅ FUNCIÓN ORIGINAL MANTENIDA PARA COMPATIBILIDAD
def calcular_similitud_producto(busqueda, producto_encontrado):
    """
    Función original mantenida para compatibilidad.
    Ahora solo compara texto simple (fallback).
    """
    if not busqueda or not producto_encontrado:
        return 0.0
    
    # Crear info_completa simple para compatibilidad
    info_simple = {
        'nombres_para_comparar': [producto_encontrado]
    }
    
    return calcular_similitud_producto_mejorada(busqueda, info_simple)

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en el sitio de Difarmer y navega a los detalles del producto.
    CORREGIDO: Verifica mensaje de "No se encontraron resultados" y limita tarjetas a máximo 10.
   
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
        logger.info(f"🔍 Buscando producto: '{nombre_producto}'")
       
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
                logger.info(f"✅ Campo de búsqueda encontrado con selector: {selector}")
                break
       
        if not search_field:
            logger.error("❌ No se pudo encontrar el campo de búsqueda")
            driver.save_screenshot("error_no_campo_busqueda.png")
            return False
       
        # Limpiar campo de búsqueda y escribir el nombre del producto
        search_field.clear()
        search_field.send_keys(nombre_producto)
      
        # Enviar la búsqueda presionando Enter
        search_field.send_keys(Keys.RETURN)
        logger.info(f"🚀 Búsqueda enviada para: '{nombre_producto}'")
       
        # Esperar a que carguen los resultados
        time.sleep(5)
      
        # Guardar captura de los resultados de búsqueda
        driver.save_screenshot("resultados_busqueda.png")
        
        # Guardar HTML para análisis
        with open("resultados_busqueda.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("📄 HTML de resultados guardado para análisis")
       
        # ✅ NUEVO: VERIFICAR PRIMERO SI HAY MENSAJE DE "NO RESULTADOS"
        logger.info("🔍 Verificando si hay mensaje de 'No se encontraron resultados'...")
        
        mensajes_no_resultados = [
            "No se encontraron resultados",
            "No se encontró",
            "Sin resultados",
            "0 resultados",
            "No hay productos"
        ]
        
        texto_pagina = driver.page_source.lower()
        
        for mensaje in mensajes_no_resultados:
            if mensaje.lower() in texto_pagina:
                logger.warning(f"❌ MENSAJE DE 'NO RESULTADOS' DETECTADO: '{mensaje}'")
                logger.warning(f"   No hay productos para la búsqueda: '{nombre_producto}'")
                driver.save_screenshot("no_resultados_detectado.png")
                return False
        
        # ✅ BÚSQUEDA DE TARJETAS CON LÍMITE
        logger.info("🎯 Buscando tarjetas de productos (máximo 10 permitidas)...")
        
        # Selectores más específicos y ordenados por prioridad
        selectores_tarjetas = [
            # Selectores más específicos primero
            "//div[contains(@class, 'producto') or contains(@class, 'item') or contains(@class, 'card')]",
            "//div[.//img and contains(., '$') and contains(., 'Laboratorio:')]",  # Más específico
            "//div[contains(., 'Código Difarmer:')]",
            "//div[contains(., 'Laboratorio:') and contains(., 'Mi precio:')]",  # Más general al final
            "//div[contains(., 'Existencia:')]",
            "//div[contains(., 'León:')]"
        ]
        
        primera_tarjeta = None
        info_completa_primer_producto = None
        tarjetas_encontradas = 0
        
        for selector in selectores_tarjetas:
            try:
                elementos = driver.find_elements(By.XPATH, selector)
                elementos_visibles = [elem for elem in elementos if elem.is_displayed()]
                
                tarjetas_encontradas = len(elementos_visibles)
                
                logger.info(f"🔍 Selector: {selector}")
                logger.info(f"   Tarjetas encontradas: {tarjetas_encontradas}")
                
                # ✅ VERIFICACIÓN CRÍTICA: Si hay más de 10 tarjetas, son demasiadas (no específicas)
                if tarjetas_encontradas > 10:
                    logger.warning(f"⚠️ DEMASIADAS TARJETAS ({tarjetas_encontradas} > 10) con selector: {selector}")
                    logger.warning(f"   Este selector es demasiado amplio, probando siguiente...")
                    continue
                
                # Si hay entre 1-10 tarjetas, es un buen rango
                if 1 <= tarjetas_encontradas <= 10:
                    logger.info(f"✅ RANGO ACEPTABLE de tarjetas ({tarjetas_encontradas}) con selector: {selector}")
                    primera_tarjeta = elementos_visibles[0]
                    
                    # ✅ Extraer información completa de la tarjeta
                    info_completa_primer_producto = extraer_info_completa_tarjeta(primera_tarjeta)
                    
                    if info_completa_primer_producto.get('nombres_para_comparar'):
                        logger.info(f"✅ Información completa extraída de la primera tarjeta")
                        break
                    
            except Exception as e:
                logger.warning(f"⚠️ Error con selector {selector}: {e}")
                continue
        
        # ✅ VERIFICACIÓN FINAL: Si NO se encontraron tarjetas válidas
        if tarjetas_encontradas == 0:
            logger.warning(f"❌ NO se encontraron tarjetas de productos para: '{nombre_producto}'")
            driver.save_screenshot("no_tarjetas_encontradas.png")
            return False
        
        elif tarjetas_encontradas > 10:
            logger.warning(f"❌ TODAS las tarjetas superan el límite de 10 (encontradas: {tarjetas_encontradas})")
            logger.warning(f"   Esto indica que la búsqueda no fue específica para: '{nombre_producto}'")
            driver.save_screenshot("demasiadas_tarjetas.png")
            return False
        
        # Si no se pudo extraer info de la tarjeta, buscar en texto general
        if not primera_tarjeta or not info_completa_primer_producto:
            logger.info("🔍 No se encontraron tarjetas específicas, buscando en texto general")
            
            # Buscar elementos que contengan nombres que parezcan medicamentos
            elementos_texto = driver.find_elements(By.XPATH, "//*[text()]")
            for elemento in elementos_texto:
                if elemento.is_displayed():
                    texto = elemento.text.strip()
                    # Buscar texto que parezca nombre de medicamento
                    if re.search(r'[A-Z]{3,}.*(?:MG|TABS|TAB|CAP|ML|G\b)', texto) and len(texto) > 5:
                        primera_tarjeta = elemento
                        info_completa_primer_producto = {
                            'nombres_para_comparar': [texto],
                            'nombre_principal': texto,
                            'principio_activo': '',
                            'texto_completo': texto
                        }
                        logger.info(f"📝 Texto encontrado en elemento general: '{texto}'")
                        break
        
        # Verificar si tenemos información para evaluar
        if not info_completa_primer_producto or not info_completa_primer_producto.get('nombres_para_comparar'):
            logger.warning("❌ No se pudo extraer información de ningún producto de los resultados")
            logger.warning(f"   No hay datos válidos para evaluar similitud con: '{nombre_producto}'")
            return False
        
        # ✅ CALCULAR SIMILITUD con algoritmo MEJORADO (comparación múltiple)
        similitud = calcular_similitud_producto_mejorada(nombre_producto, info_completa_primer_producto)
        umbral_similitud = 0.4  # Mantener umbral actual
        
        logger.info(f"🧮 EVALUACIÓN DE SIMILITUD MEJORADA:")
        logger.info(f"   Búsqueda: '{nombre_producto}'")
        logger.info(f"   Datos encontrados: {info_completa_primer_producto.get('nombres_para_comparar', [])}")
        logger.info(f"   Similitud: {similitud:.3f} (umbral: {umbral_similitud})")
        logger.info(f"   Tarjetas analizadas: {tarjetas_encontradas}")
        
        if similitud < umbral_similitud:
            logger.warning(f"❌ SIMILITUD INSUFICIENTE ({similitud:.3f} < {umbral_similitud})")
            logger.warning(f"   Los datos encontrados no son suficientemente similares a '{nombre_producto}'")
            driver.save_screenshot("similitud_insuficiente.png")
            return False
        
        logger.info(f"✅ SIMILITUD ACEPTABLE ({similitud:.3f} >= {umbral_similitud})")
        logger.info(f"   Procediendo a hacer clic en el producto encontrado")
        
        # ✅ HACER CLIC EN EL PRIMER PRODUCTO (que ya validamos que es similar)
        if primera_tarjeta:
            try:
                # Resaltar el elemento para depuración
                driver.execute_script("arguments[0].style.border='3px solid green'", primera_tarjeta)
                driver.save_screenshot("producto_seleccionado.png")
                
                # Intentar encontrar elementos clickeables dentro de la tarjeta
                elementos_clickeables = [
                    ".//a[contains(text(), 'Detalle de producto')]",
                    ".//img",
                    ".//a",
                    "."  # El elemento mismo como último recurso
                ]
                
                clic_exitoso = False
                for selector_click in elementos_clickeables:
                    try:
                        elemento_click = primera_tarjeta.find_element(By.XPATH, selector_click)
                        if elemento_click.is_displayed():
                            logger.info(f"🎯 Intentando hacer clic con selector: {selector_click}")
                            
                            # Scroll al elemento
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elemento_click)
                            time.sleep(1)
                            
                            # Intentar clic normal
                            try:
                                elemento_click.click()
                                clic_exitoso = True
                                logger.info(f"✅ Clic exitoso con selector: {selector_click}")
                                break
                            except:
                                # Intentar clic con JavaScript
                                driver.execute_script("arguments[0].click();", elemento_click)
                                clic_exitoso = True
                                logger.info(f"✅ Clic exitoso con JavaScript, selector: {selector_click}")
                                break
                    except Exception as e:
                        logger.warning(f"⚠️ Error con selector de clic {selector_click}: {e}")
                        continue
                
                if clic_exitoso:
                    # Esperar a que cargue la página de detalle
                    time.sleep(5)
                    driver.save_screenshot("despues_clic_exitoso.png")
                    
                    # Verificar que estamos en una página de detalle
                    url_actual = driver.current_url
                    texto_pagina = driver.page_source.lower()
                    
                    # Indicadores de que estamos en página de detalle
                    indicadores_detalle = [
                        'detalle' in url_actual.lower(),
                        'producto' in url_actual.lower(),
                        'mi precio:' in texto_pagina,
                        'código difarmer:' in texto_pagina,
                        'laboratorio:' in texto_pagina
                    ]
                    
                    if any(indicadores_detalle):
                        logger.info(f"✅ ¡ÉXITO! Navegación exitosa a página de detalle")
                        logger.info(f"   URL: {url_actual}")
                        return True
                    else:
                        logger.warning(f"⚠️ Clic realizado pero no parece ser página de detalle")
                        logger.warning(f"   URL: {url_actual}")
                        # Aún así, intentemos extraer información
                        return True
                else:
                    logger.error(f"❌ No se pudo hacer clic en ningún elemento de la tarjeta")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error durante el clic en el producto: {e}")
                driver.save_screenshot("error_clic_producto.png")
                return False
        else:
            logger.error(f"❌ No hay tarjeta de producto para hacer clic")
            return False
       
    except Exception as e:
        logger.error(f"❌ Error durante la búsqueda del producto: {e}")
        driver.save_screenshot("error_busqueda_general.png")
        return False
