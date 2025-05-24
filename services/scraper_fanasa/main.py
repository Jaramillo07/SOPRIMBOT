#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import re
import os
import signal
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

# ✅ CONFIGURACIÓN OPTIMIZADA PARA TIMEOUTS RÁPIDOS
USERNAME = "ventas@insumosjip.com"
PASSWORD = "210407"
LOGIN_URL = "https://carrito.fanasa.com/login"
TIMEOUT = 8  # ✅ REDUCIDO de 20 a 8 segundos
MAX_TOTAL_TIME = 45  # ✅ MÁXIMO 45 segundos para todo el proceso
PAGE_LOAD_TIMEOUT = 15  # ✅ Timeout específico para carga de páginas

class TimeoutError(Exception):
    """Excepción para timeout general del proceso"""
    pass

def timeout_handler(signum, frame):
    """Manejador para timeout general"""
    raise TimeoutError("Proceso FANASA excedió el tiempo máximo permitido")

def inicializar_navegador(headless=True):
    """
    Navegador optimizado para velocidad y timeouts cortos.
    """
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    # ✅ CONFIGURACIÓN MÍNIMA PARA VELOCIDAD
    options.add_argument("--window-size=1280,720")  # ✅ Ventana más pequeña = más rápido
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # ✅ OPTIMIZACIONES ADICIONALES PARA VELOCIDAD
    options.add_argument("--disable-images")  # ✅ No cargar imágenes = más rápido
    options.add_argument("--disable-javascript")  # ✅ Menos JS = más rápido (si es posible)
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    
    # ✅ CONFIGURACIÓN DE RED OPTIMIZADA
    options.add_argument("--aggressive-cache-discard")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    
    # ✅ SSL RÁPIDO
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-insecure-localhost")
    
    # ✅ LOGGING MÍNIMO
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # ✅ TIMEOUTS AGRESIVOS PARA VELOCIDAD
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(3)  # ✅ Reducido de timeout implícito
        
        logger.info("Navegador Chrome inicializado con timeouts optimizados")
        return driver
    except Exception as e:
        logger.error(f"Error al inicializar navegador: {e}")
        return None

def safe_screenshot(driver, filename):
    """Toma screenshot de forma segura con timeout"""
    try:
        driver.save_screenshot(filename)
        return True
    except Exception as e:
        logger.warning(f"No se pudo tomar screenshot {filename}: {e}")
        return False

def safe_find_element(driver, by, value, timeout=3):
    """Busca elemento con timeout corto"""
    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        return None

def login_fanasa_carrito():
    """
    Login optimizado con timeouts agresivos y manejo de errores mejorado.
    """
    # ✅ CONFIGURAR TIMEOUT GENERAL PARA TODO EL PROCESO
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(MAX_TOTAL_TIME)
    
    driver = None
    try:
        driver = inicializar_navegador(headless=True)
        if not driver:
            logger.error("No se pudo inicializar navegador")
            return None
        
        # ✅ 1. Navegar con timeout corto
        logger.info(f"Navegando a login: {LOGIN_URL}")
        try:
            driver.get(LOGIN_URL)
            time.sleep(2)  # ✅ Reducido de 5 a 2 segundos
        except Exception as e:
            logger.error(f"Error navegando a login: {e}")
            return None
        
        safe_screenshot(driver, "01_fanasa_login.png")
        
        # ✅ 2. Buscar campo usuario - RÁPIDO
        logger.info("Buscando campo usuario...")
        username_field = None
        
        # Intentar selectores más específicos primero
        selectors = [
            "input[type='email']",
            "input[placeholder*='Usuario']",
            "input[placeholder*='correo']"
        ]
        
        for selector in selectors:
            username_field = safe_find_element(driver, By.CSS_SELECTOR, selector, 2)
            if username_field and username_field.is_displayed():
                logger.info(f"Campo usuario encontrado: {selector}")
                break
        
        # Fallback: primer input visible
        if not username_field:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.is_displayed():
                    username_field = inp
                    logger.info("Usando primer input visible")
                    break
        
        if not username_field:
            logger.error("No se encontró campo usuario")
            return None
        
        # ✅ 3. Ingresar usuario - RÁPIDO
        try:
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info("Usuario ingresado")
            time.sleep(0.5)  # ✅ Pausa mínima
        except Exception as e:
            logger.error(f"Error ingresando usuario: {e}")
            return None
        
        # ✅ 4. Buscar campo contraseña - RÁPIDO
        password_field = safe_find_element(driver, By.CSS_SELECTOR, "input[type='password']", 2)
        
        if not password_field:
            logger.error("No se encontró campo contraseña")
            return None
        
        # ✅ 5. Ingresar contraseña - RÁPIDO
        try:
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("Contraseña ingresada")
            time.sleep(0.5)  # ✅ Pausa mínima
        except Exception as e:
            logger.error(f"Error ingresando contraseña: {e}")
            return None
        
        # ✅ 6. Submit con Enter (más rápido que buscar botón)
        logger.info("Enviando formulario...")
        try:
            password_field.send_keys(Keys.RETURN)
            time.sleep(3)  # ✅ Espera mínima para login
        except Exception as e:
            logger.error(f"Error enviando formulario: {e}")
            return None
        
        # ✅ 7. Verificación rápida de login
        try:
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            # Verificaciones rápidas
            login_success = (
                "/login" not in current_url or
                "carrito" in page_source or
                "mi cuenta" in page_source or
                "cerrar sesión" in page_source
            )
            
            if login_success:
                logger.info("✅ LOGIN EXITOSO EN FANASA")
                safe_screenshot(driver, "02_fanasa_login_exitoso.png")
                return driver
            else:
                logger.error("❌ LOGIN FALLIDO EN FANASA")
                safe_screenshot(driver, "02_fanasa_login_fallido.png")
                driver.quit()
                return None
                
        except Exception as e:
            logger.error(f"Error verificando login: {e}")
            driver.quit()
            return None
            
    except TimeoutError:
        logger.error("⏰ TIMEOUT: Login de FANASA excedió tiempo máximo")
        if driver:
            driver.quit()
        return None
    except Exception as e:
        logger.error(f"Error general en login: {e}")
        if driver:
            driver.quit()
        return None
    finally:
        signal.alarm(0)  # Cancelar alarma

def buscar_producto_rapido(driver, nombre_producto):
    """
    Búsqueda optimizada para velocidad.
    """
    if not driver:
        return False
    
    try:
        logger.info(f"🔍 Búsqueda rápida: {nombre_producto}")
        
        # ✅ Buscar campo de búsqueda con timeout corto
        search_field = None
        search_selectors = [
            "input[name*='search']",
            "input[placeholder*='Nombre']",
            "input[placeholder*='producto']"
        ]
        
        for selector in search_selectors:
            search_field = safe_find_element(driver, By.CSS_SELECTOR, selector, 2)
            if search_field and search_field.is_displayed():
                break
        
        # Fallback: primer input text visible
        if not search_field:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for inp in inputs:
                if inp.is_displayed():
                    search_field = inp
                    break
        
        if not search_field:
            logger.error("Campo búsqueda no encontrado")
            return False
        
        # ✅ Búsqueda rápida
        try:
            search_field.clear()
            search_field.send_keys(nombre_producto)
            search_field.send_keys(Keys.RETURN)
            time.sleep(3)  # ✅ Espera mínima para resultados
            logger.info("Búsqueda enviada")
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return False
        
        # ✅ Verificación rápida de resultados
        page_source = driver.page_source.lower()
        tiene_resultados = (
            nombre_producto.lower() in page_source or
            "precio" in page_source or
            "producto" in page_source or
            "carrito" in page_source
        )
        
        if tiene_resultados:
            logger.info("✅ Resultados encontrados")
            safe_screenshot(driver, "03_fanasa_resultados.png")
            return True
        else:
            logger.warning("❌ No se encontraron resultados")
            return False
            
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return False

def extraer_info_basica(driver):
    """
    Extracción básica y rápida de información esencial.
    """
    try:
        logger.info("Extrayendo información básica...")
        
        page_source = driver.page_source
        
        info_producto = {
            'url': driver.current_url,
            'nombre': '',
            'precio_neto': '',
            'precio_publico': '',
            'precio_farmacia': '',
            'codigo': '',
            'laboratorio': '',
            'disponibilidad': 'Stock disponible',  # Valor por defecto
            'imagen': '',
            'fuente': 'FANASA',
            'estado': 'encontrado'
        }
        
        # ✅ Extracción rápida con regex
        try:
            # Buscar precios en el HTML
            import re
            precios = re.findall(r'\$\s*[\d,]+\.?\d*', page_source)
            if precios:
                info_producto['precio_neto'] = precios[0]
                if len(precios) > 1:
                    info_producto['precio_publico'] = precios[1]
                logger.info(f"Precios encontrados: {precios[:2]}")
        except:
            pass
        
        # ✅ Buscar nombre básico
        try:
            h_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
            for h in h_elements:
                texto = h.text.strip()
                if len(texto) > 10 and "precio" not in texto.lower():
                    info_producto['nombre'] = texto
                    logger.info(f"Nombre encontrado: {texto}")
                    break
        except:
            pass
        
        # ✅ Si no hay nombre, usar genérico
        if not info_producto['nombre']:
            info_producto['nombre'] = "Producto FANASA"
        
        # ✅ Buscar código básico
        try:
            codigo_match = re.search(r'\b\d{7,}\b', page_source)
            if codigo_match:
                info_producto['codigo'] = codigo_match.group()
                logger.info(f"Código encontrado: {info_producto['codigo']}")
        except:
            pass
        
        logger.info("✅ Información básica extraída")
        return info_producto
        
    except Exception as e:
        logger.error(f"Error extrayendo información: {e}")
        return None

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal OPTIMIZADA para velocidad máxima.
    """
    start_time = time.time()
    driver = None
    
    try:
        logger.info(f"🚀 Inicio búsqueda RÁPIDA FANASA: {nombre_medicamento}")
        
        # ✅ 1. Login rápido
        driver = login_fanasa_carrito()
        if not driver:
            elapsed = time.time() - start_time
            logger.error(f"❌ Login fallido en {elapsed:.1f}s")
            return {
                "error": "error_login",
                "mensaje": "Login fallido en FANASA",
                "estado": "error",
                "fuente": "FANASA",
                "tiempo_transcurrido": elapsed
            }
        
        # ✅ 2. Búsqueda rápida
        if not buscar_producto_rapido(driver, nombre_medicamento):
            elapsed = time.time() - start_time
            logger.warning(f"❌ Producto no encontrado en {elapsed:.1f}s")
            return {
                "nombre": nombre_medicamento,
                "mensaje": f"No encontrado en FANASA",
                "estado": "no_encontrado",
                "fuente": "FANASA",
                "existencia": "0",
                "tiempo_transcurrido": elapsed
            }
        
        # ✅ 3. Extracción rápida
        info_producto = extraer_info_basica(driver)
        
        elapsed = time.time() - start_time
        
        if info_producto:
            # Añadir información de compatibilidad
            info_producto['existencia'] = '1'  # Asumimos que hay si se encontró
            info_producto['tiempo_transcurrido'] = elapsed
            
            logger.info(f"✅ FANASA completado en {elapsed:.1f}s")
            return info_producto
        else:
            logger.error(f"❌ Error extracción en {elapsed:.1f}s")
            return {
                "nombre": nombre_medicamento,
                "mensaje": "Error extrayendo información",
                "estado": "error_extraccion",
                "fuente": "FANASA",
                "existencia": "0",
                "tiempo_transcurrido": elapsed
            }
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Error general FANASA en {elapsed:.1f}s: {e}")
        return {
            "nombre": nombre_medicamento,
            "mensaje": f"Error: {str(e)}",
            "estado": "error",
            "fuente": "FANASA",
            "existencia": "0",
            "tiempo_transcurrido": elapsed
        }
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Navegador cerrado")
            except:
                pass
