"""
Servicio de scraping integrado para buscar información de productos farmacéuticos.
Este servicio orquesta los scrapers de Difarmer, Sufarmed, FANASA y NADRO de forma secuencial,
comparando resultados y seleccionando opciones según disponibilidad y precio.

MODIFICADO: Ahora incluye productos SIN existencia para mostrar precios aunque estén agotados.
CORREGIDO: Filtros en formateadores para evitar procesar "no encontrado" como productos válidos.
NUEVO: Timeout robusto para Sufarmed (60s scraping, 45s login) para evitar cuelgues.
"""
import logging
import os
import sys
import time
import re
import concurrent.futures
import psutil
import subprocess
import platform
import asyncio
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingService:
    """
    Clase que coordina la búsqueda de productos en múltiples fuentes,
    comparando resultados y seleccionando las mejores opciones.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de scraping integrado configurando cada scraper individual.
        """
        logger.info("Inicializando ScrapingService integrado con múltiples scrapers (modo paralelo + timeouts)")
        
        # Verificar qué servicios están disponibles
        self.difarmer_available = self._check_difarmer_available()
        self.sufarmed_available = self._check_sufarmed_available()
        self.fanasa_available = self._check_fanasa_available()
        self.nadro_available = self._check_nadro_available()
        
        # ✅ NUEVO: Configuración de timeouts
        self.SUFARMED_TIMEOUT = 60  # 60 segundos para todo el proceso de Sufarmed
        self.DIFARMER_TIMEOUT = 180  # 3 minutos para Difarmer
        self.FANASA_TIMEOUT = 180   # 3 minutos para FANASA
        self.NADRO_TIMEOUT = 180    # 3 minutos para NADRO
        
        # Inicializar scrapers solo si están disponibles
        if self.difarmer_available:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                    logger.info(f"Directorio añadido al path: {parent_dir}")
                
                from services.scraper_difarmer import buscar_info_medicamento as buscar_difarmer
                self.buscar_difarmer = buscar_difarmer
                logger.info("Scraper Difarmer inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_difarmer: {e}")
                self.difarmer_available = False
                try:
                    scraper_path = os.path.join('services', 'scraper_difarmer')
                    sys.path.insert(0, scraper_path)
                    from main import buscar_info_medicamento
                    self.buscar_difarmer = buscar_info_medicamento
                    self.difarmer_available = True
                    logger.info("Scraper Difarmer inicializado mediante ruta alternativa")
                except ImportError as e2:
                    logger.error(f"Error en importación alternativa de Difarmer: {e2}")
        
        if self.sufarmed_available:
            try:
                from services.scraping_service_sufarmed import ScrapingService as SufarmedService
                self.sufarmed_service = SufarmedService()
                logger.info("Scraper Sufarmed inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraping_service_sufarmed: {e}")
                try:
                    if os.path.exists(os.path.join('services', 'sufarmed_service.py')):
                        from services.sufarmed_service import ScrapingService as SufarmedService
                        self.sufarmed_service = SufarmedService()
                        self.sufarmed_available = True
                        logger.info("Scraper Sufarmed inicializado desde ruta alternativa")
                except ImportError:
                    self.sufarmed_available = False
        
        if self.fanasa_available:
            try:
                from services.scraper_fanasa import buscar_info_medicamento as buscar_fanasa
                self.buscar_fanasa = buscar_fanasa
                logger.info("Scraper FANASA inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_fanasa: {e}")
                self.fanasa_available = False
                try:
                    scraper_path = os.path.join('services', 'scraper_fanasa')
                    sys.path.insert(0, scraper_path)
                    from main import buscar_info_medicamento
                    self.buscar_fanasa = buscar_info_medicamento
                    self.fanasa_available = True
                    logger.info("Scraper FANASA inicializado mediante ruta alternativa")
                except ImportError as e2:
                    logger.error(f"Error en importación alternativa de FANASA: {e2}")

        if self.nadro_available:
            try:
                from services.scraper_nadro import buscar_info_medicamento as buscar_nadro
                self.buscar_nadro = buscar_nadro
                logger.info("Scraper NADRO inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_nadro: {e}")
                self.nadro_available = False
                try:
                    scraper_path = os.path.join('services', 'scraper_nadro')
                    sys.path.insert(0, scraper_path)
                    from main import buscar_info_medicamento
                    self.buscar_nadro = buscar_info_medicamento
                    self.nadro_available = True
                    logger.info("Scraper NADRO inicializado mediante ruta alternativa")
                except ImportError as e2:
                    logger.error(f"Error en importación alternativa de NADRO: {e2}")
        
        # Verificar que al menos un scraper esté disponible
        if not (self.difarmer_available or self.sufarmed_available or self.fanasa_available or self.nadro_available):
            logger.critical("ALERTA: Ningún scraper está disponible. La funcionalidad estará limitada.")
        else:
            servicios_activos = []
            if self.difarmer_available:
                servicios_activos.append("Difarmer")
            if self.sufarmed_available:
                servicios_activos.append("Sufarmed")
            if self.fanasa_available:
                servicios_activos.append("FANASA")
            if self.nadro_available:
                servicios_activos.append("NADRO")
            logger.info(f"Scrapers activos: {', '.join(servicios_activos)}")
    
    def _check_difarmer_available(self):
        """Verifica si el scraper de Difarmer está disponible"""
        try:
            scraper_path = os.path.join('services', 'scraper_difarmer')
            if not os.path.isdir(scraper_path):
                logger.warning(f"Directorio {scraper_path} no encontrado")
                return False
            
            required_files = ['__init__.py', 'main.py', 'login.py']
            for file in required_files:
                if not os.path.exists(os.path.join(scraper_path, file)):
                    logger.warning(f"Archivo {file} no encontrado en {scraper_path}")
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Error al verificar disponibilidad de Difarmer: {e}")
            return False
    
    def _check_sufarmed_available(self):
        """Verifica si el scraper de Sufarmed está disponible"""
        try:
            sufarmed_file = os.path.join('services', 'scraping_service_sufarmed.py')
            if os.path.exists(sufarmed_file):
                return True
            
            alt_file = os.path.join('services', 'sufarmed_service.py')
            if os.path.exists(alt_file):
                return True
            
            logger.warning("Archivos de Sufarmed no encontrados")
            return False
        except Exception as e:
            logger.warning(f"Error al verificar disponibilidad de Sufarmed: {e}")
            return False
    
    def _check_fanasa_available(self):
        """Verifica si el scraper de FANASA está disponible"""
        try:
            scraper_path = os.path.join('services', 'scraper_fanasa')
            if not os.path.isdir(scraper_path):
                logger.warning(f"Directorio {scraper_path} no encontrado")
                return False
            
            required_files = ['__init__.py', 'main.py']
            for file in required_files:
                if not os.path.exists(os.path.join(scraper_path, file)):
                    logger.warning(f"Archivo {file} no encontrado en {scraper_path}")
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Error al verificar disponibilidad de FANASA: {e}")
            return False

    def _check_nadro_available(self):
        """Verifica si el scraper de NADRO está disponible"""
        try:
            scraper_path = os.path.join('services', 'scraper_nadro')
            if not os.path.isdir(scraper_path):
                logger.warning(f"Directorio {scraper_path} no encontrado")
                return False
            
            required_files = ['__init__.py', 'main.py']
            for file in required_files:
                if not os.path.exists(os.path.join(scraper_path, file)):
                    logger.warning(f"Archivo {file} no encontrado en {scraper_path}")
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Error al verificar disponibilidad de NADRO: {e}")
            return False
    
    def _cleanup_chrome_processes(self):
        """
        Limpia procesos Chrome y chromedriver que puedan haber quedado colgados.
        """
        logger.info("🧹 Iniciando limpieza de procesos Chrome...")
        
        cleaned_processes = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    process_name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                    
                    should_kill = False
                    
                    if any(name in process_name for name in ['chrome', 'chromium']):
                        if any(keyword in cmdline for keyword in ['headless', 'remote-debugging-port', 'disable-gpu']):
                            should_kill = True
                            
                    elif 'chromedriver' in process_name:
                        should_kill = True
                    
                    if should_kill:
                        logger.info(f"🔪 Matando proceso: PID {proc.info['pid']} - {process_name}")
                        proc.kill()
                        proc.wait(timeout=3)
                        cleaned_processes += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
                except Exception as e:
                    logger.warning(f"⚠️ Error al procesar PID {proc.info.get('pid', 'unknown')}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error durante limpieza de procesos: {e}")
        
        logger.info(f"✅ Limpieza completada. Procesos eliminados: {cleaned_processes}")

    def _cleanup_network_connections(self):
        """
        Intenta liberar conexiones de red que puedan estar ocupadas.
        """
        logger.info("🌐 Limpiando conexiones de red...")
        
        try:
            common_ports = [4343, 9222, 9223, 9224, 9225]
            
            for port in common_ports:
                try:
                    connections = psutil.net_connections()
                    for conn in connections:
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            try:
                                proc = psutil.Process(conn.pid)
                                if any(name in proc.name().lower() for name in ['chrome', 'chromedriver']):
                                    logger.info(f"🔌 Liberando puerto {port} usado por PID {conn.pid}")
                                    proc.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                except Exception as e:
                    logger.warning(f"⚠️ Error limpiando puerto {port}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error durante limpieza de red: {e}")
        
        logger.info("✅ Limpieza de red completada")

    def _force_cleanup_chrome(self):
        """
        Cleanup agresivo usando comandos del sistema como último recurso.
        """
        logger.info("💪 Ejecutando limpieza agresiva de Chrome...")
        
        try:
            system = platform.system().lower()
            
            if system == "linux":
                commands = [
                    "pkill -f chrome",
                    "pkill -f chromedriver", 
                    "pkill -f 'google-chrome'",
                    "pkill -f 'chromium'"
                ]
            elif system == "windows":
                commands = [
                    "taskkill /f /im chrome.exe",
                    "taskkill /f /im chromedriver.exe",
                    "taskkill /f /im googlechrome.exe"
                ]
            elif system == "darwin":  # macOS
                commands = [
                    "pkill -f chrome",
                    "pkill -f chromedriver"
                ]
            else:
                logger.warning(f"Sistema operativo no reconocido: {system}")
                return
            
            for cmd in commands:
                try:
                    subprocess.run(cmd.split(), capture_output=True, timeout=5)
                    logger.info(f"🔨 Ejecutado: {cmd}")
                except subprocess.TimeoutExpired:
                    logger.warning(f"⏰ Timeout ejecutando: {cmd}")
                except Exception as e:
                    logger.warning(f"⚠️ Error ejecutando '{cmd}': {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error en limpieza agresiva: {e}")
        
        logger.info("✅ Limpieza agresiva completada")

    def _full_cleanup_after_phase1(self):
        """
        Limpieza completa después de FASE 1 para liberar todos los recursos.
        """
        logger.info("🧽 ===== INICIANDO LIMPIEZA COMPLETA POST-FASE 1 =====")
        
        self._cleanup_chrome_processes()
        time.sleep(2)
        self._cleanup_network_connections()
        time.sleep(1)
        self._force_cleanup_chrome()
        time.sleep(3)
        
        logger.info("✨ ===== LIMPIEZA COMPLETA FINALIZADA =====")
    
    def _extract_numeric_price(self, price_str):
        """
        Extrae un valor numérico del precio para comparación.
        Modificado para tratar los precios de cero como valores muy altos (baja prioridad).
        """
        if not price_str:
            return 9999999.0
        
        clean_price = str(price_str).replace('$', '').replace(' ', '')
        
        if ',' in clean_price and '.' not in clean_price:
            clean_price = clean_price.replace(',', '.')
        elif ',' in clean_price and '.' in clean_price:
            clean_price = clean_price.replace(',', '')
        
        match = re.search(r'(\d+(\.\d+)?)', clean_price)
        
        if match:
            price_value = float(match.group(1))
            if price_value == 0:
                return 9999999.0
            return price_value
        else:
            return 9999999.0
    
    def _extract_numeric_existencia(self, existencia_str):
        """
        Extrae un valor numérico de existencia para comparación.
        """
        if not existencia_str:
            return 0
        
        valores_disponible = ["si", "sí", "disponible", "en stock", "hay"]
        
        if str(existencia_str).lower() in valores_disponible:
            return 1
        
        clean_existencia = str(existencia_str).replace(',', '').replace(' ', '')
        
        match = re.search(r'(\d+)', clean_existencia)
        
        if match:
            return int(match.group(1))
        
        for palabra in valores_disponible:
            if palabra in str(existencia_str).lower():
                return 1
        
        return 0
    
    def _format_producto_difarmer(self, producto):
        """
        Formatea los datos del producto de Difarmer al formato estandarizado.
        """
        if not producto:
            return None
        
        estado = producto.get('estado')
        if estado in ['no_encontrado', 'error']:
            logger.info(f"🚫 DIFARMER: Producto con estado '{estado}' - no se formateará como producto válido")
            return None
        
        if producto.get('error') or (producto.get('nombre', '').startswith('Error:') if producto.get('nombre') else False):
            logger.info(f"🚫 DIFARMER: Producto con error - no se formateará como producto válido")
            return None

        precio = producto.get('mi_precio') or producto.get('precio_publico') or "0"
        
        return {
            "nombre": producto.get('nombre', ''),
            "laboratorio": producto.get('laboratorio', ''),
            "codigo_barras": producto.get('codigo_barras', ''),
            "registro_sanitario": producto.get('registro_sanitario', ''),
            "url": producto.get('url', ''),
            "imagen": producto.get('imagen', ''),
            "precio": precio,
            "existencia": producto.get('existencia', '0'),
            "precio_numerico": self._extract_numeric_price(precio),
            "existencia_numerica": self._extract_numeric_existencia(producto.get('existencia', '0')),
            "fuente": "Difarmer",
            "nombre_farmacia": "Difarmer"
        }
    
    def _format_producto_sufarmed(self, producto):
        """
        Formatea los datos del producto de Sufarmed al formato estandarizado.
        """
        if not producto:
            return None
        
        estado = producto.get('estado')
        if estado in ['no_encontrado', 'error']:
            logger.info(f"🚫 SUFARMED: Producto con estado '{estado}' - no se formateará como producto válido")
            return None

        precio = producto.get('precio', "0")
        existencia = producto.get('existencia', '0')
        
        existencia_numerica = 0
        
        if producto.get('disponible', False) or producto.get('stock', '').lower() in ['disponible', 'en stock']:
            existencia_numerica = 1
        else:
            existencia_numerica = self._extract_numeric_existencia(existencia)
        
        return {
            "nombre": producto.get('nombre', ''),
            "laboratorio": producto.get('laboratorio', ''),
            "codigo_barras": producto.get('codigo_barras', ''),
            "registro_sanitario": producto.get('registro_sanitario', ''),
            "url": producto.get('url', ''),
            "imagen": producto.get('imagen', ''),
            "precio": precio,
            "existencia": existencia,
            "precio_numerico": self._extract_numeric_price(precio),
            "existencia_numerica": existencia_numerica,
            "fuente": "Sufarmed",
            "nombre_farmacia": "Sufarmed"
        }
    
    def _format_producto_fanasa(self, producto):
        """
        Formatea los datos del producto de FANASA al formato estandarizado.
        """
        if not producto:
            return None
        
        estado = producto.get('estado')
        if estado in ['no_encontrado', 'error', 'error_extraccion', 'error_navegador']:
            logger.info(f"🚫 FANASA: Producto con estado '{estado}' - no se formateará como producto válido")
            return None
        
        if producto.get('mensaje') and 'no se encontró' in producto.get('mensaje', '').lower():
            logger.info(f"🚫 FANASA: Producto con mensaje 'no encontrado' - no se formateará como producto válido")
            return None
        
        if not producto.get('nombre') and not producto.get('codigo') and not producto.get('sku'):
            logger.info(f"🚫 FANASA: Producto sin datos básicos - no se formateará como producto válido")
            return None
        
        precio = producto.get('precio_neto') or producto.get('precio_publico') or producto.get('precio_farmacia') or producto.get('pmp') or "0"
        
        existencia_numerica = 0
        if producto.get('disponibilidad'):
            stock_match = re.search(r'(\d+)', producto.get('disponibilidad', '0'))
            if stock_match:
                existencia_numerica = int(stock_match.group(1))
            elif "disponible" in producto.get('disponibilidad', '').lower():
                existencia_numerica = 1
        
        return {
            "nombre": producto.get('nombre', ''),
            "laboratorio": producto.get('laboratorio', ''),
            "codigo_barras": producto.get('codigo_barras', '') or producto.get('codigo', '') or producto.get('sku', ''),
            "registro_sanitario": producto.get('registro_sanitario', ''),
            "url": producto.get('url', ''),
            "imagen": producto.get('imagen', ''),
            "precio": precio,
            "existencia": producto.get('existencia', '0') or producto.get('disponibilidad', '0'),
            "precio_numerico": self._extract_numeric_price(precio),
            "existencia_numerica": existencia_numerica,
            "fuente": "FANASA",
            "nombre_farmacia": "FANASA"
        }

    def _format_producto_nadro(self, producto):
        """
        Formatea los datos del producto de NADRO al formato estandarizado.
        """
        if not producto:
            return None

        estado = producto.get('estado')
        if estado in ['no_encontrado', 'error', 'error_extraccion']:
            logger.info(f"🚫 NADRO: Producto con estado '{estado}' - no se formateará como producto válido")
            return None
        
        if producto.get('error') or producto.get('mensaje'):
            mensaje = producto.get('mensaje', '')
            if 'no se encontró' in mensaje.lower() or 'no encontrado' in mensaje.lower():
                logger.info(f"🚫 NADRO: Producto con mensaje 'no encontrado' - no se formateará como producto válido")
                return None
        
        if not producto.get('nombre') and not producto.get('codigo_barras'):
            logger.info(f"🚫 NADRO: Producto sin datos básicos - no se formateará como producto válido")
            return None

        precio = producto.get('precio') or producto.get('precio_farmacia') or producto.get('precio_publico') or "0"

        existencia_numerica = 0
        existencia_raw = producto.get('existencia', '')
        texto_existencia = str(existencia_raw).lower()
        indicadores_disponibilidad = ["disponible", "entrega mañana", "sí", "si", "stock"]

        stock_match = re.search(r'(\d+)', texto_existencia)
        if stock_match:
            existencia_numerica = int(stock_match.group(1))
        elif any(ind in texto_existencia for ind in indicadores_disponibilidad):
            existencia_numerica = 1

        return {
            "nombre": producto.get('nombre', ''),
            "laboratorio": producto.get('laboratorio', ''),
            "codigo_barras": producto.get('codigo_barras', ''),
            "registro_sanitario": producto.get('registro_sanitario', ''),
            "url": producto.get('url', ''),
            "imagen": producto.get('imagen', ''),
            "precio": precio,
            "existencia": existencia_raw,
            "precio_numerico": self._extract_numeric_price(precio),
            "existencia_numerica": existencia_numerica,
            "fuente": "NADRO",
            "nombre_farmacia": "NADRO"
        }
    
    def buscar_producto_difarmer(self, nombre_producto):
        """
        Busca un producto en Difarmer y formatea el resultado.
        ACTUALIZADO: Con timeout robusto.
        """
        if not self.difarmer_available:
            logger.warning("Scraper Difarmer no disponible. No se realizará búsqueda.")
            return None
        
        def _buscar_difarmer_sync():
            """Función síncrona para buscar en Difarmer"""
            headless = True
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            return self.buscar_difarmer(nombre_producto, headless=headless)
        
        try:
            logger.info(f"Buscando producto en Difarmer: {nombre_producto}")
            
            # ✅ NUEVO: Timeout para Difarmer
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                try:
                    future = executor.submit(_buscar_difarmer_sync)
                    info_producto = future.result(timeout=self.DIFARMER_TIMEOUT)
                    
                    logger.info("✅ Difarmer completado dentro del timeout")
                    
                except concurrent.futures.TimeoutError:
                    logger.error(f"⏰ TIMEOUT: Difarmer tardó más de {self.DIFARMER_TIMEOUT} segundos")
                    logger.error("🔄 Continuando con otros scrapers...")
                    future.cancel()
                    return None
                except Exception as e:
                    logger.error(f"❌ Error en Difarmer: {e}")
                    return None
            
            if info_producto:
                resultado = self._format_producto_difarmer(info_producto)
                if resultado:
                    logger.info(f"Producto encontrado en Difarmer: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                    return resultado
                else:
                    logger.info(f"Producto de Difarmer descartado por el formateador (estado no válido)")
                    return None
            else:
                logger.warning(f"No se encontró información en Difarmer para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error general al buscar producto en Difarmer: {e}")
            return None
    
    def buscar_producto_sufarmed(self, nombre_producto):
        """
        Busca un producto en Sufarmed y formatea el resultado.
        ✅ CORREGIDO: Con timeout robusto para evitar que se cuelgue el login.
        """
        if not self.sufarmed_available:
            logger.warning("Scraper Sufarmed no disponible. No se realizará búsqueda.")
            return None
        
        def _buscar_sufarmed_sync():
            """Función síncrona para buscar en Sufarmed"""
            return self.sufarmed_service.buscar_producto(nombre_producto)
        
        try:
            logger.info(f"Buscando producto en Sufarmed: {nombre_producto}")
            
            # ✅ NUEVO: Timeout específico para Sufarmed (60 segundos)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                try:
                    future = executor.submit(_buscar_sufarmed_sync)
                    info_producto = future.result(timeout=self.SUFARMED_TIMEOUT)
                    
                    logger.info("✅ Sufarmed completado dentro del timeout")
                    
                except concurrent.futures.TimeoutError:
                    logger.error(f"⏰ TIMEOUT: Sufarmed tardó más de {self.SUFARMED_TIMEOUT} segundos (probablemente login colgado)")
                    logger.error("🔄 Continuando con otros scrapers...")
                    
                    # Intentar cancelar el future si es posible
                    future.cancel()
                    
                    return None
                except Exception as e:
                    logger.error(f"❌ Error en Sufarmed: {e}")
                    return None
            
            # Formatear el producto al estándar común
            if info_producto:
                resultado = self._format_producto_sufarmed(info_producto)
                if resultado:
                    logger.info(f"Producto encontrado en Sufarmed: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']} (Valor numérico: {resultado['existencia_numerica']})")
                    return resultado
                else:
                    logger.info(f"Producto de Sufarmed descartado por el formateador (estado no válido)")
                    return None
            else:
                logger.warning(f"No se encontró información en Sufarmed para: {nombre_producto}")
                return None
                
        except Exception as e:
            logger.error(f"Error general al buscar producto en Sufarmed: {e}")
            logger.error("🔄 Continuando con otros scrapers...")
            return None
    
    def buscar_producto_fanasa(self, nombre_producto):
        """
        Busca un producto en FANASA y formatea el resultado.
        ACTUALIZADO: Con timeout robusto.
        """
        if not self.fanasa_available:
            logger.warning("Scraper FANASA no disponible. No se realizará búsqueda.")
            return None
        
        def _buscar_fanasa_sync():
            """Función síncrona para buscar en FANASA"""
            headless = True
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            return self.buscar_fanasa(nombre_producto, headless=headless)
        
        try:
            logger.info(f"Buscando producto en FANASA: {nombre_producto}")
            
            # ✅ NUEVO: Timeout para FANASA
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                try:
                    future = executor.submit(_buscar_fanasa_sync)
                    info_producto = future.result(timeout=self.FANASA_TIMEOUT)
                    
                    logger.info("✅ FANASA completado dentro del timeout")
                    
                except concurrent.futures.TimeoutError:
                    logger.error(f"⏰ TIMEOUT: FANASA tardó más de {self.FANASA_TIMEOUT} segundos")
                    logger.error("🔄 Continuando con otros scrapers...")
                    future.cancel()
                    return None
                except Exception as e:
                    logger.error(f"❌ Error en FANASA: {e}")
                    return None
            
            if info_producto:
                resultado = self._format_producto_fanasa(info_producto)
                if resultado:
                    logger.info(f"Producto encontrado en FANASA: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                    return resultado
                else:
                    logger.info(f"Producto de FANASA descartado por el formateador (estado no válido)")
                    return None
            else:
                logger.warning(f"No se encontró información en FANASA para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error general al buscar producto en FANASA: {e}")
            return None

    def buscar_producto_nadro(self, nombre_producto):
        """
        Busca un producto en NADRO y formatea el resultado.
        ACTUALIZADO: Con timeout robusto.
        """
        if not self.nadro_available:
            logger.warning("Scraper NADRO no disponible. No se realizará búsqueda.")
            return None
        
        def _buscar_nadro_sync():
            """Función síncrona para buscar en NADRO"""
            headless = True
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            return self.buscar_nadro(nombre_producto, headless=headless)
        
        try:
            logger.info(f"Buscando producto en NADRO: {nombre_producto}")
            
            # ✅ NUEVO: Timeout para NADRO
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                try:
                    future = executor.submit(_buscar_nadro_sync)
                    info_producto = future.result(timeout=self.NADRO_TIMEOUT)
                    
                    logger.info("✅ NADRO completado dentro del timeout")
                    
                except concurrent.futures.TimeoutError:
                    logger.error(f"⏰ TIMEOUT: NADRO tardó más de {self.NADRO_TIMEOUT} segundos")
                    logger.error("🔄 Continuando con otros scrapers...")
                    future.cancel()
                    return None
                except Exception as e:
                    logger.error(f"❌ Error en NADRO: {e}")
                    return None
            
            if info_producto:
                resultado = self._format_producto_nadro(info_producto)
                if resultado:
                    logger.info(f"Producto encontrado en NADRO: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                    return resultado
                else:
                    logger.info(f"Producto de NADRO descartado por el formateador (estado no válido)")
                    return None
            else:
                logger.warning(f"No se encontró información en NADRO para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error general al buscar producto en NADRO: {e}")
            return None
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto en todas las fuentes disponibles,
        compara resultados y selecciona opciones según la nueva lógica de negocio.
        
        ✅ ACTUALIZADO: FASE 1 en paralelo + CLEANUP completo de recursos + TIMEOUTS ROBUSTOS
        """
        logger.info(f"Iniciando búsqueda con FASE 1 EN PARALELO + TIMEOUTS para: {nombre_producto}")
        
        resultados = []
        
        # ✅ FASE 1: Difarmer y Sufarmed EN PARALELO CON TIMEOUTS
        fase1_scrapers = []
        if self.difarmer_available:
            fase1_scrapers.append(('difarmer', self.buscar_producto_difarmer))
        if self.sufarmed_available:
            fase1_scrapers.append(('sufarmed', self.buscar_producto_sufarmed))
        
        if fase1_scrapers:
            logger.info(f"🚀 FASE 1: Ejecutando scrapers EN PARALELO CON TIMEOUTS: {', '.join([x[0] for x in fase1_scrapers])}")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(fase1_scrapers)) as executor:
                future_to_scraper = {}
                for source_name, search_func in fase1_scrapers:
                    logger.info(f"🔄 Iniciando {source_name} en paralelo...")
                    future = executor.submit(search_func, nombre_producto)
                    future_to_scraper[future] = source_name
                
                for future in concurrent.futures.as_completed(future_to_scraper):
                    source_name = future_to_scraper[future]
                    try:
                        # ✅ TIMEOUT YA MANEJADO DENTRO DE CADA FUNCIÓN INDIVIDUAL
                        resultado = future.result()  # No timeout aquí porque ya está dentro
                        
                        if resultado:
                            if resultado.get('nombre') or resultado.get('precio'):
                                logger.info(f"✅ Resultado obtenido de {source_name} (PARALELO)")
                                resultados.append(resultado)
                            else:
                                logger.warning(f"⚠️ Resultado de {source_name} descartado por falta de datos básicos")
                        else:
                            logger.info(f"❌ No se encontraron resultados en {source_name}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error en búsqueda paralela de {source_name}: {e}")
            
            logger.info(f"🏁 FASE 1 COMPLETADA - Resultados obtenidos: {len(resultados)}")
            
            # 🧹 LIMPIEZA COMPLETA DESPUÉS DE FASE 1
            self._full_cleanup_after_phase1()
        
        # Delay después del cleanup
        logger.info("⏱️ Esperando 5 segundos adicionales después del cleanup antes de FASE 2...")
        time.sleep(5)
        
        # FASE 2: NADRO (independiente) CON TIMEOUT
        if self.nadro_available:
            logger.info("FASE 2: Ejecutando scraper NADRO CON TIMEOUT")
            try:
                resultado_nadro = self.buscar_producto_nadro(nombre_producto)
                if resultado_nadro:
                    if resultado_nadro.get('nombre') or resultado_nadro.get('precio'):
                        logger.info("✅ Resultado obtenido de NADRO")
                        resultados.append(resultado_nadro)
                    else:
                        logger.warning("⚠️ Resultado de NADRO descartado por falta de datos básicos")
                else:
                    logger.info("❌ No se encontraron resultados en NADRO")
            except Exception as e:
                logger.error(f"❌ Error en búsqueda de NADRO: {e}")
        
        # Delay antes de FASE 3
        logger.info("⏱️ Esperando 5 segundos antes de iniciar FASE 3...")
        time.sleep(5)
        
        # FASE 3: FANASA (último recurso) CON TIMEOUT
        if self.fanasa_available:
            if resultados:
                logger.info("FASE 3: Ejecutando scraper FANASA CON TIMEOUT (siempre ejecutado como último recurso)")
            else:
                logger.info("FASE 3: Ejecutando scraper FANASA CON TIMEOUT como último recurso")
                
            try:
                resultado_fanasa = self.buscar_producto_fanasa(nombre_producto)
                if resultado_fanasa:
                    if resultado_fanasa.get('nombre') or resultado_fanasa.get('precio'):
                        logger.info("✅ Resultado obtenido de FANASA")
                        resultados.append(resultado_fanasa)
                    else:
                        logger.warning("⚠️ Resultado de FANASA descartado por falta de datos básicos")
                else:
                    logger.info("❌ No se encontraron resultados en FANASA")
            except Exception as e:
                logger.error(f"❌ Error en búsqueda de FANASA: {e}")
        
        # PROCESO DE COMPARACIÓN Y SELECCIÓN
        logger.info("🔍 COMENZANDO ANÁLISIS Y COMPARACIÓN DE RESULTADOS 🔍")
        
        if not resultados:
            logger.warning(f"No se encontraron resultados para: {nombre_producto}")
            return {
                "opcion_entrega_inmediata": None,
                "opcion_mejor_precio": None,
                "tiene_doble_opcion": False
            }
        
        logger.info(f"Analizando {len(resultados)} resultados encontrados:")
        for i, resultado in enumerate(resultados):
            logger.info(f"  • Resultado #{i+1}: {resultado['fuente']} - "
                       f"Nombre: {resultado['nombre']} - "
                       f"Precio: {resultado['precio']} ({resultado['precio_numerico']}) - "
                       f"Existencia: {resultado['existencia']} ({resultado['existencia_numerica']})")
        
        # Separar productos CON y SIN existencia, pero incluir ambos
        productos_con_existencia = [p for p in resultados if p['existencia_numerica'] > 0]
        productos_sin_existencia = [p for p in resultados if p['existencia_numerica'] <= 0]
        
        todos_productos_ordenados = productos_con_existencia + productos_sin_existencia
        
        logger.info(f"Productos encontrados: {len(todos_productos_ordenados)} total ({len(productos_con_existencia)} con stock, {len(productos_sin_existencia)} sin stock)")
        
        if not todos_productos_ordenados:
            logger.warning(f"No se encontraron productos para: {nombre_producto}")
            return {
                "opcion_entrega_inmediata": None,
                "opcion_mejor_precio": None,
                "tiene_doble_opcion": False
            }
        
        # BUSCAR OPCIÓN DE ENTREGA INMEDIATA (Sufarmed preferible)
        logger.info("Buscando opción de ENTREGA INMEDIATA (producto de Sufarmed, preferiblemente con stock)...")
        opcion_entrega_inmediata = None
        for producto in todos_productos_ordenados:
            if producto['fuente'] == "Sufarmed":
                opcion_entrega_inmediata = producto.copy()
                del opcion_entrega_inmediata['precio_numerico']
                del opcion_entrega_inmediata['existencia_numerica']
                
                if producto['existencia_numerica'] > 0:
                    logger.info(f"✅ Opción de entrega inmediata CON STOCK seleccionada: {opcion_entrega_inmediata['nombre']} de Sufarmed "
                               f"- Precio: {opcion_entrega_inmediata['precio']} - Existencia: {opcion_entrega_inmediata['existencia']}")
                else:
                    logger.info(f"⚠️ Opción de entrega inmediata SIN STOCK seleccionada: {opcion_entrega_inmediata['nombre']} de Sufarmed "
                               f"- Precio: {opcion_entrega_inmediata['precio']} - Existencia: {opcion_entrega_inmediata['existencia']}")
                break
        
        if not opcion_entrega_inmediata:
            logger.info("❌ No se encontró opción de entrega inmediata (Sufarmed)")
        
        # ORDENAR POR PRECIO (priorizando productos CON existencia)
        logger.info("Buscando opción de MEJOR PRECIO (producto más barato, preferiblemente con existencias)...")
        productos_ordenados = sorted(todos_productos_ordenados, key=lambda x: (
            x['precio_numerico'],
            0 if x['existencia_numerica'] > 0 else 1
        ))
        
        logger.info("Productos ordenados por precio (menor a mayor, priorizando stock):")
        for i, p in enumerate(productos_ordenados):
            stock_status = "CON STOCK" if p['existencia_numerica'] > 0 else "SIN STOCK"
            logger.info(f"  • #{i+1}: {p['fuente']} - {p['nombre']} - Precio: {p['precio']} ({p['precio_numerico']}) [{stock_status}]")
        
        opcion_mejor_precio = None
        if productos_ordenados:
            opcion_mejor_precio = productos_ordenados[0].copy()
            del opcion_mejor_precio['precio_numerico']
            del opcion_mejor_precio['existencia_numerica']
            
            if productos_ordenados[0]['existencia_numerica'] > 0:
                logger.info(f"✅ Opción de mejor precio CON STOCK seleccionada: {opcion_mejor_precio['nombre']} de {opcion_mejor_precio['fuente']} "
                           f"- Precio: {opcion_mejor_precio['precio']} - Existencia: {opcion_mejor_precio['existencia']}")
            else:
                logger.info(f"⚠️ Opción de mejor precio SIN STOCK seleccionada: {opcion_mejor_precio['nombre']} de {opcion_mejor_precio['fuente']} "
                           f"- Precio: {opcion_mejor_precio['precio']} - Existencia: {opcion_mejor_precio['existencia']}")
        
        # Determinar si hay doble opción
        tiene_doble_opcion = False
        
        if opcion_entrega_inmediata and opcion_mejor_precio:
            if opcion_entrega_inmediata['fuente'] != opcion_mejor_precio['fuente']:
                tiene_doble_opcion = True
                logger.info(f"✅ DOBLE OPCIÓN HABILITADA: Fuentes diferentes ({opcion_entrega_inmediata['fuente']} vs {opcion_mejor_precio['fuente']})")
            elif opcion_entrega_inmediata['precio'] != opcion_mejor_precio['precio']:
                tiene_doble_opcion = True
                logger.info(f"✅ DOBLE OPCIÓN HABILITADA: Precios diferentes ({opcion_entrega_inmediata['precio']} vs {opcion_mejor_precio['precio']})")
            else:
                logger.info("❌ No hay doble opción: Misma fuente y mismo precio")
        else:
            logger.info("❌ No hay doble opción: Falta alguna de las opciones")
        
        logger.info("🏁 ANÁLISIS COMPLETO CON TIMEOUTS - RESULTADOS PREPARADOS 🏁")
        
        return {
            "opcion_entrega_inmediata": opcion_entrega_inmediata,
            "opcion_mejor_precio": opcion_mejor_precio,
            "tiene_doble_opcion": tiene_doble_opcion
        }
