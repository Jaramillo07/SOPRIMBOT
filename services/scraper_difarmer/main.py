#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .login import login_difarmer
from .search import buscar_producto
from .extract import extraer_info_producto
from .save import guardar_resultados
from .settings import logger

def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en Difarmer.
   
    Args:
        nombre_medicamento (str): Nombre del medicamento a buscar
        headless (bool): Si es True, el navegador se ejecuta en modo headless
       
    Returns:
        dict: Diccionario con la información del medicamento o None si no se encuentra
    """
    driver = None
    try:
        # 1. Iniciar sesión en Difarmer
        logger.info(f"Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")
       
        driver = login_difarmer(headless=headless)
        if not driver:
            logger.error("No se pudo iniciar sesión en Difarmer. Abortando búsqueda.")
            return None
       
        # 2. Buscar el producto
        logger.info(f"Sesión iniciada. Buscando producto: '{nombre_medicamento}'")
       
        resultado_busqueda = buscar_producto(driver, nombre_medicamento)
       
        if not resultado_busqueda:
            logger.warning(f"No se pudo encontrar o acceder al producto: '{nombre_medicamento}'")
            return None
       
        # 3. Extraer información del producto
        logger.info("Extrayendo información del producto...")
        info_producto = extraer_info_producto(driver)
        
        # Verificar que info_producto sea un diccionario o None
        if info_producto is not None and not isinstance(info_producto, dict):
            logger.error(f"Error: extraer_info_producto no devolvió un diccionario, devolvió {type(info_producto)}")
            return None
        
        return info_producto
       
    except Exception as e:
        logger.error(f"Error general durante el proceso: {e}")
        return None
    finally:
        if driver:
            logger.info("Cerrando navegador...")
            driver.quit()

# Función principal para ejecutar desde línea de comandos
if __name__ == "__main__":
    import sys
   
    print("=== Sistema de Búsqueda de Medicamentos en Difarmer ===")
   
    # Si se proporciona un argumento por línea de comandos, usarlo como nombre del medicamento
    if len(sys.argv) > 1:
        medicamento = " ".join(sys.argv[1:])
    else:
        # De lo contrario, pedir al usuario
        medicamento = input("Ingrese el nombre del medicamento a buscar: ")
   
    print(f"\nBuscando información sobre: {medicamento}")
    print("Espere un momento...\n")
   
    # Definir el modo headless basado en entorno
    import os
    # Si estamos en un entorno de servidor o container, usar headless=True, de lo contrario False para desarrollo
    headless = os.environ.get('ENVIRONMENT', 'production').lower() != 'development'
    
    # Buscar información del medicamento
    info = buscar_info_medicamento(medicamento, headless=headless)
   
    if info:
        # Guardar la información en un archivo JSON
        guardar_resultados(info)
    else:
        print("No se pudo encontrar información sobre el medicamento solicitado")
