"""
Servicio de scraping unificado para buscar información de productos farmacéuticos.
Puede utilizar diferentes fuentes: Sufarmed (implementación actual) o Difarmer (nuevo scraper).
"""
import logging
import os
import sys
from pathlib import Path
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    ElementClickInterceptedException
)
from config.settings import HEADLESS_BROWSER

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
    DIFARMER_AVAILABLE = True
    logger.info("Scraper de Difarmer importado correctamente")
except ImportError as e:
    DIFARMER_AVAILABLE = False
    logger.error(f"Error al importar el scraper de Difarmer: {e}")
    logger.error(f"SCRAPER_PATH: {SCRAPER_PATH}")
    logger.error(f"sys.path: {sys.path}")
    # Si falla la importación, definimos una función dummy
    def buscar_info_medicamento(nombre_medicamento, headless=True):
        logger.error(f"Usando función dummy de buscar_info_medicamento para: {nombre_medicamento}")
        return None

class ScrapingService:
    """
    Clase que proporciona métodos para buscar información de productos farmacéuticos mediante scraping.
    Puede utilizar diferentes fuentes: Sufarmed o Difarmer.
    """
    
    def __init__(self, headless: bool = HEADLESS_BROWSER, 
                username: str = "laubec83@gmail.com", 
                password: str = "Sr3ChK8pBoSEScZ",
                login_url: str = "https://sufarmed.com/sufarmed/iniciar-sesion"):
        self.headless = headless
        self.username = username
        self.password = password
        self.login_url = login_url
        self.timeout = 15
        self.difarmer_available = DIFARMER_AVAILABLE
        
        logger.info(f"ScrapingService inicializado (headless={headless}, difarmer_available={DIFARMER_AVAILABLE})")
    
    # [Mantener todos los métodos actuales de ScrapingService para Sufarmed]
    # find_one, inicializar_navegador, login, es_pagina_producto, extraer_info_producto, etc.
    
    def buscar_producto_difarmer(self, nombre_producto):
        """
        Busca un producto en Difarmer y extrae su información.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            
        Returns:
            dict: Información del producto o None si no se encuentra
        """
        if not self.difarmer_available:
            logger.warning("Scraper de Difarmer no disponible")
            return None
            
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
            
    def buscar_producto(self, nombre_producto, fuente="sufarmed"):
        """
        Busca un producto en la fuente especificada y extrae su información.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            fuente (str): Fuente a utilizar ('sufarmed', 'difarmer', o 'ambos')
            
        Returns:
            dict: Información del producto o None si no se encuentra
        """
        if fuente == "difarmer" or fuente == "ambos":
            # Intentar con Difarmer primero si está habilitado y es la fuente seleccionada
            if self.difarmer_available:
                logger.info(f"Buscando producto en Difarmer primero: {nombre_producto}")
                producto = self.buscar_producto_difarmer(nombre_producto)
                if producto:
                    return producto
                    
                # Si no se encontró en Difarmer y la fuente es 'ambos', seguir con Sufarmed
                if fuente == "ambos":
                    logger.info(f"Producto no encontrado en Difarmer, intentando con Sufarmed: {nombre_producto}")
                else:
                    return None
            else:
                logger.warning("Scraper de Difarmer no disponible, usando solo Sufarmed")
                
        # Si la fuente es 'sufarmed' o 'ambos' y no se encontró en Difarmer
        if fuente == "sufarmed" or fuente == "ambos":
            logger.info(f"Buscando producto en Sufarmed: {nombre_producto}")
            # Usar el método original de búsqueda en Sufarmed
            driver = self.inicializar_navegador()
            if not driver:
                return None
                
            # [Código original para buscar en Sufarmed]
            # Este es el código actual de la función buscar_producto que ya existe
            
            try:
                # NUEVO: Realizar login primero para obtener precios
                logger.info("Iniciando proceso de login antes de buscar productos")
                login_exitoso = self.login(driver)
                
                if login_exitoso:
                    logger.info("Login exitoso, procediendo con la búsqueda de productos")
                else:
                    logger.warning("Login fallido, continuando sin autenticación (no se obtendrán precios)")
                
                # Acceder al sitio web principal
                logger.info(f"Accediendo al sitio web de Sufarmed...")
                driver.get("https://sufarmed.com")
                
                # ... [Resto del código original de búsqueda en Sufarmed]
                
            except Exception as e:
                logger.error(f"Error durante la búsqueda en Sufarmed: {e}")
            finally:
                # Cerrar el navegador
                if driver:
                    driver.quit()
                    
        # Si no se encontró en ninguna fuente
        return None
