#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo NADRO - VERSIÓN SIMULANDO NAVEGADOR MÓVIL
✅ SOLUCIÓN: Simula Safari en iPhone / Chrome en Android
✅ OBJETIVO: Evitar bloqueo de navegadores desktop
✅ ESTRATEGIA: NADRO permite móviles pero bloquea desktop
"""

import time
import json
import random
import traceback
import logging
import re
import unicodedata
import tempfile
import shutil
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar undetected_chromedriver solo si está disponible
try:
    import undetected_chromedriver as uc
    uc.Chrome.__del__ = lambda self: None
    UNDETECTED_AVAILABLE = True
except ImportError:
    logger.warning("undetected_chromedriver no está disponible. Se usará selenium estándar.")
    UNDETECTED_AVAILABLE = False
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configuración
USERNAME = "ventas@insumosjip.com"
PASSWORD = "Edu2014$"
MAIN_URL = "https://i22.nadro.mx/"

# ===============================
# 📱 CONFIGURACIÓN MÓVIL PARA NADRO
# ===============================

def get_mobile_user_agents():
    """
    ✅ User Agents reales de navegadores móviles que funcionan con NADRO
    """
    return [
        # Safari en iPhone (iOS 17)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        
        # Chrome en Android
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
        
        # Samsung Internet en Android
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
        
        # Edge en Android
        "Mozilla/5.0 (Linux; Android 12; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) EdgA/119.0.0.0 Mobile Safari/537.36"
    ]

def get_mobile_viewport():
    """
    ✅ Resoluciones móviles reales
    """
    viewports = [
        {"width": 375, "height": 667},   # iPhone SE/8
        {"width": 390, "height": 844},   # iPhone 12/13/14
        {"width": 414, "height": 896},   # iPhone 11/XR
        {"width": 360, "height": 800},   # Android común
        {"width": 412, "height": 915},   # Pixel
    ]
    return random.choice(viewports)

def crear_perfil_movil_temporal():
    """
    ✅ Crea perfil temporal específico para móvil
    """
    timestamp = int(time.time() * 1000)
    random_id = random.randint(1000, 9999)
    temp_dir = tempfile.mkdtemp(prefix=f"nadro_mobile_{timestamp}_{random_id}_")
    
    logger.info(f"📱 Perfil móvil temporal creado: {temp_dir}")
    return temp_dir

def limpiar_perfil_movil(profile_path):
    """
    ✅ Limpia perfil móvil temporal
    """
    try:
        if profile_path and Path(profile_path).exists():
            shutil.rmtree(profile_path, ignore_errors=True)
            logger.info(f"🗑️ Perfil móvil eliminado: {profile_path}")
    except Exception as e:
        logger.warning(f"⚠️ Error eliminando perfil móvil: {e}")

def configurar_headers_moviles(driver):
    """
    ✅ Configura headers específicos de navegadores móviles
    """
    try:
        # Headers que envían los navegadores móviles reales
        mobile_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Aplicar headers usando CDP si está disponible
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": driver.execute_script("return navigator.userAgent;"),
                "acceptLanguage": "es-MX,es;q=0.9,en;q=0.8",
                "platform": "iPhone" if "iPhone" in driver.execute_script("return navigator.userAgent;") else "Linux armv7l"
            })
            
            driver.execute_cdp_cmd('Network.enable', {})
            logger.info("✅ Headers móviles configurados via CDP")
            
        except Exception as e:
            logger.debug(f"CDP headers no disponibles: {e}")
        
        # Inyectar propiedades móviles en JavaScript
        driver.execute_script("""
            // Simular propiedades de dispositivo móvil
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 5
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => navigator.userAgent.includes('iPhone') ? 'iPhone' : 'Linux armv7l'
            });
            
            // Simular eventos touch
            window.TouchEvent = window.TouchEvent || function(){};
            
            // Simular conexión móvil
            if (navigator.connection) {
                Object.defineProperty(navigator.connection, 'effectiveType', {
                    get: () => '4g'
                });
            }
            
            console.log('📱 Propiedades móviles inyectadas');
        """)
        
        logger.info("📱 Configuración móvil aplicada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error configurando headers móviles: {e}")

def inicializar_navegador_movil(headless=True):
    """
    ✅ FUNCIÓN PRINCIPAL: Inicializa navegador simulando móvil
    """
    # Crear perfil temporal para móvil
    profile_path = crear_perfil_movil_temporal()
    
    # Seleccionar configuración móvil aleatoria
    user_agent = random.choice(get_mobile_user_agents())
    viewport = get_mobile_viewport()
    
    logger.info(f"📱 Simulando: {user_agent[:50]}...")
    logger.info(f"📐 Resolución: {viewport['width']}x{viewport['height']}")
    
    if UNDETECTED_AVAILABLE:
        try:
            logger.info("🔧 Iniciando navegador móvil (undetected)...")
            
            options = uc.ChromeOptions()
            
            # ✅ CONFIGURACIÓN MÓVIL CRÍTICA
            options.add_argument(f"--user-agent={user_agent}")
            options.add_argument(f"--window-size={viewport['width']},{viewport['height']}")
            options.add_argument(f"--user-data-dir={profile_path}")
            
            # ✅ SIMULAR DISPOSITIVO MÓVIL
            options.add_argument("--disable-desktop-notifications")
            options.add_argument("--disable-web-security")  # Para mejor simulación móvil
            options.add_argument("--allow-running-insecure-content")
            
            # Configuración de limpieza (mantenida)
            options.add_argument("--incognito")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            
            # Configuración anti-detección
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            
            # Configuración headless si es necesario
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
            
            # ✅ CONFIGURACIÓN EXPERIMENTAL MÓVIL
            mobile_emulation = {
                "deviceMetrics": {
                    "width": viewport['width'],
                    "height": viewport['height'],
                    "pixelRatio": 2.0 if "iPhone" in user_agent else 1.0
                },
                "userAgent": user_agent,
                "touch": True,
                "mobile": True
            }
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            
            # Inicializar navegador
            driver = uc.Chrome(options=options)
            
            # ✅ CONFIGURACIÓN POST-INICIALIZACIÓN
            time.sleep(1)
            
            # Configurar headers móviles
            configurar_headers_moviles(driver)
            
            # Verificar configuración móvil
            mobile_check = driver.execute_script("""
                return {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    maxTouchPoints: navigator.maxTouchPoints,
                    width: window.screen.width,
                    height: window.screen.height,
                    hasTouchEvent: 'TouchEvent' in window
                };
            """)
            
            logger.info(f"📱 Verificación móvil: {mobile_check}")
            
            logger.info("✅ Navegador móvil inicializado (undetected)")
            return driver, profile_path
            
        except Exception as e:
            logger.error(f"❌ Error inicializando navegador móvil (undetected): {e}")
            limpiar_perfil_movil(profile_path)
            logger.info("Intentando con navegador estándar...")
    
    # Respaldo con Selenium estándar
    try:
        options = webdriver.ChromeOptions() if not UNDETECTED_AVAILABLE else Options()
        
        # Aplicar TODA la configuración móvil
        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument(f"--window-size={viewport['width']},{viewport['height']}")
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--incognito")
        options.add_argument("--disable-desktop-notifications")
        
        if headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Emulación móvil
        mobile_emulation = {
            "deviceMetrics": {
                "width": viewport['width'],
                "height": viewport['height'],
                "pixelRatio": 2.0 if "iPhone" in user_agent else 1.0
            },
            "userAgent": user_agent,
            "touch": True,
            "mobile": True
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Anti-detección
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        # Configurar headers móviles
        time.sleep(1)
        configurar_headers_moviles(driver)
        
        logger.info("✅ Navegador móvil inicializado (estándar)")
        return driver, profile_path
        
    except Exception as e:
        logger.error(f"❌ Error inicializando navegador móvil (estándar): {e}")
        limpiar_perfil_movil(profile_path)
        return None, None

def safe_driver_quit_movil(driver, profile_path):
    """
    ✅ Cierre seguro del navegador móvil
    """
    try:
        if driver:
            driver.quit()
            logger.info("✅ Navegador móvil cerrado")
        
        time.sleep(2)
        limpiar_perfil_movil(profile_path)
        
    except Exception as e:
        logger.error(f"❌ Error cerrando navegador móvil: {e}")

# ===============================
# FUNCIONES DE BÚSQUEDA (adaptadas para móvil)
# ===============================

def normalizar_busqueda_nadro(producto_nombre):
    """
    Normaliza la búsqueda para NADRO (misma lógica)
    """
    if not producto_nombre:
        return producto_nombre
    
    texto = producto_nombre.lower().strip()
    
    # Extraer cantidad
    patron_cantidad = r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|ui|iu|%|cc|mgs)'
    match_cantidad = re.search(patron_cantidad, texto)
    cantidad = ""
    if match_cantidad:
        numero = match_cantidad.group(1)
        unidad = match_cantidad.group(2)
        if unidad == 'mgs':
            unidad = 'mg'
        cantidad = f"{numero} {unidad}"
    
    # Extraer nombre del principio activo
    formas_farmaceuticas = [
        'inyectable', 'tabletas', 'tablets', 'cápsulas', 'capsulas', 
        'jarabe', 'solución', 'solucion', 'crema', 'gel', 'ungüento',
        'gotas', 'ampolletas', 'ampollas', 'suspensión', 'suspension',
        'comprimidos', 'pastillas', 'tabs', 'cap', 'sol', 'iny',
        'ampolla', 'vial', 'frasco', 'sobre', 'tubo'
    ]
    
    palabras = texto.split()
    palabras_filtradas = []
    
    for palabra in palabras:
        if re.match(r'\d+(?:\.\d+)?', palabra) or palabra in ['mg', 'g', 'ml', 'mcg', 'ui', 'iu', '%', 'cc', 'mgs']:
            continue
        if re.match(r'\d+(?:\.\d+)?(mg|g|ml|mcg|ui|iu|%|cc|mgs)', palabra):
            continue
        if palabra in formas_farmaceuticas:
            continue
        palabras_filtradas.append(palabra)
    
    if palabras_filtradas:
        if len(palabras_filtradas) == 1:
            nombre = palabras_filtradas[0]
        else:
            nombre = ' '.join(palabras_filtradas[:2])
    else:
        nombre = producto_nombre.split()[0] if producto_nombre.split() else producto_nombre
    
    if cantidad:
        resultado = f"{nombre} {cantidad}"
    else:
        resultado = nombre
    
    logger.info(f"[NADRO MÓVIL] Normalización: '{producto_nombre}' → '{resultado}'")
    return resultado

def buscar_producto_movil(driver, nombre_producto):
    """
    ✅ Búsqueda adaptada para navegador móvil
    """
    try:
        logger.info(f"📱 Buscando producto en modo móvil: {nombre_producto}")
        
        # Verificar que estamos simulando móvil correctamente
        mobile_verification = driver.execute_script("""
            return {
                userAgent: navigator.userAgent.substring(0, 50),
                isMobile: /Mobi|Android/i.test(navigator.userAgent),
                touchPoints: navigator.maxTouchPoints,
                screenWidth: window.screen.width
            };
        """)
        logger.info(f"📱 Verificación móvil: {mobile_verification}")
        
        time.sleep(5)  # Espera inicial para carga
        
        # Buscar campo de búsqueda (mismo que antes)
        search_selectors = [
            "input[placeholder*='Buscar']",
            "input[placeholder*='buscar']",
            "input.vtex-styleguide-9-x-input",
            "div.vtex-store-components-3-x-searchBarContainer input",
            "input[type='text'][placeholder]",
            "div.vtex-search-2-x-searchBar input"
        ]
        
        search_field = None
        for selector in search_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elems:
                    if el.is_displayed():
                        search_field = el
                        logger.info(f"📱 Campo de búsqueda encontrado: {selector}")
                        break
                if search_field:
                    break
            except:
                continue
                
        if not search_field:
            logger.error("❌ No se encontró campo de búsqueda en modo móvil")
            return {"error": "Campo de búsqueda no encontrado", "productos": []}

        # ✅ INTERACCIÓN MÓVIL: Simular touch y typing más lento
        logger.info("📱 Simulando interacción móvil...")
        
        # Scroll hasta el campo de búsqueda
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_field)
        time.sleep(1)
        
        # Simular tap en móvil
        driver.execute_script("arguments[0].focus();", search_field)
        time.sleep(0.8)  # Delay móvil más largo
        
        # Limpiar campo
        search_field.clear()
        time.sleep(0.5)
        
        # ✅ TYPING MÓVIL: Más lento, simula escritura en pantalla táctil
        logger.info(f"📱 Escribiendo en modo móvil: {nombre_producto}")
        for i, char in enumerate(nombre_producto):
            search_field.send_keys(char)
            # Delays variables más largos para simular typing móvil
            delay = random.uniform(0.1, 0.4)
            time.sleep(delay)
            
            # Pausa más larga cada 3-4 caracteres (simula corrección/pensamiento)
            if (i + 1) % 4 == 0:
                time.sleep(random.uniform(0.3, 0.8))
        
        time.sleep(1.5)  # Pausa antes de enviar
        search_field.send_keys(Keys.RETURN)
        
        # ✅ ESPERA MÓVIL: Los móviles son más lentos
        logger.info("📱 Esperando resultados (timing móvil)...")
        time.sleep(10)  # Espera más larga para móviles
        
        # Tomar screenshot para debug
        debug_dir = Path("debug_screenshots")
        debug_dir.mkdir(exist_ok=True)
        driver.save_screenshot(str(debug_dir / "resultados_busqueda_movil.png"))
        
        # Buscar productos (misma lógica)
        product_selectors = [
            "div.vtex-search-result-3-x-galleryItem",
            "article.vtex-product-summary-2-x-element", 
            "div.vtex-product-summary-2-x-container",
            "div[data-testid='gallery-layout-item']"
        ]
        
        productos = []
        for sel in product_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                if elems:
                    productos = elems
                    logger.info(f"📱 Encontrados {len(elems)} productos móviles: {sel}")
                    break
            except:
                continue

        if not productos:
            logger.warning("⚠️ No se encontraron productos en modo móvil")
            return {"warning": "No se encontraron productos", "productos": []}

        # Procesar productos con delays móviles
        resultados = []
        for i, prod in enumerate(productos[:5]):
            try:
                # ✅ SCROLL MÓVIL: Suave y lento
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", prod)
                time.sleep(1.2)  # Delay móvil
                
                info = {}
                
                # Extraer nombre
                for sel in [".vtex-product-summary-2-x-productBrand", "h3", ".vtex-product-summary-2-x-productNameContainer"]:
                    try:
                        el = prod.find_element(By.CSS_SELECTOR, sel)
                        if el.text.strip():
                            info["nombre"] = el.text.strip()
                            logger.info(f"📱 Nombre móvil: {info['nombre']}")
                            break
                    except:
                        pass

                # Extraer precio
                precio_selectors = [
                    ".vtex-product-price-1-x-sellingPrice",
                    ".vtex-store-components-3-x-price", 
                    ".nadro-nadro-components-1-x-priceContainer",
                    ".price"
                ]
                
                for sel in precio_selectors:
                    try:
                        els = prod.find_elements(By.CSS_SELECTOR, sel)
                        for el in els:
                            txt = el.text.strip()
                            if "$" in txt and any(c.isdigit() for c in txt):
                                info["precio_farmacia"] = txt
                                logger.info(f"📱 Precio móvil: {txt}")
                                break
                        if info.get("precio_farmacia"):
                            break
                    except:
                        pass

                # Detectar disponibilidad (misma lógica)
                disponibilidad_detectada = False
                
                try:
                    xpath_comprar = [
                        ".//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'COMPRAR')]",
                        ".//*[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'COMPRAR')]"
                    ]
                    
                    for xpath in xpath_comprar:
                        elementos = prod.find_elements(By.XPATH, xpath)
                        for elem in elementos:
                            if elem.is_displayed():
                                texto_elem = elem.text.strip().upper()
                                if "COMPRAR" in texto_elem:
                                    if elem.tag_name.lower() == "button":
                                        disabled = elem.get_attribute("disabled")
                                        if not disabled:
                                            info["existencia"] = "Disponible"
                                        else:
                                            info["existencia"] = "No disponible"
                                    else:
                                        info["existencia"] = "Disponible"
                                    disponibilidad_detectada = True
                                    logger.info(f"📱 Disponibilidad móvil: {info['existencia']}")
                                    break
                        if disponibilidad_detectada:
                            break
                except Exception as e:
                    logger.debug(f"Error disponibilidad móvil: {e}")

                if not disponibilidad_detectada:
                    info["existencia"] = "Estado desconocido"

                if info.get("nombre"):
                    resultados.append(info)
                    logger.info(f"📱 Producto móvil #{i+1}: {info['nombre']} - {info.get('precio_farmacia', 'N/D')} - {info['existencia']}")
                
            except Exception as e:
                logger.error(f"❌ Error procesando producto móvil {i+1}: {e}")
                continue

        if resultados:
            logger.info(f"✅ {len(resultados)} productos procesados en modo móvil")
            return {"success": True, "productos": resultados}
        else:
            return {"warning": "No se pudieron procesar productos móviles", "productos": []}

    except Exception as e:
        logger.error(f"❌ Error en búsqueda móvil: {e}")
        return {"error": str(e), "productos": []}

def login_and_search_movil(producto):
    """
    ✅ FUNCIÓN PRINCIPAL: Login y búsqueda en modo móvil
    """
    driver = None
    profile_path = None
    
    try:
        logger.info("📱 ===== INICIANDO SESIÓN EN MODO MÓVIL =====")
        
        # Inicializar navegador móvil
        driver, profile_path = inicializar_navegador_movil(headless=True)
        if not driver:
            return {"error": "No se pudo inicializar navegador móvil", "productos": []}
        
        # Navegar con timing móvil
        logger.info(f"📱 Navegando a {MAIN_URL} en modo móvil...")
        driver.get(MAIN_URL)
        time.sleep(random.uniform(5, 8))  # Móviles son más lentos
        
        # Verificar carga móvil
        page_info = driver.execute_script("""
            return {
                readyState: document.readyState,
                userAgent: navigator.userAgent.substring(0, 60),
                viewport: {width: window.innerWidth, height: window.innerHeight}
            };
        """)
        logger.info(f"📱 Estado página móvil: {page_info}")
        
        # Buscar acceso a login (adaptado para móvil)
        logger.info("📱 Buscando acceso a login en interfaz móvil...")
        
        # En móvil, el login puede estar en un menú hamburguesa
        login_selectors = [
            "a[href*='login']", 
            "a.vtex-login-2-x-button",
            "span:contains('Iniciar sesión')",
            "button:contains('Ingresar')",
            "a:contains('Iniciar sesión')",
            ".menu-toggle",  # Menú hamburguesa
            ".mobile-menu-button",
            "[aria-label*='menu']"
        ]
        
        login_found = False
        for selector in login_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info(f"📱 Elemento login móvil encontrado: {selector}")
                        # Scroll suave antes de hacer click
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(1)
                        element.click()
                        login_found = True
                        time.sleep(random.uniform(5, 8))  # Espera móvil
                        break
                if login_found:
                    break
            except:
                continue
        
        if not login_found:
            logger.info("📱 Navegando directamente a URL login móvil...")
            driver.get("https://i22.nadro.mx/login")
            time.sleep(random.uniform(5, 8))
        
        # Captura móvil
        debug_dir = Path("debug_screenshots") 
        debug_dir.mkdir(exist_ok=True)
        driver.save_screenshot(str(debug_dir / "login_movil.png"))
        
        # ✅ PROCESO DE LOGIN MÓVIL
        logger.info("📱 Iniciando login en modo móvil...")
        
        try:
            # Campo usuario (con mayor timeout para móvil)
            username_field = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text'], input[type='email'], #username, input[name='username']"))
            )
            
            # ✅ INTERACCIÓN MÓVIL USUARIO
            logger.info(f"📱 Ingresando usuario móvil: {USERNAME}")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", username_field)
            time.sleep(1)
            driver.execute_script("arguments[0].focus();", username_field)
            time.sleep(0.8)
            
            username_field.clear()
            time.sleep(1)
            
            # Typing móvil (más lento)
            for char in USERNAME:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.15, 0.4))
            
            time.sleep(random.uniform(1, 2))
            
            # Campo contraseña
            password_field = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password'], #password, input[name='password']"))
            )
            
            # ✅ INTERACCIÓN MÓVIL CONTRASEÑA
            logger.info("📱 Ingresando contraseña móvil...")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", password_field)
            time.sleep(1)
            driver.execute_script("arguments[0].focus();", password_field)
            time.sleep(0.8)
            
            password_field.clear()
            time.sleep(1)
            
            for char in PASSWORD:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.15, 0.4))
            
            time.sleep(random.uniform(1.5, 2.5))
            
            # Botón login móvil
            button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Iniciar sesión')",
                "button:contains('Ingresar')"
            ]
            
            login_button = None
            for selector in button_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            login_button = element
                            break
                    if login_button:
                        break
                except:
                    continue
            
            # ✅ ENVIAR LOGIN MÓVIL
            if login_button:
                logger.info("📱 Enviando login móvil...")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", login_button)
                time.sleep(1)
                login_button.click()
            else:
                logger.info("📱 Enviando con Enter móvil...")
                password_field.send_keys(Keys.RETURN)
            
            # ✅ ESPERA MÓVIL EXTENDIDA (crítico para NADRO)
            logger.info("📱 Esperando procesamiento login móvil (timing extendido)...")
            time.sleep(18)  # Tiempo AÚN MÁS largo para móviles
            
            # Captura post-login móvil
            driver.save_screenshot(str(debug_dir / "post_login_movil.png"))
            
            # Verificar login móvil exitoso
            current_url = driver.current_url.lower()
            page_text = driver.page_source.lower()
            
            login_exitoso = (
                "login" not in current_url or
                "logout" in page_text or
                "cerrar sesión" in page_text or
                "mi cuenta" in page_text or
                "bienvenido" in page_text
            )
            
            if login_exitoso:
                logger.info("✅ LOGIN MÓVIL EXITOSO!")
                
                # Pequeña pausa adicional para estabilizar
                time.sleep(3)
                
                # Proceder con búsqueda móvil
                resultado = buscar_producto_movil(driver, producto)
                return resultado
            else:
                logger.error("❌ Login móvil falló")
                
                # Debug móvil
                debug_logs_dir = Path("debug_logs")
                debug_logs_dir.mkdir(exist_ok=True)
                with open(debug_logs_dir / "login_movil_fallido.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
                return {"error": "Login móvil falló", "productos": []}
                
        except Exception as e:
            logger.error(f"❌ Error en proceso login móvil: {e}")
            driver.save_screenshot(str(debug_dir / "error_login_movil.png"))
            return {"error": f"Error login móvil: {str(e)}", "productos": []}
    
    except Exception as e:
        logger.error(f"❌ Error general login móvil: {e}")
        return {"error": str(e), "productos": []}
    
    finally:
        # Limpieza móvil
        logger.info("📱 Limpieza final móvil...")
        safe_driver_quit_movil(driver, profile_path)

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    ✅ FUNCIÓN PRINCIPAL: Búsqueda NADRO simulando navegador móvil
    """
    try:
        logger.info(f"📱 BÚSQUEDA NADRO MODO MÓVIL: {nombre_medicamento}")
        logger.info("🎯 ESTRATEGIA: Simular Safari/Chrome móvil (NADRO permite móviles)")
        
        # Normalizar búsqueda
        nombre_normalizado = normalizar_busqueda_nadro(nombre_medicamento)
        
        # Crear directorios debug
        Path("debug_screenshots").mkdir(exist_ok=True)
        Path("debug_logs").mkdir(exist_ok=True)
        
        # ✅ USAR FUNCIÓN MÓVIL
        resultado = login_and_search_movil(nombre_normalizado)
        
        # Procesar resultado
        if "error" in resultado:
            return {
                "nombre": nombre_medicamento,
                "error": resultado["error"],
                "estado": "error",
                "fuente": "NADRO",
                "existencia": "0"
            }
        
        if "warning" in resultado or not resultado.get("productos"):
            return {
                "nombre": nombre_medicamento,
                "mensaje": resultado.get("warning", "No se encontraron productos"),
                "estado": "no_encontrado",
                "fuente": "NADRO",
                "existencia": "0"
            }
        
        # Formatear primer producto
        if resultado.get("productos"):
            primer_producto = resultado["productos"][0]
            
            info_producto = {
                "nombre": primer_producto.get("nombre", nombre_medicamento),
                "laboratorio": primer_producto.get("laboratorio", "No disponible"),
                "codigo_barras": primer_producto.get("codigo_barras", "No disponible"),
                "registro_sanitario": "No disponible",
                "url": "https://i22.nadro.mx/",
                "imagen": primer_producto.get("imagen", ""),
                "precio": primer_producto.get("precio_farmacia", "No disponible"),
                "existencia": "0",
                "fuente": "NADRO",
                "estado": "encontrado"
            }
            
            # Procesar existencia
            existencia_raw = primer_producto.get("existencia", "")
            if existencia_raw:
                if "disponible" in existencia_raw.lower():
                    info_producto["existencia"] = "Si"
                else:
                    info_producto["existencia"] = "0"
            
            logger.info(f"✅ PRODUCTO ENCONTRADO MODO MÓVIL: {info_producto['nombre']} - {info_producto['precio']} - Stock: {info_producto['existencia']}")
            return info_producto
        
        return {
            "nombre": nombre_medicamento,
            "mensaje": "No se pudo procesar respuesta NADRO móvil",
            "estado": "error",
            "fuente": "NADRO",
            "existencia": "0"
        }
        
    except Exception as e:
        logger.error(f"❌ Error general NADRO móvil: {e}")
        return {
            "nombre": nombre_medicamento,
            "error": str(e),
            "estado": "error",
            "fuente": "NADRO",
            "existencia": "0"
        }

if __name__ == "__main__":
    import sys
    
    print("📱 === NADRO SCRAPER MODO MÓVIL ===")
    print("🎯 Simula Safari en iPhone / Chrome en Android")
    print("✅ Evita bloqueo de navegadores desktop")
    
    if len(sys.argv) > 1:
        medicamento = " ".join(sys.argv[1:])
    else:
        medicamento = input("Nombre del medicamento: ")
    
    print(f"\n📱 Iniciando búsqueda móvil para: {medicamento}")
    print("⏳ Simulando navegador móvil...")
    
    resultado = buscar_info_medicamento(medicamento)
    
    if resultado.get('estado') == 'encontrado':
        print(f"\n✅ ÉXITO CON NAVEGADOR MÓVIL")
        print(f"Producto: {resultado['nombre']}")
        print(f"Precio: {resultado['precio']}")
        print(f"Stock: {resultado['existencia']}")
    else:
        print(f"\n❌ {resultado.get('mensaje', resultado.get('error', 'Error desconocido'))}")
    
    print(f"\n📱 Simulación móvil completada.")
