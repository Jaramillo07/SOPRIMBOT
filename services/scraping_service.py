"""
Servicio de scraping modificado para SOPRIM BOT.
Este módulo usa exclusivamente el scraper de NADRO para pruebas.
"""
import logging
import os
import sys
import re
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingService:
    """
    Clase que coordina la búsqueda de productos mediante scraping.
    MODIFICADA: Solo usa el scraper de NADRO para pruebas.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de scraping limitado a NADRO para pruebas.
        """
        logger.info("Inicializando ScrapingService modificado para pruebas con NADRO")
        
        # Deshabilitar los scrapers existentes
        self.difarmer_available = False
        self.sufarmed_available = False
        self.fanasa_available = False
        
        # Verificar si NADRO está disponible
        self.nadro_available = self._check_nadro_available()
        
        # Inicializar el scraper de NADRO si está disponible
        if self.nadro_available:
            try:
                # Añadir el directorio actual al path para facilitar las importaciones
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                
                # Importar el módulo de NADRO
                from services.scraper_nadro import buscar_info_medicamento
                self.buscar_nadro = buscar_info_medicamento
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
        
        # Verificar que el scraper esté disponible
        if not self.nadro_available:
            logger.critical("ALERTA: Scraper NADRO no disponible. La funcionalidad de scraping no estará disponible.")
        else:
            logger.info("MODO PRUEBA: Solo usando scraper NADRO")
    
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
        
        # Obtener el precio 
        precio = producto.get('precio')
        
        # Extraer valor numérico de la existencia para comparaciones
        existencia_numerica = 0
        if producto.get('existencia'):
            stock_match = re.search(r'(\d+)', producto.get('existencia', '0'))
            if stock_match:
                existencia_numerica = int(stock_match.group(1))
            elif "disponible" in producto.get('existencia', '').lower():
                existencia_numerica = 1
        
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
            "existencia_numerica": existencia_numerica,
            "fuente": "NADRO",
            "nombre_farmacia": "NADRO"
        }
    
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
            return float(match.group(1))
        else:
            return 9999999.0  # Valor por defecto si no se puede extraer
    
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
                if resultado:
                    logger.info(f"Producto encontrado en NADRO: {resultado['nombre']} - Precio: {resultado['precio']} - Existencia: {resultado['existencia']}")
                    return resultado
                else:
                    logger.warning(f"Error al formatear producto de NADRO para: {nombre_producto}")
            
            logger.warning(f"No se encontró información en NADRO para: {nombre_producto}")
            return None
        except Exception as e:
            logger.error(f"Error al buscar producto en NADRO: {e}")
            return None
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto usando exclusivamente el scraper de NADRO.
        MODIFICADO: Este método ahora solo usa NADRO para pruebas.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: El producto encontrado o None si no se encuentra
        """
        logger.info(f"Iniciando búsqueda modificada (solo NADRO) para: {nombre_producto}")
        
        # Verificar que el scraper está disponible
        if not self.nadro_available:
            logger.error("No se puede realizar la búsqueda porque el scraper NADRO no está disponible")
            return None
        
        # Buscar con el scraper de NADRO
        try:
            resultado = self.buscar_producto_nadro(nombre_producto)
            
            if resultado:
                logger.info(f"Producto encontrado en NADRO: {resultado['nombre']}")
                # Registrar información detallada
                logger.info(f"Información completa: Precio: {resultado['precio']}, Existencia: {resultado['existencia']}")
                return resultado
            else:
                logger.warning(f"No se encontró información en NADRO para: {nombre_producto}")
                return None
        except Exception as e:
            logger.error(f"Error durante la búsqueda en NADRO: {e}")