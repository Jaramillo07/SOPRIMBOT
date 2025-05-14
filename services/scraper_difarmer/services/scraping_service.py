"""
Servicio de scraping para buscar información de productos farmacéuticos.
Este servicio integra las funcionalidades de scraping modularizadas,
permitiendo buscar productos en diferentes farmacias online.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.scraper_sufarmed import buscar_producto_sufarmed
from services.scraper_difarmer.main import buscar_info_medicamento
from config.settings import HEADLESS_BROWSER

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingService:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos mediante scraping.
    """
    def __init__(self, headless: bool = HEADLESS_BROWSER):
        """
        Inicializa el servicio de scraping.
        Args:
            headless (bool): Indica si el navegador debe ejecutarse en modo headless.
        """
        self.headless = headless
        logger.info(f"Servicio de scraping inicializado (modo headless: {headless})")
        
    def buscar_producto(self, nombre_producto: str) -> dict:
        """
        Busca un producto farmacéutico y retorna su información.
        Args:
            nombre_producto (str): Nombre del producto a buscar
        Returns:
            dict: Información del producto más barato con existencia, o None si no se encuentra
        """
        logger.info(f"Iniciando búsqueda para: {nombre_producto}")
        resultados = []
        
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Usamos lambda para pasar el parámetro headless a las funciones de búsqueda
                tareas = {
                    executor.submit(buscar_producto_sufarmed, nombre_producto, self.headless): 'Sufarmed',
                    executor.submit(lambda: buscar_info_medicamento(nombre_producto, headless=self.headless)): 'Difarmer'
                }
                
                for future in as_completed(tareas):
                    origen = tareas[future]
                    try:
                        resultado = future.result()
                        if resultado:
                            # Verificar existencia con manejo de casos
                            existencia_str = str(resultado.get('existencia', '0')).replace(',', '')
                            try:
                                existencia = int(existencia_str) if existencia_str.isdigit() else 0
                            except (ValueError, TypeError):
                                existencia = 0
                                
                            if existencia > 0:
                                # Normalizar precio para comparar correctamente
                                if origen == 'Difarmer':
                                    # Primero usar mi_precio si está disponible
                                    precio = resultado.get('mi_precio') or resultado.get('precio_publico') or '999999'
                                else:
                                    precio = resultado.get('precio', '999999')
                                    
                                # Intentar convertir el precio a float para comparación
                                try:
                                    precio_limpio = str(precio).replace('$', '').replace(',', '')
                                    resultado['precio_normalizado'] = float(precio_limpio)
                                except (ValueError, AttributeError):
                                    logger.warning(f"No se pudo convertir el precio '{precio}' a float. Usando valor por defecto.")
                                    resultado['precio_normalizado'] = 999999
                                    
                                resultado['nombre_farmacia'] = origen
                                resultados.append(resultado)
                                logger.info(f"Resultado válido de {origen}: {resultado.get('nombre', 'Sin nombre')} - Existencia: {existencia}")
                            else:
                                logger.info(f"Producto sin existencia en {origen}")
                    except Exception as e:
                        logger.warning(f"Error al procesar resultados de {origen}: {e}")
            
            if not resultados:
                logger.warning(f"No se encontró disponibilidad del producto '{nombre_producto}' en ninguna farmacia")
                return None
                
            # Ordenar por precio normalizado (el más barato con existencia)
            resultados_ordenados = sorted(resultados, key=lambda x: x.get('precio_normalizado', 999999))
            mejor_opcion = resultados_ordenados[0]
            
            # Obtener el precio para mostrar en el log
            if mejor_opcion['nombre_farmacia'] == 'Difarmer':
                precio_mostrar = mejor_opcion.get('mi_precio') or mejor_opcion.get('precio_publico', 'N/A')
            else:
                precio_mostrar = mejor_opcion.get('precio', 'N/A')
                
            logger.info(f"Mejor opción encontrada: {mejor_opcion.get('nombre', 'Sin nombre')} en {mejor_opcion['nombre_farmacia']} por ${precio_mostrar}")
            return mejor_opcion
            
        except Exception as e:
            logger.error(f"Error durante la búsqueda del producto: {e}")
            return None
