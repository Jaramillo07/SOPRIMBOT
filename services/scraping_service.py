"""
Servicio de scraping integrado para buscar información de productos farmacéuticos.
Este servicio orquesta los scrapers de Difarmer y Sufarmed, comparando resultados
y seleccionando el mejor en función de existencias y precio.
"""
import logging
import os
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedScrapingService:
    """
    Clase que coordina la búsqueda de productos en múltiples fuentes,
    comparando resultados y seleccionando la mejor opción.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de scraping integrado configurando cada scraper individual.
        """
        logger.info("Inicializando IntegratedScrapingService con múltiples scrapers")
        
        # Verificar qué servicios están disponibles
        self.difarmer_available = self._check_difarmer_available()
        self.sufarmed_available = self._check_sufarmed_available()
        
        # Inicializar scrapers solo si están disponibles
        if self.difarmer_available:
            try:
                from services.scraper_difarmer import buscar_info_medicamento as buscar_difarmer
                self.buscar_difarmer = buscar_difarmer
                logger.info("Scraper Difarmer inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraper_difarmer: {e}")
                self.difarmer_available = False
        
        if self.sufarmed_available:
            try:
                # Importar el scraper original
                from services.scraping_service_sufarmed import ScrapingService as SufarmedService
                self.sufarmed_service = SufarmedService()
                logger.info("Scraper Sufarmed inicializado correctamente")
            except ImportError as e:
                logger.error(f"Error al importar scraping_service_sufarmed: {e}")
                self.sufarmed_available = False
        
        # Verificar que al menos un scraper esté disponible
        if not self.difarmer_available and not self.sufarmed_available:
            logger.critical("ALERTA: Ningún scraper está disponible. La funcionalidad estará limitada.")
    
    def _check_difarmer_available(self):
        """Verifica si el scraper de Difarmer está disponible"""
        try:
            import services.scraper_difarmer
            return True
        except ImportError:
            logger.warning("Scraper Difarmer no disponible")
            return False
    
    def _check_sufarmed_available(self):
        """Verifica si el scraper de Sufarmed está disponible"""
        try:
            import services.scraping_service_sufarmed
            return True
        except ImportError:
            logger.warning("Scraper Sufarmed no disponible")
            return False
    
    def _extract_numeric_price(self, price_str):
        """
        Extrae un valor numérico del precio para comparación.
        
        Args:
            price_str (str): Precio en formato de texto (ej. "$120.50", "120,50", "120")
            
        Returns:
            float: Valor numérico del precio o 9999999.0 si no se puede extraer
        """
        if not price_str:
            return 9999999.0  # Valor alto para que tenga prioridad baja
        
        # Eliminar símbolos de moneda y espacios
        clean_price = price_str.replace('$', '').replace(' ', '')
        
        # Convertir comas a puntos si es necesario
        if ',' in clean_price and '.' not in clean_price:
            clean_price = clean_price.replace(',', '.')
        elif ',' in clean_price and '.' in clean_price:
            # Formato como "$1,234.56"
            clean_price = clean_price.replace(',', '')
        
        # Extraer el número con regex
        match = re.search(r'(\d+(\.\d+)?)', clean_price)
        
        if match:
            return float(match.group(1))
        else:
            return 9999999.0  # Valor por defecto si no se puede extraer
    
    def _extract_numeric_existencia(self, existencia_str):
        """
        Extrae un valor numérico de existencia para comparación.
        
        Args:
            existencia_str (str): Existencia en formato de texto (ej. "15", "1,500")
            
        Returns:
            int: Valor numérico de existencia o 0 si no se puede extraer
        """
        if not existencia_str:
            return 0
        
        # Eliminar comas y espacios
        clean_existencia = existencia_str.replace(',', '').replace(' ', '')
        
        # Extraer el número con regex
        match = re.search(r'(\d+)', clean_existencia)
        
        if match:
            return int(match.group(1))
        else:
            return 0
    
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
            "fuente": "Difarmer"
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
            "fuente": "Sufarmed"
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
            info_producto = self.buscar_difarmer(nombre_producto)
            
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
                logger.info(f"Producto encontrado en Sufarmed: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                return resultado
            else:
                logger.warning(f"No se encontró información en Sufarmed para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error al buscar producto en Sufarmed: {e}")
            return None
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto en todas las fuentes disponibles, compara resultados
        y selecciona el mejor basado en existencia y precio.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: El mejor producto encontrado o None si no se encuentra en ninguna fuente
        """
        logger.info(f"Iniciando búsqueda integrada para: {nombre_producto}")
        
        # Lista para almacenar resultados de todas las fuentes
        resultados = []
        
        # Verificar qué scrapers podemos usar
        scrapers_disponibles = []
        if self.difarmer_available:
            scrapers_disponibles.append(('difarmer', self.buscar_producto_difarmer))
        if self.sufarmed_available:
            scrapers_disponibles.append(('sufarmed', self.buscar_producto_sufarmed))
        
        if not scrapers_disponibles:
            logger.error("No hay scrapers disponibles para realizar la búsqueda")
            return None
        
        # Para más eficiencia, usar ThreadPoolExecutor para búsquedas en paralelo
        with ThreadPoolExecutor(max_workers=len(scrapers_disponibles)) as executor:
            # Crear tareas de búsqueda
            futures = {
                executor.submit(search_func, nombre_producto): source_name
                for source_name, search_func in scrapers_disponibles
            }
            
            # Recopilar resultados a medida que se completan
            for future in futures:
                source_name = futures[future]
                try:
                    resultado = future.result()
                    if resultado:
                        logger.info(f"Resultado obtenido de {source_name}")
                        resultados.append(resultado)
                except Exception as e:
                    logger.error(f"Error en búsqueda de {source_name}: {e}")
        
        # Si no hay resultados, terminar
        if not resultados:
            logger.warning(f"No se encontraron resultados para: {nombre_producto}")
            return None
        
        # Filtrar productos sin existencia 
        productos_con_existencia = [p for p in resultados if p['existencia_numerica'] > 0]
        
        # Si hay productos con existencia, usarlos, sino usar todos los resultados
        productos_a_comparar = productos_con_existencia if productos_con_existencia else resultados
        
        # Ordenar por precio (menor a mayor)
        productos_ordenados = sorted(productos_a_comparar, key=lambda x: x['precio_numerico'])
        
        # Elegir el de menor precio
        mejor_producto = productos_ordenados[0] if productos_ordenados else None
        
        if mejor_producto:
            logger.info(f"Mejor resultado: {mejor_producto['nombre']} de {mejor_producto['fuente']} "
                       f"- Precio: {mejor_producto['precio']} - Existencia: {mejor_producto['existencia']}")
            
            # Eliminar campos auxiliares de comparación antes de devolver
            del mejor_producto['precio_numerico']
            del mejor_producto['existencia_numerica']
        
        return mejor_producto
