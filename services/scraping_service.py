"""
Servicio de scraping para buscar información de productos farmacéuticos.
Este servicio integra la funcionalidad de scraping de Difarmer,
y está optimizado para el entorno de producción en Google Cloud Run.
"""
import logging
import os
import sys
import time
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
    Clase que proporciona métodos para buscar información de productos farmacéuticos mediante scraping.
    Ahora utiliza el módulo scraper_difarmer en lugar del scraper anterior.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de scraping configurando las rutas y opciones.
        """
        logger.info("Inicializando ScrapingService con scraper_difarmer")
        
        # Verificar que el directorio scraper_difarmer existe
        scraper_path = os.path.join('services', 'scraper_difarmer')
        if not os.path.isdir(scraper_path):
            logger.error(f"Error: El directorio {scraper_path} no existe")
            # Listar directorios disponibles para diagnóstico
            try:
                services_dir = os.listdir('services')
                logger.info(f"Contenido del directorio 'services': {services_dir}")
            except Exception as e:
                logger.error(f"No se pudo listar el directorio 'services': {e}")
        
        # Asegurarse que el módulo scraper_difarmer esté en el path
        try:
            # Intentar ubicar el archivo __init__.py en scraper_difarmer
            init_file = os.path.join(scraper_path, '__init__.py')
            if not os.path.isfile(init_file):
                logger.warning(f"Archivo {init_file} no encontrado. Verificar estructura del módulo.")
            
            # Verificar archivos esenciales para el scraper
            expected_files = ['main.py', 'login.py', 'search.py', 'extract.py']
            for file in expected_files:
                file_path = os.path.join(scraper_path, file)
                if not os.path.isfile(file_path):
                    logger.warning(f"Archivo esencial {file_path} no encontrado.")
            
            # Añadir el directorio actual al path para facilitar las importaciones
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                logger.info(f"Directorio añadido al path: {parent_dir}")
            
            # Importar el módulo scraper_difarmer
            from services.scraper_difarmer import buscar_info_medicamento
            self.buscar_info_medicamento = buscar_info_medicamento
            logger.info("Módulo scraper_difarmer importado correctamente")
        except ImportError as e:
            logger.error(f"Error al importar scraper_difarmer: {e}")
            # Intentar import alternativo
            try:
                sys.path.insert(0, scraper_path)
                # Importación alternativa
                from main import buscar_info_medicamento
                self.buscar_info_medicamento = buscar_info_medicamento
                logger.info("Módulo scraper_difarmer importado mediante ruta alternativa")
            except ImportError as e2:
                logger.error(f"Error en importación alternativa: {e2}")
                raise
    
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
    
    def _format_product_info(self, producto):
        """
        Formatea la información del producto para presentarla de manera consistente.
        
        Args:
            producto (dict): Información del producto obtenida del scraper
            
        Returns:
            dict: Información formateada del producto
        """
        if not producto:
            return None
        
        # Obtener el precio (puede estar en mi_precio o precio_publico)
        precio = producto.get('mi_precio') or producto.get('precio_publico') or "0"
        
        # Formatear correctamente
        result = {
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
            "fuente": "Difarmer"  # Identificar la fuente
        }
        
        return result
    
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
            
            # Intentos de búsqueda con diferentes variantes del nombre
            max_intentos = 2  # Máximo de intentos por variante
            variantes = [
                nombre_producto,  # Primero intentar con el nombre exacto
                nombre_producto.upper(),  # Luego en mayúsculas
            ]
            
            # Si el nombre contiene espacios, también probar con la primera palabra
            palabras = nombre_producto.split()
            if len(palabras) > 1 and len(palabras[0]) > 3:
                variantes.append(palabras[0])  # Añadir primera palabra como variante
            
            # Configuración para entorno de producción (sin interfaz gráfica)
            headless = True
            
            # Verificar si estamos en entorno de desarrollo
            if os.environ.get('ENVIRONMENT', 'production').lower() == 'development':
                headless = False
                logger.info("Utilizando navegador con interfaz gráfica (modo desarrollo)")
            
            # Intentar con cada variante
            for variante in variantes:
                for intento in range(1, max_intentos + 1):
                    logger.info(f"Buscando '{variante}' (intento {intento}/{max_intentos})")
                    
                    try:
                        # Llamar a la función de búsqueda del scraper de Difarmer
                        info_producto = self.buscar_info_medicamento(variante)
                        
                        # Si se encontró información, formatearla y devolverla
                        if info_producto:
                            result = self._format_product_info(info_producto)
                            if result:
                                logger.info(f"Producto encontrado: {result['nombre']}")
                                logger.info(f"Precio: {result['precio']}, Existencia: {result['existencia']}")
                                return result
                    except Exception as e:
                        logger.error(f"Error en intento {intento} con variante '{variante}': {e}")
                        # Esperar un poco antes del siguiente intento
                        time.sleep(1)
            
            # Si llegamos aquí, no se encontró información con ninguna variante
            logger.warning(f"No se encontró información para el producto: {nombre_producto}")
            return None
                
        except Exception as e:
            logger.error(f"Error general al buscar producto con scraper_difarmer: {e}")
            return None
    
    def verificar_disponibilidad(self):
        """
        Verifica que el servicio de scraping está disponible y funcionando.
        
        Returns:
            bool: True si el servicio está disponible, False en caso contrario
        """
        try:
            # Verificar si podemos importar las funciones necesarias
            if hasattr(self, 'buscar_info_medicamento') and callable(self.buscar_info_medicamento):
                logger.info("Servicio de scraping verificado y disponible")
                return True
            else:
                logger.error("La función buscar_info_medicamento no está disponible")
                return False
        except Exception as e:
            logger.error(f"Error al verificar disponibilidad del servicio de scraping: {e}")
            return False
