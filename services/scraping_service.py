"""
Servicio de scraping para obtener información de productos farmacéuticos de Difarmer.
Encapsula la funcionalidad del scraper de Difarmer.
"""
import logging
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir la ruta del scraper de Difarmer al path
SCRAPER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraper_difarmer')
sys.path.append(SCRAPER_PATH)

# Importar las funciones del scraper de Difarmer
try:
    from scraper_difarmer import buscar_info_medicamento
    logger.info("Scraper de Difarmer importado correctamente")
except ImportError as e:
    logger.error(f"Error al importar el scraper de Difarmer: {e}")
    logger.error(f"SCRAPER_PATH: {SCRAPER_PATH}")
    logger.error(f"sys.path: {sys.path}")
    # Si falla la importación, definimos una función dummy
    def buscar_info_medicamento(nombre_medicamento, headless=True):
        logger.error(f"Usando función dummy de buscar_info_medicamento para: {nombre_medicamento}")
        return None

class DifarmerScrapingService:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos
    mediante scraping de Difarmer.
    """
    
    def __init__(self, headless: bool = True):
        """
        Inicializa el servicio de scraping de Difarmer.
        
        Args:
            headless (bool): Si es True, el navegador se ejecuta en modo headless
        """
        self.headless = headless
        logger.info(f"DifarmerScrapingService inicializado (headless={headless})")
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto en Difarmer y extrae su información.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Información del producto o None si no se encuentra
        """
        logger.info(f"Buscando producto en Difarmer: {nombre_producto}")
        try:
            # Usar el scraper de Difarmer para buscar el producto
            info_producto = buscar_info_medicamento(nombre_producto, headless=self.headless)
            
            if info_producto:
                # Mapeo de campos para mantener consistencia con el formato
                # esperado por el resto del sistema
                producto_formateado = {
                    "nombre": info_producto.get("nombre"),
                    "laboratorio": info_producto.get("laboratorio"),
                    "codigo_barras": info_producto.get("codigo_barras"),
                    "registro_sanitario": info_producto.get("registro_sanitario"),
                    "url": info_producto.get("url"),
                    "imagen": info_producto.get("imagen"),
                    "precio": info_producto.get("mi_precio") or info_producto.get("precio_publico")
                }
                
                logger.info(f"Producto encontrado en Difarmer: {producto_formateado['nombre']}")
                return producto_formateado
            else:
                logger.warning(f"No se encontró información para el producto '{nombre_producto}' en Difarmer")
                return None
                
        except Exception as e:
            logger.error(f"Error al buscar producto en Difarmer: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
