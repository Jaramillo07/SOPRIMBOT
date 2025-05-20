"""
Servicio de scraping integrado para buscar información de productos farmacéuticos.
Este servicio orquesta los scrapers de Difarmer, Sufarmed, FANASA y NADRO de forma secuencial,
comparando resultados y seleccionando opciones según disponibilidad y precio.
"""
import logging
import os
import sys
import time
import re
import concurrent.futures
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
        logger.info("Inicializando ScrapingService integrado con múltiples scrapers (modo secuencial)")
        
        # Verificar qué servicios están disponibles
        self.difarmer_available = self._check_difarmer_available()
        self.sufarmed_available = self._check_sufarmed_available()
        # Activar la verificación de FANASA en lugar de forzarlo a False
        self.fanasa_available = self._check_fanasa_available()
        self.nadro_available = self._check_nadro_available()
        
        # Inicializar scrapers solo si están disponibles
        if self.difarmer_available:
            try:
                # Añadir el directorio actual al path para facilitar las importaciones
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                    logger.info(f"Directorio añadido al path: {parent_dir}")
                
                # Importar el módulo scraper_difarmer
                from services.scraper_difarmer import buscar_info_medicamento as buscar_difarmer
                self.buscar_difarmer = buscar_difarmer
                logger.info("Scraper Difarmer inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_difarmer: {e}")
                self.difarmer_available = False
                # Intentar import alternativo
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
                # Importar el servicio original de Sufarmed
                # Asumimos que este es el que está en scraping_service_sufarmed.py
                from services.scraping_service_sufarmed import ScrapingService as SufarmedService
                self.sufarmed_service = SufarmedService()
                logger.info("Scraper Sufarmed inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraping_service_sufarmed: {e}")
                # Búsqueda alternativa del servicio de Sufarmed
                try:
                    # Comprobar si existe como módulo independiente
                    if os.path.exists(os.path.join('services', 'sufarmed_service.py')):
                        from services.sufarmed_service import ScrapingService as SufarmedService
                        self.sufarmed_service = SufarmedService()
                        self.sufarmed_available = True
                        logger.info("Scraper Sufarmed inicializado desde ruta alternativa")
                except ImportError:
                    self.sufarmed_available = False
        
        # Inicializar FANASA si está disponible
        if self.fanasa_available:
            try:
                # Importar el módulo de FANASA
                from services.scraper_fanasa import buscar_info_medicamento as buscar_fanasa
                self.buscar_fanasa = buscar_fanasa
                logger.info("Scraper FANASA inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_fanasa: {e}")
                self.fanasa_available = False
                # Intentar import alternativo
                try:
                    scraper_path = os.path.join('services', 'scraper_fanasa')
                    sys.path.insert(0, scraper_path)
                    from main import buscar_info_medicamento
                    self.buscar_fanasa = buscar_info_medicamento
                    self.fanasa_available = True
                    logger.info("Scraper FANASA inicializado mediante ruta alternativa")
                except ImportError as e2:
                    logger.error(f"Error en importación alternativa de FANASA: {e2}")

        # Inicializar NADRO si está disponible
        if self.nadro_available:
            try:
                # Importar el módulo de NADRO
                from services.scraper_nadro import buscar_info_medicamento as buscar_nadro
                self.buscar_nadro = buscar_nadro
                logger.info("Scraper NADRO inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_nadro: {e}")
                self.nadro_available = False
                # Intentar import alternativo
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
            # Verificar que existe el directorio
            scraper_path = os.path.join('services', 'scraper_difarmer')
            if not os.path.isdir(scraper_path):
                logger.warning(f"Directorio {scraper_path} no encontrado")
                return False
            
            # Verificar que existen los archivos principales
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
            # Verificar que existe el archivo de servicio
            sufarmed_file = os.path.join('services', 'scraping_service_sufarmed.py')
            if os.path.exists(sufarmed_file):
                return True
            
            # Alternativa: verificar si existe como otro archivo
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
            # Verificar que existe el directorio
            scraper_path = os.path.join('services', 'scraper_fanasa')
            if not os.path.isdir(scraper_path):
                logger.warning(f"Directorio {scraper_path} no encontrado")
                return False
            
            # Verificar que existen los archivos principales
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
            # Verificar que existe el directorio
            scraper_path = os.path.join('services', 'scraper_nadro')
            if not os.path.isdir(scraper_path):
                logger.warning(f"Directorio {scraper_path} no encontrado")
                return False
            
            # Verificar que existen los archivos principales
            required_files = ['__init__.py', 'main.py']
            for file in required_files:
                if not os.path.exists(os.path.join(scraper_path, file)):
                    logger.warning(f"Archivo {file} no encontrado en {scraper_path}")
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Error al verificar disponibilidad de NADRO: {e}")
            return False
    
    def _extract_numeric_price(self, price_str):
        """
        Extrae un valor numérico del precio para comparación.
        
        Modificado para tratar los precios de cero como valores muy altos (baja prioridad).
        
        Args:
            price_str (str): Precio en formato de texto (ej. "$120.50", "120,50", "120")
            
        Returns:
            float: Valor numérico del precio o 9999999.0 si no se puede extraer o es cero
        """
        if not price_str:
            return 9999999.0  # Valor alto para que tenga prioridad baja
        
        # Eliminar símbolos de moneda y espacios
        clean_price = str(price_str).replace('$', '').replace(' ', '')
        
        # Convertir comas a puntos si es necesario
        if ',' in clean_price and '.' not in clean_price:
            clean_price = clean_price.replace(',', '.')
        elif ',' in clean_price and '.' in clean_price:
            # Formato como "$1,234.56"
            clean_price = clean_price.replace(',', '')
        
        # Extraer el número con regex
        match = re.search(r'(\d+(\.\d+)?)', clean_price)
        
        if match:
            price_value = float(match.group(1))
            # Considerar precios de cero como valores altos (baja prioridad)
            if price_value == 0:
                return 9999999.0
            return price_value
        else:
            return 9999999.0  # Valor por defecto si no se puede extraer
    
    def _extract_numeric_existencia(self, existencia_str):
        """
        Extrae un valor numérico de existencia para comparación.
        
        Args:
            existencia_str (str): Existencia en formato de texto (ej. "15", "1,500", "Si", "Disponible")
            
        Returns:
            int: Valor numérico de existencia o 0 si no se puede extraer
        """
        if not existencia_str:
            return 0
        
        # Valores especiales que indican disponibilidad sin cantidad específica
        valores_disponible = ["si", "sí", "disponible", "en stock", "hay"]
        
        # Verificar primero si es un valor especial que indica disponibilidad
        if str(existencia_str).lower() in valores_disponible:
            return 1  # Asignar valor positivo para indicar disponibilidad
        
        # Convertir a string y limpiar
        clean_existencia = str(existencia_str).replace(',', '').replace(' ', '')
        
        # Extraer el número con regex
        match = re.search(r'(\d+)', clean_existencia)
        
        if match:
            return int(match.group(1))
        
        # Si no contiene números pero tiene palabras que indican disponibilidad
        for palabra in valores_disponible:
            if palabra in str(existencia_str).lower():
                return 1  # Asignar valor positivo
        
        return 0  # No hay disponibilidad o no se puede determinar
    
    def _format_producto_difarmer(self, producto):
        """
        Formatea los datos del producto de Difarmer al formato estandarizado.
        
        Args:
            producto (dict): Información del producto en formato Difarmer
            
        Returns:
            dict: Producto formateado al estándar común
        """
        if not producto:
            return None
        
        # Obtener el precio (puede estar en mi_precio o precio_publico)
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
        
        Args:
            producto (dict): Información del producto en formato Sufarmed
            
        Returns:
            dict: Producto formateado al estándar común
        """
        if not producto:
            return None
        
        # El precio en Sufarmed generalmente está en 'precio'
        precio = producto.get('precio', "0")
        existencia = producto.get('existencia', '0')
        
        # Manejo especial para valores de existencia
        existencia_numerica = 0
        
        # Si stock indica que está disponible pero no tenemos un valor numérico claro
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
        
        Args:
            producto (dict): Información del producto en formato FANASA
            
        Returns:
            dict: Producto formateado al estándar común
        """
        if not producto:
            return None
        
        # Obtener el precio (puede estar en precio_neto, precio_publico, precio_farmacia o pmp)
        precio = producto.get('precio_neto') or producto.get('precio_publico') or producto.get('precio_farmacia') or producto.get('pmp') or "0"
        
        # Extraer valor numérico de la existencia para comparaciones
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

        Args:
            producto (dict): Información del producto en formato NADRO

        Returns:
            dict: Producto formateado al estándar común
        """
        if not producto:
            return None

        # Obtener el precio (puede estar en diferentes campos según el scraper NADRO)
        precio = producto.get('precio') or producto.get('precio_farmacia') or producto.get('precio_publico') or "0"

        # Determinar existencia numérica
        existencia_numerica = 0
        existencia_raw = producto.get('existencia', '')
        texto_existencia = str(existencia_raw).lower()
        indicadores_disponibilidad = ["disponible", "entrega mañana", "sí", "si", "stock"]

        # Verificar si hay número en la existencia
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
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Producto formateado o None si no se encuentra
        """
        if not self.difarmer_available:
            logger.warning("Scraper Difarmer no disponible. No se realizará búsqueda.")
            return None
        
        try:
            logger.info(f"Buscando producto en Difarmer: {nombre_producto}")
            
            # Configuración para entorno de producción (sin interfaz gráfica)
            headless = True
            
            # Verificar si estamos en entorno de desarrollo
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            # Llamar a la función de búsqueda del scraper de Difarmer
            info_producto = self.buscar_difarmer(nombre_producto, headless=headless)
            
            # Formatear el producto al estándar común
            if info_producto:
                resultado = self._format_producto_difarmer(info_producto)
                logger.info(f"Producto encontrado en Difarmer: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                return resultado
            else:
                logger.warning(f"No se encontró información en Difarmer para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error al buscar producto en Difarmer: {e}")
            return None
    
    def buscar_producto_sufarmed(self, nombre_producto):
        """
        Busca un producto en Sufarmed y formatea el resultado.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Producto formateado o None si no se encuentra
        """
        if not self.sufarmed_available:
            logger.warning("Scraper Sufarmed no disponible. No se realizará búsqueda.")
            return None
        
        try:
            logger.info(f"Buscando producto en Sufarmed: {nombre_producto}")
            
            # Llamar a la función de búsqueda del scraper de Sufarmed
            info_producto = self.sufarmed_service.buscar_producto(nombre_producto)
            
            # Formatear el producto al estándar común
            if info_producto:
                resultado = self._format_producto_sufarmed(info_producto)
                logger.info(f"Producto encontrado en Sufarmed: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']} (Valor numérico: {resultado['existencia_numerica']})")
                return resultado
            else:
                logger.warning(f"No se encontró información en Sufarmed para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error al buscar producto en Sufarmed: {e}")
            return None
    
    def buscar_producto_fanasa(self, nombre_producto):
        """
        Busca un producto en FANASA y formatea el resultado.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Producto formateado o None si no se encuentra
        """
        if not self.fanasa_available:
            logger.warning("Scraper FANASA no disponible. No se realizará búsqueda.")
            return None
        
        try:
            logger.info(f"Buscando producto en FANASA: {nombre_producto}")
            
            # Configuración para entorno de producción (sin interfaz gráfica)
            headless = True
            
            # Verificar si estamos en entorno de desarrollo
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            # Llamar a la función de búsqueda del scraper de FANASA
            info_producto = self.buscar_fanasa(nombre_producto, headless=headless)
            
            # Formatear el producto al estándar común
            if info_producto:
                resultado = self._format_producto_fanasa(info_producto)
                logger.info(f"Producto encontrado en FANASA: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                return resultado
            else:
                logger.warning(f"No se encontró información en FANASA para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error al buscar producto en FANASA: {e}")
            return None

    def buscar_producto_nadro(self, nombre_producto):
        """
        Busca un producto en NADRO y formatea el resultado.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Producto formateado o None si no se encuentra
        """
        if not self.nadro_available:
            logger.warning("Scraper NADRO no disponible. No se realizará búsqueda.")
            return None
        
        try:
            logger.info(f"Buscando producto en NADRO: {nombre_producto}")
            
            # Configuración para entorno de producción (sin interfaz gráfica)
            headless = True
            
            # Verificar si estamos en entorno de desarrollo
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            # Llamar a la función de búsqueda del scraper de NADRO
            info_producto = self.buscar_nadro(nombre_producto, headless=headless)
            
            # Formatear el producto al estándar común
            if info_producto:
                resultado = self._format_producto_nadro(info_producto)
                logger.info(f"Producto encontrado en NADRO: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                return resultado
            else:
                logger.warning(f"No se encontró información en NADRO para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error al buscar producto en NADRO: {e}")
            return None
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto en todas las fuentes disponibles,
        compara resultados y selecciona opciones según la nueva lógica de negocio:
        - Opción de entrega inmediata (Sufarmed con stock)
        - Opción de mejor precio (producto más barato con stock)
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Diccionario con opciones de productos disponibles y un flag de doble opción
        """
        logger.info(f"Iniciando búsqueda secuencial para: {nombre_producto}")
        
        # Lista para almacenar resultados de todas las fuentes
        resultados = []
        
        # FASE 1: Difarmer y Sufarmed en paralelo (ya probados y funcionan juntos)
        fase1_scrapers = []
        if self.difarmer_available:
            fase1_scrapers.append(('difarmer', self.buscar_producto_difarmer))
        if self.sufarmed_available:
            fase1_scrapers.append(('sufarmed', self.buscar_producto_sufarmed))
        
        if fase1_scrapers:
            logger.info(f"FASE 1: Ejecutando scrapers {', '.join([x[0] for x in fase1_scrapers])}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(fase1_scrapers)) as executor:
                futures = {}
                for source_name, search_func in fase1_scrapers:
                    future = executor.submit(search_func, nombre_producto)
                    futures[future] = source_name
                
                for future in concurrent.futures.as_completed(futures):
                    source_name = futures[future]
                    try:
                        resultado = future.result()
                        if resultado:
                            # Verificar que el precio no sea cero antes de añadirlo
                            if resultado['precio_numerico'] < 9999998.0:  # Un valor normal
                                logger.info(f"Resultado obtenido de {source_name}")
                                resultados.append(resultado)
                            else:
                                logger.warning(f"Resultado de {source_name} descartado por precio cero o inválido")
                    except Exception as e:
                        logger.error(f"Error en búsqueda de {source_name}: {e}")
        
        # Delay de 5 segundos entre Fase 1 y Fase 2
        logger.info("⏱️ Esperando 5 segundos antes de iniciar FASE 2...")
        time.sleep(5)
        
        # FASE 2: NADRO (independiente)
        if self.nadro_available:
            logger.info("FASE 2: Ejecutando scraper NADRO")
            try:
                resultado_nadro = self.buscar_producto_nadro(nombre_producto)
                if resultado_nadro:
                    # Verificar que el precio no sea cero antes de añadirlo
                    if resultado_nadro['precio_numerico'] < 9999998.0:  # Un valor normal
                        logger.info("Resultado obtenido de NADRO")
                        resultados.append(resultado_nadro)
                    else:
                        logger.warning("Resultado de NADRO descartado por precio cero o inválido")
            except Exception as e:
                logger.error(f"Error en búsqueda de NADRO: {e}")
        
        # Delay de 5 segundos entre Fase 2 y Fase 3
        logger.info("⏱️ Esperando 5 segundos antes de iniciar FASE 3...")
        time.sleep(5)
        
        # FASE 3: FANASA (último recurso)
        if self.fanasa_available:
            # Agregar log especial para enfatizar que FANASA siempre se ejecuta al final
            if resultados:
                logger.info("FASE 3: Ejecutando scraper FANASA (siempre ejecutado como último recurso, aunque ya existan resultados)")
            else:
                logger.info("FASE 3: Ejecutando scraper FANASA como último recurso")
                
            try:
                resultado_fanasa = self.buscar_producto_fanasa(nombre_producto)
                if resultado_fanasa:
                    # Verificar que el precio no sea cero antes de añadirlo
                    if resultado_fanasa['precio_numerico'] < 9999998.0:  # Un valor normal
                        logger.info("Resultado obtenido de FANASA")
                        resultados.append(resultado_fanasa)
                    else:
                        logger.warning("Resultado de FANASA descartado por precio cero o inválido")
            except Exception as e:
                logger.error(f"Error en búsqueda de FANASA: {e}")
        
        # COMIENZA PROCESO DE COMPARACIÓN Y SELECCIÓN
        logger.info("🔍 COMENZANDO ANÁLISIS Y COMPARACIÓN DE RESULTADOS 🔍")
        
        # Si no hay resultados, terminar
        if not resultados:
            logger.warning(f"No se encontraron resultados para: {nombre_producto}")
            return {
                "opcion_entrega_inmediata": None,
                "opcion_mejor_precio": None,
                "tiene_doble_opcion": False
            }
        
        # Imprimir resultados para diagnóstico
        logger.info(f"Analizando {len(resultados)} resultados encontrados:")
        for i, resultado in enumerate(resultados):
            logger.info(f"  • Resultado #{i+1}: {resultado['fuente']} - "
                       f"Nombre: {resultado['nombre']} - "
                       f"Precio: {resultado['precio']} ({resultado['precio_numerico']}) - "
                       f"Existencia: {resultado['existencia']} ({resultado['existencia_numerica']})")
        
        # Filtrar productos con existencia
        productos_con_existencia = [p for p in resultados if p['existencia_numerica'] > 0]
        logger.info(f"Productos con existencias disponibles: {len(productos_con_existencia)} de {len(resultados)}")
        
        # Si no hay productos con existencia, devolver None para ambas opciones
        if not productos_con_existencia:
            logger.warning(f"No se encontraron productos con existencia para: {nombre_producto}")
            return {
                "opcion_entrega_inmediata": None,
                "opcion_mejor_precio": None,
                "tiene_doble_opcion": False
            }
        
        # Buscar opción de entrega inmediata (Sufarmed con stock)
        logger.info("Buscando opción de ENTREGA INMEDIATA (producto de Sufarmed con stock)...")
        opcion_entrega_inmediata = None
        for producto in productos_con_existencia:
            if producto['fuente'] == "Sufarmed" and producto['existencia_numerica'] > 0:
                opcion_entrega_inmediata = producto.copy()
                # Eliminar campos auxiliares de comparación
                del opcion_entrega_inmediata['precio_numerico']
                del opcion_entrega_inmediata['existencia_numerica']
                logger.info(f"✅ Opción de entrega inmediata seleccionada: {opcion_entrega_inmediata['nombre']} de Sufarmed "
                           f"- Precio: {opcion_entrega_inmediata['precio']} - Existencia: {opcion_entrega_inmediata['existencia']}")
                break
        
        if not opcion_entrega_inmediata:
            logger.info("❌ No se encontró opción de entrega inmediata (Sufarmed)")
        
        # Ordenar por precio (menor a mayor) para encontrar la opción de mejor precio
        logger.info("Buscando opción de MEJOR PRECIO (producto más barato con existencias)...")
        productos_ordenados = sorted(productos_con_existencia, key=lambda x: x['precio_numerico'])
        
        # Mostrar todos los productos ordenados por precio
        logger.info("Productos ordenados por precio (menor a mayor):")
        for i, p in enumerate(productos_ordenados):
            logger.info(f"  • #{i+1}: {p['fuente']} - {p['nombre']} - Precio: {p['precio']} ({p['precio_numerico']})")
        
        # Elegir el de menor precio
        opcion_mejor_precio = None
        if productos_ordenados:
            opcion_mejor_precio = productos_ordenados[0].copy()
            # Eliminar campos auxiliares de comparación
            del opcion_mejor_precio['precio_numerico']
            del opcion_mejor_precio['existencia_numerica']
            logger.info(f"✅ Opción de mejor precio seleccionada: {opcion_mejor_precio['nombre']} de {opcion_mejor_precio['fuente']} "
                       f"- Precio: {opcion_mejor_precio['precio']} - Existencia: {opcion_mejor_precio['existencia']}")
        
        # Determinar si hay doble opción
        tiene_doble_opcion = False
        
        if opcion_entrega_inmediata and opcion_mejor_precio:
            # Si la opción de entrega inmediata es diferente a la opción de mejor precio
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
        
        logger.info("🏁 ANÁLISIS COMPLETO - RESULTADOS PREPARADOS 🏁")
        
        return {
            "opcion_entrega_inmediata": opcion_entrega_inmediata,
            "opcion_mejor_precio": opcion_mejor_precio,
            "tiene_doble_opcion": tiene_doble_opcion
        }

# Función para generar respuestas a partir de los resultados de búsqueda
def generate_product_response(producto_info, query=None, additional_context=None):
    """
    Genera una respuesta para el usuario basada en las opciones de productos disponibles.
    
    Args:
        producto_info (dict): Diccionario con las opciones de productos disponibles
        query (str, opcional): La consulta original del usuario
        additional_context (dict, opcional): Contexto adicional para la generación
        
    Returns:
        str: Respuesta generada para el usuario
    """
    # Si no hay opciones disponibles
    if not producto_info["opcion_entrega_inmediata"] and not producto_info["opcion_mejor_precio"]:
        return f"Lo siento, no encontré información sobre {query} en nuestras farmacias asociadas."
    
    # Si solo hay una opción (sea entrega inmediata o mejor precio)
    if not producto_info["tiene_doble_opcion"]:
        producto = producto_info["opcion_entrega_inmediata"] or producto_info["opcion_mejor_precio"]
        
        # Determinar si la entrega es inmediata o no
        delivery_text = "hoy mismo" if producto["fuente"] == "Sufarmed" else "mañana"
        
        # Generar respuesta para una sola opción
        response = f"Encontré el producto {producto['nombre']}. El precio es {producto['precio']} y está disponible para entrega {delivery_text}."
        
        return response
    
    # Si hay dos opciones diferentes
    else:
        entrega_inmediata = producto_info["opcion_entrega_inmediata"]
        mejor_precio = producto_info["opcion_mejor_precio"]
        
        nombre_producto = entrega_inmediata['nombre'] or mejor_precio['nombre']
        
        response = f"📦 Tenemos dos opciones para {nombre_producto}:\n\n"
        
        # Añadir opción de entrega inmediata
        response += f"🚚 *Entrega inmediata* hoy mismo con un precio de {entrega_inmediata['precio']}\n\n"
        
        # Añadir opción de mejor precio
        response += f"💲 *Mejor precio* con entrega mañana por {mejor_precio['precio']}"
        
        return response
