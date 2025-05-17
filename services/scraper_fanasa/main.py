#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo principal para el scraper de FANASA.
Proporciona funcionalidad para buscar información de productos en el portal FANASA Carrito.
"""

import time
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
USERNAME = "ventas@insumosjip.com"  # Usuario para FANASA
PASSWORD = "210407"                # Contraseña para FANASA
LOGIN_URL = "https://carrito.fanasa.com/login"  # URL del portal de carrito
TIMEOUT = 20                       # Tiempo de espera para elementos (segundos)

def inicializar_navegador(headless=True):
    """
    Inicializa el navegador Chrome con opciones configuradas.
    
    Args:
        headless (bool): Si es True, el navegador se ejecuta en modo headless (sin interfaz gráfica)
        
    Returns:
        webdriver.Chrome: Instancia del navegador
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    # Configuración adicional para mejorar la estabilidad
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Inicializar el navegador Chrome
        driver = webdriver.Chrome(options=options)
        logger.info("Navegador Chrome inicializado correctamente")
        return driver
    except Exception as e:
        logger.error(f"Error al inicializar el navegador: {e}")
        return None

def login_fanasa_carrito():
    """
    Realiza el proceso de login en el portal de carrito de FANASA.
    
    Returns:
        webdriver.Chrome: Instancia del navegador con sesión iniciada o None si falla
    """
    driver = inicializar_navegador(headless=True)  # Usar True para entorno de producción
    if not driver:
        logger.error("No se pudo inicializar el navegador. Abortando.")
        return None
    
    try:
        # 1. Navegar a la página de login
        logger.info(f"Navegando a la página de login: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        time.sleep(5)  # Esperar a que cargue la página
        
        # 2. Buscar campo de usuario
        logger.info("Buscando campo de usuario...")
        
        username_field = None
        username_selectors = [
            "input[placeholder='Usuario o correo']",
            "#email",  # Posible ID
            "input[type='email']",
            "input[type='text']:first-of-type",
            ".form-control:first-of-type"
        ]
        
        for selector in username_selectors:
            try:
                fields = driver.find_elements(By.CSS_SELECTOR, selector)
                for field in fields:
                    if field.is_displayed():
                        username_field = field
                        logger.info(f"Campo de usuario encontrado con selector: {selector}")
                        break
                if username_field:
                    break
            except:
                continue
        
        # Si no encontramos con los selectores específicos, buscar cualquier input visible
        if not username_field:
            try:
                # Buscar todos los inputs visibles
                inputs = driver.find_elements(By.TAG_NAME, "input")
                visible_inputs = [inp for inp in inputs if inp.is_displayed()]
                
                if visible_inputs:
                    # Primer input visible probablemente sea el de usuario
                    username_field = visible_inputs[0]
                    logger.info("Campo de usuario encontrado como primer input visible")
            except:
                pass
        
        # Si no se encuentra el campo de usuario, no podemos continuar
        if not username_field:
            logger.error("No se pudo encontrar el campo de usuario")
            driver.quit()
            return None
        
        # Limpiar e ingresar el usuario
        username_field.clear()
        username_field.send_keys(USERNAME)
        logger.info(f"Usuario ingresado: {USERNAME}")
        time.sleep(1)
        
        # 3. Buscar campo de contraseña
        logger.info("Buscando campo de contraseña...")
        
        password_field = None
        password_selectors = [
            "input[placeholder='Contraseña']",
            "#password",  # Posible ID
            "input[type='password']",
            "input.form-control[type='password']"
        ]
        
        for selector in password_selectors:
            try:
                fields = driver.find_elements(By.CSS_SELECTOR, selector)
                for field in fields:
                    if field.is_displayed():
                        password_field = field
                        logger.info(f"Campo de contraseña encontrado con selector: {selector}")
                        break
                if password_field:
                    break
            except:
                continue
        
        # Si no encontramos con selectores específicos, buscar por tipo password
        if not password_field:
            try:
                password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                if password_inputs:
                    for inp in password_inputs:
                        if inp.is_displayed():
                            password_field = inp
                            logger.info("Campo de contraseña encontrado por tipo 'password'")
                            break
            except:
                pass
        
        # Si no se encuentra el campo de contraseña, no podemos continuar
        if not password_field:
            logger.error("No se pudo encontrar el campo de contraseña")
            driver.quit()
            return None
        
        # Limpiar e ingresar la contraseña
        password_field.clear()
        password_field.send_keys(PASSWORD)
        logger.info("Contraseña ingresada")
        time.sleep(1)
        
        # 4. Buscar botón de inicio de sesión
        logger.info("Buscando botón 'Iniciar sesión'...")
        
        login_button = None
        button_selectors = [
            "button.btn-primary",  # Clase probable basada en la captura
            "button[type='submit']",
            "button:contains('Iniciar sesión')",
            ".btn-primary",
            ".btn-login"
        ]
        
        for selector in button_selectors:
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and "iniciar sesión" in button.text.lower():
                        login_button = button
                        logger.info(f"Botón 'Iniciar sesión' encontrado con selector: {selector}")
                        break
                if login_button:
                    break
            except:
                continue
        
        # Si no encontramos con CSS, intentar con XPath específico para el texto
        if not login_button:
            try:
                xpath_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ', 'abcdefghijklmnñopqrstuvwxyz'), 'iniciar sesión')]")
                if xpath_buttons:
                    for button in xpath_buttons:
                        if button.is_displayed():
                            login_button = button
                            logger.info("Botón 'Iniciar sesión' encontrado por texto")
                            break
            except:
                pass
        
        # Si no se encuentra un botón específico, buscar cualquier botón visible
        if not login_button:
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    if button.is_displayed() and button.is_enabled():
                        login_button = button
                        logger.info("Usando primer botón visible como botón de login")
                        break
            except:
                pass
        
        # Si no se encuentra el botón, intentar enviar el formulario con Enter
        if not login_button:
            logger.warning("No se encontró botón de inicio de sesión. Intentando enviar formulario con Enter.")
            password_field.send_keys(Keys.RETURN)
            time.sleep(5)
        else:
            # Hacer clic en el botón
            try:
                # Asegurar que el botón sea visible
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", login_button)
                time.sleep(1)
                
                # Hacer clic
                login_button.click()
                logger.info("Clic en botón 'Iniciar sesión' realizado")
                
            except ElementClickInterceptedException:
                # Si hay algo interceptando el clic, intentar con JavaScript
                logger.warning("Clic interceptado. Intentando con JavaScript.")
                driver.execute_script("arguments[0].click();", login_button)
                logger.info("Clic en botón realizado con JavaScript")
            
            time.sleep(5)  # Esperar a que se procese el login
        
        # 5. Verificar si el login fue exitoso
        current_url = driver.current_url
        logger.info(f"URL actual después del intento de login: {current_url}")
        
        # Verificar si ya no estamos en la página de login
        login_exitoso = "/login" not in current_url
        
        # También verificar si hay indicadores de sesión iniciada
        if not login_exitoso:
            page_text = driver.page_source.lower()
            success_indicators = [
                "cerrar sesión" in page_text,
                "logout" in page_text,
                "mi cuenta" in page_text,
                "carrito" in page_text and not "/login" in current_url
            ]
            
            login_exitoso = any(success_indicators)
        
        # Verificar si hay mensajes de error visibles
        has_error = False
        try:
            error_messages = driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, .text-danger")
            for error in error_messages:
                if error.is_displayed():
                    has_error = True
                    logger.error(f"Mensaje de error detectado: {error.text}")
                    break
        except:
            pass
        
        # Resultado final
        if login_exitoso and not has_error:
            logger.info("¡LOGIN EXITOSO EN FANASA CARRITO!")
            return driver
        else:
            logger.error("ERROR: Login en FANASA Carrito fallido")
            
            if has_error:
                logger.error("Se detectaron mensajes de error en la página")
            
            driver.quit()
            return None
        
    except Exception as e:
        logger.error(f"Error durante el proceso de login: {e}")
        if driver:
            driver.quit()
        return None

# SKU / CÓDIGO DE PRODUCTO
        try:
            # Buscar elementos que contengan "SKU" o "Código"
            try:
                sku_elements = driver.find_elements(By.XPATH, 
                    "//*[contains(text(), 'SKU') or contains(text(), 'Código') or contains(text(), 'Codigo')]/following::*")
                
                for element in sku_elements:
                    if element.is_displayed():
                        texto = element.text.strip()
                        # Los SKUs generalmente son números largos
                        sku_match = re.search(r'\b(\d{7,})\b', texto)
                        if sku_match:
                            info_producto['sku'] = sku_match.group(1)
                            logger.info(f"SKU: {info_producto['sku']}")
                            break
                        # Si no hay número largo pero contiene un patrón alfanumérico que podría ser un código
                        elif re.match(r'^[A-Za-z0-9-]+', texto) and len(texto) >= 5:
                            info_producto['sku'] = texto
                            logger.info(f"SKU (alfanumérico): {info_producto['sku']}")
                            break
            except:
                pass


def buscar_info_medicamento(nombre_medicamento, headless=True):
    """
    Función principal que busca información de un medicamento en FANASA.
    
    Args:
        nombre_medicamento (str): Nombre del medicamento a buscar
        headless (bool): Si es True, el navegador se ejecuta en modo headless
        
    Returns:
        dict: Diccionario con la información del medicamento o None si no se encuentra
    """
    driver = None
    try:
        # 1. Iniciar sesión en FANASA
        logger.info(f"Iniciando proceso para buscar información sobre: '{nombre_medicamento}'")
        
        driver = login_fanasa_carrito()
        if not driver:
            logger.error("No se pudo iniciar sesión en FANASA. Abortando búsqueda.")
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
        
        # Añadir la fuente para integración con el servicio principal
        if info_producto:
            info_producto['fuente'] = 'FANASA'
            # Compatibilidad para trabajar con el servicio de orquestación
            info_producto['existencia'] = '0'
            if info_producto['disponibilidad']:
                # Extraer números de la disponibilidad si existe
                stock_match = re.search(r'(\d+)', info_producto['disponibilidad'])
                if stock_match:
                    info_producto['existencia'] = stock_match.group(1)
                elif 'disponible' in info_producto['disponibilidad'].lower():
                    info_producto['existencia'] = 'Si'
        
        return info_producto
        
    except Exception as e:
        logger.error(f"Error general durante el proceso: {e}")
        return None
    finally:
        if driver:
            logger.info("Cerrando navegador...")
            driver.quit()

# Para ejecución directa como script independiente
if __name__ == "__main__":
    import sys
    
    print("=== Sistema de Búsqueda de Medicamentos en FANASA ===")
    
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
    headless = os.environ.get('ENVIRONMENT', 'production').lower() != 'development'
    
    # Buscar información del medicamento
    info = buscar_info_medicamento(medicamento, headless=headless)
    
    if info:
        print("\n=== INFORMACIÓN DEL PRODUCTO ===")
        print(f"Nombre: {info.get('nombre', 'No disponible')}")
        print(f"Precio Neto: {info.get('precio_neto', 'No disponible')}")
        print(f"PMP: {info.get('pmp', 'No disponible')}")
        print(f"Laboratorio: {info.get('laboratorio', 'No disponible')}")
        print(f"SKU: {info.get('sku', 'No disponible')}")
        print(f"Disponibilidad: {info.get('disponibilidad', 'No disponible')}")
        if info.get('imagen'):
            print(f"Imagen: {info['imagen']}")
        print(f"URL: {info['url']}")
        
        # Preguntar si desea guardar la información en un archivo
        guardar = input("\n¿Deseas guardar esta información en un archivo? (s/n): ").lower()
        if guardar == 's':
            try:
                import json
                from datetime import datetime
                
                fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"{info['nombre']}_{fecha_hora}.json".replace(" ", "_").replace("/", "_")
                
                with open(nombre_archivo, "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=4)
                
                print(f"\n✅ Información guardada en el archivo: {nombre_archivo}")
            except Exception as e:
                print(f"\n❌ Error al guardar información: {e}")
    else:
        print("No se pudo encontrar información sobre el medicamento solicitado")
