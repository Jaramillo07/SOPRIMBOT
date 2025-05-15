"""
Servicio de scraping para buscar información de productos farmacéuticos.
Este servicio integra la funcionalidad de scraping de Difarmer,
reemplazando temporalmente la integración anterior de Sufarmed.
"""
import logging
import os
import sys
import time
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingService:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos mediante scraping.
    Ahora utiliza el módulo scraper_difarmer en lugar del scraper anterior.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de scraping configurando las rutas y opciones.
        """
        logger.info("Inicializando ScrapingService con scraper_difarmer")
        
        # Asegurarnos que el módulo scraper_difarmer esté en el path
        try:
            # Importar el módulo scraper_difarmer
            from services.scraper_difarmer import buscar_info_medicamento
            self.buscar_info_medicamento = buscar_info_medicamento
            logger.info("Módulo scraper_difarmer importado correctamente")
        except ImportError as e:
            logger.error(f"Error al importar scraper_difarmer: {e}")
            raise
    
    def buscar_producto(self, nombre_producto):
        """
        Busca un producto en Difarmer y extrae su información.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Información del producto o None si no se encuentra
        """
        try:
            logger.info(f"Iniciando búsqueda de producto en Difarmer: {nombre_producto}")
            
            # Configuración para entorno de producción (sin interfaz gráfica)
            headless = True
            
            # Verificar si estamos en entorno de desarrollo
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            # Llamar a la función de búsqueda del scraper de Difarmer
            info_producto = self.buscar_info_medicamento(nombre_producto, headless=headless)
            
            if info_producto:
                # Formatear el resultado para mantener compatibilidad con la estructura esperada
                result = {
                    "nombre": info_producto.get('nombre', ''),
                    "laboratorio": info_producto.get('laboratorio', ''),
                    "codigo_barras": info_producto.get('codigo_barras', ''),
                    "registro_sanitario": info_producto.get('registro_sanitario', ''),
                    "url": info_producto.get('url', ''),
                    "imagen": info_producto.get('imagen', ''),
                    "precio": info_producto.get('mi_precio', info_producto.get('precio_publico', '')),
                    "existencia": info_producto.get('existencia', ''),
                    "fuente": "Difarmer"  # Añadir la fuente para identificación
                }
                
                logger.info(f"Producto encontrado: {result['nombre']}")
                return result
            else:
                logger.warning(f"No se encontró información para el producto: {nombre_producto}")
                return None
                
        except Exception as e:
            logger.error(f"Error al buscar producto con scraper_difarmer: {e}")
            return None
