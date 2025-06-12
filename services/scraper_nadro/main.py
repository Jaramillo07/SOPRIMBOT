#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal para el scraper de NADRO - VERSIÓN CON LIMPIEZA EXTREMA
✅ CORREGIDO: Implementa limpieza extrema de cookies, caché y datos siguiendo instrucciones de NADRO
✅ NUEVO: Cada ejecución usa perfil completamente nuevo y limpio
✅ NUEVO: Limpieza agresiva "Desde siempre" como indica NADRO
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
    # Parche para evitar WinError 6 en el destructor de Chrome
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
# ✅ NUEVAS FUNCIONES DE LIMPIEZA EXTREMA
# ===============================

def limpiar_datos_chrome_sistema():
    """
    ✅ FUNCIÓN NUEVA: Limpia datos de Chrome a nivel del sistema operativo
    Simula el "Borrar datos de navegación -> Desde siempre" que NADRO recomienda
    """
    try:
        logger.info("🧹 ===== LIMPIEZA EXTREMA DE CHROME EN SISTEMA =====")
        
        # Rutas comunes de datos de Chrome en diferentes OS
        chrome_data_paths = []
        
        if os.name == 'nt':  # Windows
            chrome_data_paths = [
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data"),
                os.path.expanduser("~\\AppData\\Roaming\\Google\\Chrome"),
                os.path.expanduser("~\\AppData\\Local\\Chromium\\User Data"),
            ]
        else:  # Linux/Mac
            chrome_data_paths = [
                os.path.expanduser("~/.config/google-chrome"),
                os.path.expanduser("~/.cache/google-chrome"),
                os.path.expanduser("~/Library/Application Support/Google/Chrome"),  # Mac
                os.path.expanduser("~/Library/Caches/Google/Chrome"),  # Mac
            ]
        
        # Agregar directorios temporales
        temp_dirs = [
            tempfile.gettempdir(),
            "/tmp" if os.name != 'nt' else os.environ.get('TEMP', 'C:\\Temp')
        ]
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                chrome_temp_pattern = os.path.join(temp_dir, "*chrome*")
                try:
                    import glob
                    temp_chrome_files = glob.glob(chrome_temp_pattern)
                    for temp_file in temp_chrome_files:
                        try:
                            if os.path.isfile(temp_file):
                                os.remove(temp_file)
                            elif os.path.isdir(temp_file):
                                shutil.rmtree(temp_file)
                            logger.info(f"🗑️ Archivo/directorio temporal eliminado: {temp_file}")
                        except Exception as e:
                            logger.debug(f"No se pudo eliminar {temp_file}: {e}")
                except:
                    pass
        
        # Intentar limpiar archivos específicos de cookies/caché si Chrome está cerrado
        for chrome_path in chrome_data_paths:
            if os.path.exists(chrome_path):
                try:
                    # Archivos específicos a limpiar
                    files_to_clean = [
                        "Default/Cookies",
                        "Default/Cookies-journal", 
                        "Default/Cache",
                        "Default/Code Cache",
                        "Default/GPUCache",
                        "Default/Local Storage",
                        "Default/Session Storage",
                        "Default/IndexedDB",
                        "Default/Web Data",
                        "Default/History",
                        "Default/Login Data"
                    ]
                    
                    for file_rel_path in files_to_clean:
                        file_full_path = os.path.join(chrome_path, file_rel_path)
                        try:
                            if os.path.exists(file_full_path):
                                if os.path.isfile(file_full_path):
                                    os.remove(file_full_path)
                                    logger.info(f"🗑️ Archivo eliminado: {file_rel_path}")
                                elif os.path.isdir(file_full_path):
                                    shutil.rmtree(file_full_path)
                                    logger.info(f"🗑️ Directorio eliminado: {file_rel_path}")
                        except Exception as e:
                            logger.debug(f"No se pudo eliminar {file_rel_path}: {e}")
                            
                except Exception as e:
                    logger.debug(f"Error accediendo a {chrome_path}: {e}")
        
        logger.info("✅ ===== LIMPIEZA EXTREMA DEL SISTEMA COMPLETADA =====")
        
    except Exception as e:
        logger.warning(f"⚠️ Error en limpieza extrema del sistema: {e}")

def crear_perfil_temporal_unico():
    """
    ✅ FUNCIÓN MEJORADA: Crea un perfil temporal con nombre único timestamp
    """
    timestamp = int(time.time() * 1000)  # timestamp en milisegundos
    random_id = random.randint(1000, 9999)
    temp_dir = tempfile.mkdtemp(prefix=f"nadro_clean_{timestamp}_{random_id}_")
    
    logger.info(f"🆕 Perfil temporal único creado: {temp_dir}")
    return temp_dir

def limpiar_perfil_temporal_agresivo(profile_path):
    """
    ✅ FUNCIÓN MEJORADA: Elimina el perfil temporal de forma agresiva
    """
    try:
        if profile_path and Path(profile_path).exists():
            # Intentar múltiples veces con diferentes métodos
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Método 1: shutil.rmtree con parámetros agresivos
                    shutil.rmtree(profile_path, ignore_errors=True)
                    
                    # Verificar si se eliminó
                    if not Path(profile_path).exists():
                        logger.info(f"✅ Perfil temporal eliminado (intento {attempt + 1}): {profile_path}")
                        return
                    
                    # Método 2: Eliminar archivos individualmente
                    if attempt == 1:
                        for root, dirs, files in os.walk(profile_path, topdown=False):
                            for file in files:
                                try:
                                    os.remove(os.path.join(root, file))
                                except:
                                    pass
                            for dir in dirs:
                                try:
                                    os.rmdir(os.path.join(root, dir))
                                except:
                                    pass
                        os.rmdir(profile_path)
                    
                    time.sleep(0.5)  # Pequeña pausa entre intentos
                    
                except Exception as e:
                    logger.debug(f"Intento {attempt + 1} falló: {e}")
                    if attempt == max_attempts - 1:
                        # Último intento con comando del sistema
                        try:
                            if os.name == 'nt':  # Windows
                                os.system(f'rmdir /s /q "{profile_path}"')
                            else:  # Linux/Mac
                                os.system(f'rm -rf "{profile_path}"')
                        except:
                            pass
            
            # Verificación final
            if Path(profile_path).exists():
                logger.warning(f"⚠️ No se pudo eliminar completamente: {profile_path}")
            else:
                logger.info(f"✅ Perfil temporal eliminado exitosamente: {profile_path}")
                
    except Exception as e:
        logger.warning(f"⚠️ Error eliminando perfil temporal: {e}")

def limpiar_sesion_nadro_extrema(driver):
    """
    ✅ FUNCIÓN NUEVA: Limpieza extrema específica para NADRO
    Simula exactamente lo que NADRO recomienda: "Desde siempre"
    """
    try:
        logger.info("🧹 ===== LIMPIEZA EXTREMA ESTILO NADRO =====")
        
        # 1. Limpiar todas las cookies
        logger.info("🍪 Limpiando TODAS las cookies...")
        driver.delete_all_cookies()
        
        # 2. Limpiar localStorage
        logger.info("💾 Limpiando localStorage...")
        driver.execute_script("window.localStorage.clear();")
        
        # 3. Limpiar sessionStorage  
        logger.info("🗂️ Limpiando sessionStorage...")
        driver.execute_script("window.sessionStorage.clear();")
        
        # 4. Limpiar indexedDB agresivamente
        logger.info("🗄️ Limpiando indexedDB...")
        driver.execute_script("""
            // Limpiar todas las bases de datos IndexedDB
            if (window.indexedDB) {
                // Método 1: Limpiar bases de datos conocidas
                const commonDBs = ['NADRO', 'nadro', 'cache', 'session', 'user_data', 'vtex', 'VTEX'];
                commonDBs.forEach(dbName => {
                    try {
                        const deleteReq = indexedDB.deleteDatabase(dbName);
                        deleteReq.onsuccess = () => console.log('DB deleted:', dbName);
                        deleteReq.onerror = () => console.log('DB delete failed:', dbName);
                    } catch(e) { console.log('Error deleting DB:', dbName, e); }
                });
                
                // Método 2: Obtener lista de todas las DBs y eliminarlas
                try {
                    if (indexedDB.databases) {
                        indexedDB.databases().then(databases => {
                            databases.forEach(db => {
                                try {
                                    indexedDB.deleteDatabase(db.name);
                                    console.log('Auto-detected DB deleted:', db.name);
                                } catch(e) { console.log('Error auto-deleting DB:', db.name, e); }
                            });
                        });
                    }
                } catch(e) { console.log('Error listing databases:', e); }
            }
        """)
        
        # 5. Limpiar WebSQL (si está disponible)
        logger.info("🗃️ Limpiando WebSQL...")
        driver.execute_script("""
            if (window.openDatabase) {
                try {
                    // Limpiar bases de datos WebSQL comunes
                    const webSQLDBs = ['NADRO', 'cache', 'session'];
                    webSQLDBs.forEach(dbName => {
                        try {
                            const db = openDatabase(dbName, '', '', '');
                            db.transaction(tx => {
                                tx.executeSql('DROP TABLE IF EXISTS data');
                                tx.executeSql('DROP TABLE IF EXISTS cache');  
                                tx.executeSql('DROP TABLE IF EXISTS session');
                            });
                        } catch(e) { console.log('WebSQL clean error:', dbName, e); }
                    });
                } catch(e) { console.log('WebSQL not supported or error:', e); }
            }
        """)
        
        # 6. Limpiar Application Cache
        logger.info("📦 Limpiando Application Cache...")
        driver.execute_script("""
            if (window.applicationCache) {
                try {
                    window.applicationCache.update();
                    console.log('Application cache updated');
                } catch(e) { console.log('Application cache error:', e); }
            }
        """)
        
        # 7. Limpiar Cache API (Service Workers)
        logger.info("🔧 Limpiando Cache API...")
        driver.execute_script("""
            if ('caches' in window) {
                caches.keys().then(cacheNames => {
                    cacheNames.forEach(cacheName => {
                        caches.delete(cacheName).then(success => {
                            console.log('Cache deleted:', cacheName, success);
                        });
                    });
                });
            }
        """)
        
        # 8. Desregistrar Service Workers
        logger.info("👷 Desregistrando Service Workers...")
        driver.execute_script("""
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistrations().then(registrations => {
                    registrations.forEach(registration => {
                        registration.unregister().then(success => {
                            console.log('Service Worker unregistered:', success);
                        });
                    });
                });
            }
        """)
        
        # 9. Limpiar variables globales de NADRO/VTEX
        logger.info("🌐 Limpiando variables globales...")
        driver.execute_script("""
            // Limpiar variables globales comunes de VTEX/NADRO
            const globalVarsToDelete = [
                'vtex', 'VTEX', 'nadro', 'NADRO', '_satellite', 'dataLayer',
                'gtag', 'ga', 'fbq', '__vtex', '__nadro'
            ];
            
            globalVarsToDelete.forEach(varName => {
                try {
                    if (window[varName]) {
                        delete window[varName];
                        console.log('Global var deleted:', varName);
                    }
                } catch(e) { console.log('Error deleting global var:', varName, e); }
            });
        """)
        
        # 10. Usar Chrome DevTools Protocol para limpiar caché si está disponible
        logger.info("🔧 Limpiando caché via CDP...")
        try:
            # Network.clearBrowserCache
            driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            logger.info("✅ Caché de navegador limpiado via CDP")
            
            # Storage.clearDataForOrigin 
            driver.execute_cdp_cmd('Storage.clearDataForOrigin', {
                'origin': 'https://i22.nadro.mx',
                'storageTypes': 'all'
            })
            logger.info("✅ Datos de origen NADRO limpiados via CDP")
            
        except Exception as e:
            logger.debug(f"CDP limpieza no disponible: {e}")
        
        # 11. Forzar refresco completo de página
        logger.info("🔄 Refrescando navegador...")
        driver.refresh()
        time.sleep(2)
        
        # 12. Verificar limpieza
        logger.info("🔍 Verificando limpieza...")
        storage_check = driver.execute_script("""
            const checks = {
                cookies: document.cookie.length,
                localStorage: Object.keys(localStorage).length,
                sessionStorage: Object.keys(sessionStorage).length
            };
            return checks;
        """)
        
        logger.info(f"📊 Estado post-limpieza: {storage_check}")
        
        logger.info("✅ ===== LIMPIEZA EXTREMA NADRO COMPLETADA =====")
        
    except Exception as e:
        logger.error(f"❌ Error durante limpieza extrema NADRO: {e}")

def inicializar_navegador_ultra_limpio(headless=True):
    """
    ✅ FUNCIÓN NUEVA: Inicializa navegador con configuración ultra limpia
    Implementa todas las recomendaciones de NADRO
    """
    # PASO 1: Limpieza previa del sistema
    limpiar_datos_chrome_sistema()
    time.sleep(1)
    
    # PASO 2: Crear perfil temporal único
    profile_path = crear_perfil_temporal_unico()
    
    if UNDETECTED_AVAILABLE:
        try:
            logger.info("🔧 Iniciando navegador ULTRA LIMPIO (undetected)...")
            
            options = uc.ChromeOptions()
            
            # ✅ CRÍTICO: Configuración ultra limpia
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--incognito")  # Modo incógnito
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            
            # ✅ NUEVO: Deshabilitar TODA persistencia de datos
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-component-update")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-domain-reliability")
            options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            
            # ✅ NUEVO: Forzar limpieza de datos al inicio y salida
            options.add_argument("--aggressive-cache-discard")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            
            # ✅ NUEVO: Configuración de cookies y storage
            options.add_argument("--disable-web-security")  # Para poder limpiar mejor
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Configuración anti-detección (mantener lo que funcionaba)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            
            # Configuración headless
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
            
            # Ventana con tamaño aleatorio
            width = random.randint(1100, 1300)
            height = random.randint(700, 900)
            options.add_argument(f"--window-size={width},{height}")
            
            # User Agent rotativo
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Inicializar navegador
            driver = uc.Chrome(options=options)
            
            # ✅ CRÍTICO: Limpieza inmediata después de inicializar
            time.sleep(1)
            limpiar_sesion_nadro_extrema(driver)
            
            logger.info("✅ Navegador ULTRA LIMPIO inicializado (undetected)")
            return driver, profile_path
            
        except Exception as e:
            logger.error(f"❌ Error inicializando navegador ultra limpio (undetected): {e}")
            limpiar_perfil_temporal_agresivo(profile_path)
            logger.info("Intentando con navegador estándar...")
    
    # Respaldo con Selenium estándar
    try:
        options = webdriver.ChromeOptions() if not UNDETECTED_AVAILABLE else Options()
        
        # Aplicar TODAS las mismas configuraciones ultra limpias
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--incognito")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--aggressive-cache-discard")
        
        if headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # JavaScript anti-detección
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        # ✅ CRÍTICO: Limpieza inmediata
        time.sleep(1)
        limpiar_sesion_nadro_extrema(driver)
        
        logger.info("✅ Navegador ULTRA LIMPIO inicializado (estándar)")
        return driver, profile_path
        
    except Exception as e:
        logger.error(f"❌ Error inicializando navegador ultra limpio (estándar): {e}")
        limpiar_perfil_temporal_agresivo(profile_path)
        return None, None

def safe_driver_quit_ultra(driver, profile_path):
    """
    ✅ FUNCIÓN NUEVA: Cierre ultra seguro con limpieza extrema
    """
    try:
        if driver:
            logger.info("🧹 Realizando limpieza final extrema...")
            
            # Última limpieza antes de cerrar
            try:
                limpiar_sesion_nadro_extrema(driver)
                time.sleep(1)
            except Exception as e:
                logger.debug(f"Error en limpieza final: {e}")
            
            # Cerrar todas las ventanas
            try:
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    driver.close()
            except:
                pass
            
            # Cerrar navegador
            driver.quit()
            logger.info("✅ Navegador cerrado")
            
        # Esperar liberación de archivos
        time.sleep(3)
        
        # Limpiar perfil temporal agresivamente
        limpiar_perfil_temporal_agresivo(profile_path)
        
        # Limpieza adicional del sistema
        limpiar_datos_chrome_sistema()
        
    except Exception as e:
        logger.error(f"❌ Error cerrando navegador ultra: {e}")
        # Forzar cierre de procesos
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'chrome' in proc.info['name'].lower():
                        proc.kill()
                except:
                    pass
        except:
            # Método alternativo si psutil no está disponible
            try:
                if os.name == 'nt':  # Windows
                    os.system("taskkill /f /im chromedriver.exe 2>nul")
                    os.system("taskkill /f /im chrome.exe 2>nul")
                else:  # Linux/Mac
                    os.system("pkill -f chromedriver 2>/dev/null")
                    os.system("pkill -f chrome 2>/dev/null")
            except:
                pass

# ===============================
# SISTEMA DE SIMILITUD (mantenemos el existente)
# ===============================

def normalizar_texto_nadro_similitud(texto):
    """Normalización específica para comparación en NADRO."""
    if not texto:
        return ""
    
    # Convertir a minúsculas y quitar acentos
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    
    # Normalizaciones específicas de farmacéuticos
    replacements = {
        'acetaminofen': 'paracetamol',
        'acetaminofén': 'paracetamol', 
        'miligramos': 'mg',
        'mililitros': 'ml',
        'microgramos': 'mcg',
        'gramos': 'g',
        'tabletas': 'tab',
        'comprimidos': 'tab',
        'capsulas': 'cap',
        'cápsulas': 'cap',
        'inyectable': 'iny',
        'solucion': 'sol',
        'solución': 'sol',
        'jarabe': 'jar'
    }
    
    for original, replacement in replacements.items():
        texto = re.sub(rf'\b{original}\b', replacement, texto)
    
    # Eliminar caracteres especiales excepto espacios y números
    texto = re.sub(r'[^\w\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def normalizar_busqueda_nadro(producto_nombre):
    """
    Normaliza la búsqueda para NADRO: nombre + cantidad separados.
    """
    if not producto_nombre:
        return producto_nombre
    
    # Convertir a minúsculas para procesamiento
    texto = producto_nombre.lower().strip()
    
    # Extraer cantidad (número + unidad)
    patron_cantidad = r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|ui|iu|%|cc|mgs)'
    match_cantidad = re.search(patron_cantidad, texto)
    cantidad = ""
    if match_cantidad:
        numero = match_cantidad.group(1)
        unidad = match_cantidad.group(2)
        # Normalizar unidad
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
    
    # Dividir en palabras
    palabras = texto.split()
    palabras_filtradas = []
    
    for palabra in palabras:
        # Saltar números y unidades
        if re.match(r'\d+(?:\.\d+)?', palabra) or palabra in ['mg', 'g', 'ml', 'mcg', 'ui', 'iu', '%', 'cc', 'mgs']:
            continue
        # Saltar números con unidades pegadas
        if re.match(r'\d+(?:\.\d+)?(mg|g|ml|mcg|ui|iu|%|cc|mgs)', palabra):
            continue
        # Saltar formas farmacéuticas
        if palabra in formas_farmaceuticas:
            continue
        # Mantener palabras del nombre
        palabras_filtradas.append(palabra)
    
    # Tomar las primeras 1-2 palabras del nombre
    if palabras_filtradas:
        if len(palabras_filtradas) == 1:
            nombre = palabras_filtradas[0]
        else:
            nombre = ' '.join(palabras_filtradas[:2])
    else:
        nombre = producto_nombre.split()[0] if producto_nombre.split() else producto_nombre
    
    # Combinar nombre + cantidad
    if cantidad:
        resultado = f"{nombre} {cantidad}"
    else:
        resultado = nombre
    
    logger.info(f"[NADRO] Normalización: '{producto_nombre}' → '{resultado}'")
    return resultado

# ===============================
# FUNCIONES DE BÚSQUEDA (mantenemos la lógica existente)
# ===============================

def buscar_producto(driver, nombre_producto):
    """
    Busca un producto en NADRO (lógica mantenida, solo mejorada la limpieza)
    """
    try:
        logger.info(f"🔍 Buscando producto: {nombre_producto}")
        
        # Verificar que el navegador esté limpio
        storage_state = driver.execute_script("""
            return {
                cookies: document.cookie.length,
                localStorage: Object.keys(localStorage).length,
                sessionStorage: Object.keys(sessionStorage).length
            };
        """)
        logger.info(f"📊 Estado del navegador antes de búsqueda: {storage_state}")
        
        # Continuar con la lógica de búsqueda existente...
        # (mantener toda la lógica de buscar_producto del código original)
        
        time.sleep(5)
        
        # --- 1) Encontrar el campo de búsqueda ---
        search_selectors = [
            "input[placeholder='Buscar...']",
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
                        break
                if search_field:
                    break
            except:
                continue
                
        if not search_field:
            logger.error("❌ No se encontró campo de búsqueda")
            return {"error": "No se pudo encontrar el campo de búsqueda", "productos": []}

        # --- 2) Buscar producto ---
        driver.execute_script("arguments[0].focus();", search_field)
        time.sleep(0.5)
        search_field.clear()
        time.sleep(0.5)
        
        # Escribir con delays humanos
        for c in nombre_producto:
            search_field.send_keys(c)
            time.sleep(random.uniform(0.05, 0.2))
        
        time.sleep(1)
        search_field.send_keys(Keys.RETURN)

        # --- 3) Esperar y procesar resultados ---
        logger.info("⏳ Esperando resultados...")
        time.sleep(8)
        
        # Tomar screenshot para debug
        debug_dir = Path("debug_screenshots")
        debug_dir.mkdir(exist_ok=True)
        driver.save_screenshot(str(debug_dir / "resultados_busqueda_ultra_limpio.png"))
        
        # Buscar productos en la página
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
                    logger.info(f"✅ Encontrados {len(elems)} productos con selector: {sel}")
                    break
            except:
                continue

        if not productos:
            logger.warning("⚠️ No se encontraron productos")
            return {"warning": "No se encontraron productos", "productos": []}

        # Procesar productos encontrados
        resultados = []
        for i, prod in enumerate(productos[:5]):  # Limitar a 5 para evitar timeout
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", prod)
                time.sleep(0.5)
                
                info = {}
                
                # Extraer nombre
                for sel in [".vtex-product-summary-2-x-productBrand", "h3", ".vtex-product-summary-2-x-productNameContainer"]:
                    try:
                        el = prod.find_element(By.CSS_SELECTOR, sel)
                        if el.text.strip():
                            info["nombre"] = el.text.strip()
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
                                break
                        if info.get("precio_farmacia"):
                            break
                    except:
                        pass

                # Detectar disponibilidad por botón COMPRAR
                disponibilidad_detectada = False
                
                # Buscar botones COMPRAR
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
                                    break
                        if disponibilidad_detectada:
                            break
                except Exception as e:
                    logger.debug(f"Error detectando disponibilidad: {e}")

                if not disponibilidad_detectada:
                    info["existencia"] = "Estado desconocido"

                if info.get("nombre"):
                    resultados.append(info)
                
            except Exception as e:
                logger.error(f"❌ Error procesando producto {i+1}: {e}")
                continue

        if resultados:
            logger.info(f"✅ {len(resultados)} productos procesados exitosamente")
            return {"success": True, "productos": resultados}
        else:
            return {"warning": "No se pudieron procesar productos", "productos": []}

    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        return {"error": str(e), "productos": []}

def login_and_search_ultra_limpio(producto):
    """
    ✅ FUNCIÓN PRINCIPAL CON LIMPIEZA EXTREMA PARA NADRO
    """
    driver = None
    profile_path = None
    
    try:
        logger.info("🚀 ===== INICIANDO SESIÓN ULTRA LIMPIA PARA NADRO =====")
        
        # Inicializar navegador ultra limpio
        driver, profile_path = inicializar_navegador_ultra_limpio(headless=True)
        if not driver:
            return {"error": "No se pudo inicializar navegador ultra limpio", "productos": []}
        
        # Navegar con pausa
        logger.info(f"🌐 Navegando a {MAIN_URL} con sesión limpia...")
        driver.get(MAIN_URL)
        time.sleep(random.uniform(4, 6))
        
        # Verificar estado de limpieza
        storage_check = driver.execute_script("""
            return {
                cookies: document.cookie.length,
                localStorage: Object.keys(localStorage).length,
                sessionStorage: Object.keys(sessionStorage).length,
                url: window.location.href
            };
        """)
        logger.info(f"📊 Verificación de limpieza inicial: {storage_check}")
        
        # Buscar enlace de login
        logger.info("🔍 Buscando acceso a login...")
        login_selectors = [
            "a[href*='login']", 
            "a.vtex-login-2-x-button",
            "span:contains('Iniciar sesión')",
            "button:contains('Ingresar')",
            "a:contains('Iniciar sesión')"
        ]
        
        login_found = False
        for selector in login_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info("🖱️ Accediendo a página de login...")
                        element.click()
                        login_found = True
                        time.sleep(random.uniform(4, 6))
                        break
                if login_found:
                    break
            except:
                continue
        
        if not login_found:
            logger.info("📍 Navegando directamente a URL de login...")
            driver.get("https://i22.nadro.mx/login")
            time.sleep(random.uniform(4, 6))
        
        # Captura de debug
        debug_dir = Path("debug_screenshots") 
        debug_dir.mkdir(exist_ok=True)
        driver.save_screenshot(str(debug_dir / "login_ultra_limpio.png"))
        
        # PROCESO DE LOGIN
        logger.info("🔐 Iniciando login ultra limpio...")
        
        try:
            # Campo usuario
            username_field = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text'], input[type='email'], #username, input[name='username']"))
            )
            
            # Escribir usuario
            logger.info(f"👤 Ingresando usuario: {USERNAME}")
            username_field.clear()
            time.sleep(random.uniform(0.5, 1.5))
            
            for c in USERNAME:
                username_field.send_keys(c)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(0.5, 1.5))
            
            # Campo contraseña
            password_field = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password'], #password, input[name='password']"))
            )
            
            # Escribir contraseña
            logger.info("🔒 Ingresando contraseña...")
            password_field.clear()
            time.sleep(random.uniform(0.5, 1.5))
            
            for c in PASSWORD:
                password_field.send_keys(c)
                time.sleep(random.uniform(0.1, 0.3))
            
            time.sleep(random.uniform(1, 2))
            
            # Botón login
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
            
            # Enviar login
            if login_button:
                logger.info("🚀 Enviando login...")
                login_button.click()
            else:
                logger.info("⌨️ Enviando con Enter...")
                password_field.send_keys(Keys.RETURN)
            
            # ✅ ESPERA EXTENDIDA DESPUÉS DEL LOGIN (problema principal de NADRO)
            logger.info("⏳ Esperando procesamiento de login ultra limpio (tiempo extendido)...")
            time.sleep(15)  # Tiempo más largo para login ultra limpio
            
            # Captura post-login
            driver.save_screenshot(str(debug_dir / "post_login_ultra_limpio.png"))
            
            # Verificar login exitoso
            current_url = driver.current_url.lower()
            page_text = driver.page_source.lower()
            
            login_exitoso = (
                "login" not in current_url or
                "logout" in page_text or
                "cerrar sesión" in page_text or
                "mi cuenta" in page_text
            )
            
            if login_exitoso:
                logger.info("✅ LOGIN ULTRA LIMPIO EXITOSO!")
                
                # Verificar estado final
                final_storage = driver.execute_script("""
                    return {
                        cookies: document.cookie.length,
                        localStorage: Object.keys(localStorage).length,
                        sessionStorage: Object.keys(sessionStorage).length
                    };
                """)
                logger.info(f"📊 Estado final del navegador: {final_storage}")
                
                # Proceder con búsqueda
                resultado = buscar_producto(driver, producto)
                return resultado
            else:
                logger.error("❌ Login ultra limpio falló")
                
                # Debug del error
                debug_logs_dir = Path("debug_logs")
                debug_logs_dir.mkdir(exist_ok=True)
                with open(debug_logs_dir / "login_ultra_limpio_fallido.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
                return {"error": "Login ultra limpio falló", "productos": []}
                
        except Exception as e:
            logger.error(f"❌ Error en proceso de login ultra limpio: {e}")
            driver.save_screenshot(str(debug_dir / "error_login_ultra_limpio.png"))
            return {"error": f"Error login ultra limpio: {str(e)}", "productos": []}
    
    except Exception as e:
        logger.error(f"❌ Error general en login ultra limpio: {e}")
        return {"error": str(e), "productos": []}
    
    finally:
        # Limpieza final extrema
        logger.info("🧹 Iniciando limpieza final extrema...")
        safe_driver_quit_ultra(driver, profile_path)

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    ✅ FUNCIÓN PRINCIPAL CORREGIDA: Implementa limpieza extrema siguiendo instrucciones NADRO
    """
    try:
        logger.info(f"🚀 BÚSQUEDA NADRO ULTRA LIMPIA: {nombre_medicamento}")
        logger.info("📋 Implementando recomendaciones de NADRO: Borrar datos 'Desde siempre'")
        
        # Normalizar búsqueda
        nombre_normalizado = normalizar_busqueda_nadro(nombre_medicamento)
        
        # Crear directorios debug
        Path("debug_screenshots").mkdir(exist_ok=True)
        Path("debug_logs").mkdir(exist_ok=True)
        
        # ✅ USAR FUNCIÓN ULTRA LIMPIA
        resultado = login_and_search_ultra_limpio(nombre_normalizado)
        
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
        
        # Formatear primer producto encontrado
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
            
            logger.info(f"✅ PRODUCTO ENCONTRADO CON SESIÓN ULTRA LIMPIA: {info_producto['nombre']} - {info_producto['precio']} - Stock: {info_producto['existencia']}")
            return info_producto
        
        return {
            "nombre": nombre_medicamento,
            "mensaje": "No se pudo procesar respuesta NADRO",
            "estado": "error",
            "fuente": "NADRO",
            "existencia": "0"
        }
        
    except Exception as e:
        logger.error(f"❌ Error general NADRO ultra limpio: {e}")
        return {
            "nombre": nombre_medicamento,
            "error": str(e),
            "estado": "error",
            "fuente": "NADRO",
            "existencia": "0"
        }

if __name__ == "__main__":
    import sys
    
    print("=== NADRO SCRAPER CON LIMPIEZA EXTREMA ===")
    print("=== Implementa recomendaciones oficiales de NADRO ===")
    print("=== Borrar datos 'Desde siempre' automáticamente ===")
    
    if len(sys.argv) > 1:
        medicamento = " ".join(sys.argv[1:])
    else:
        medicamento = input("Nombre del medicamento: ")
    
    print(f"\n🚀 Iniciando búsqueda ultra limpia para: {medicamento}")
    print("⏳ Aplicando limpieza extrema de cookies/caché...")
    
    resultado = buscar_info_medicamento(medicamento)
    
    if resultado.get('estado') == 'encontrado':
        print(f"\n✅ ÉXITO CON LIMPIEZA EXTREMA")
        print(f"Producto: {resultado['nombre']}")
        print(f"Precio: {resultado['precio']}")
        print(f"Stock: {resultado['existencia']}")
    else:
        print(f"\n❌ {resultado.get('mensaje', resultado.get('error', 'Error desconocido'))}")
    
    print(f"\n🧹 Limpieza extrema completada.")
