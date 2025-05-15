#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .settings import USERNAME, PASSWORD, BASE_URL, TIMEOUT, logger

def inicializar_navegador(headless=True):
    """
    Inicializa el navegador Chrome con opciones configuradas para entorno de servidor.
  
    Args:
        headless (bool): Si es True, el navegador se ejecuta en modo headless (sin interfaz gráfica)
       
    Returns:
        webdriver.Chrome: Instancia del navegador
    """
    options = Options()
    
    # Forzar modo headless en entorno de servidor
    options.add_argument("--headless=new")
    
    # Configuración adicional para entorno sin interfaz gráfica
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    
    # Configuración adicional para evitar errores comunes
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--single-process")
    
    # Agregar log level para debugging
    options.add_argument("--log-level=3")
    
    try:
        # Inicializar el navegador Chrome con service
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        try:
            # Intentar con webdriver-manager (preferido para desarrollo)
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("Navegador Chrome inicializado correctamente con webdriver-manager")
        except Exception as e:
            # Si falla, intentar con la ubicación predeterminada de Chrome en sistemas Linux
            logger.warning(f"Error al inicializar con webdriver-manager: {e}")
            logger.info("Intentando inicializar con ubicación predeterminada...")
            driver = webdriver.Chrome(options=options)
            logger.info("Navegador Chrome inicializado correctamente con ubicación predeterminada")
            
        return driver
    except Exception as e:
        logger.error(f"Error al inicializar el navegador: {e}")
        return None

def login_difarmer(headless=True):
    """
    Realiza el proceso de login en el sitio web de Difarmer.
   
    Args:
        headless (bool): Si es True, el navegador se ejecuta en modo headless
        
    Returns:
        webdriver.Chrome: Instancia del navegador con sesión iniciada o None si falla
    """
    driver = inicializar_navegador(headless=headless)  # Pasar el parámetro headless
    if not driver:
        logger.error("No se pudo inicializar el navegador. Abortando.")
        return None
   
    try:
        # 1. Navegar a la página principal
        logger.info(f"Navegando a: {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(3)  # Esperar a que cargue la página
       
        # 2. Buscar y hacer clic en el botón "Iniciar Sesion"
        try:
            logger.info("Buscando botón 'Iniciar Sesion'...")
           
            # Buscar específicamente por el texto "Iniciar Sesion" (con varias alternativas)
            login_buttons = driver.find_elements(By.XPATH,
                "//button[contains(., 'Iniciar Sesion')] | //a[contains(., 'Iniciar Sesion')] | "
                "//button[contains(., 'Iniciar Sesión')] | //a[contains(., 'Iniciar Sesión')]"
            )
           
            # Si no encontramos el botón específico, buscar por clase o estilo similar al de la imagen
            if not login_buttons:
                login_buttons = driver.find_elements(By.CSS_SELECTOR,
                    ".btn-primary, .btn-login, .login-button, button.blue-button, .difarmer-login-button"
                )
           
            # Última opción: buscar cualquier elemento con el texto 'iniciar sesion'
            if not login_buttons:
                login_buttons = driver.find_elements(By.XPATH,
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'iniciar sesion')]"
                )
           
            if login_buttons:
                logger.info(f"Botón 'Iniciar Sesion' encontrado")
                login_buttons[0].click()
                logger.info("Clic en 'Iniciar Sesion' realizado")
                time.sleep(2)  # Esperar a que aparezca el modal de login
               
            else:
                logger.warning("No se encontró botón 'Iniciar Sesion'. Verificando si ya estamos en la página de login...")
               
        except Exception as e:
            logger.warning(f"Error al buscar/hacer clic en botón de 'Iniciar Sesion': {e}")
            logger.info("Intentando continuar asumiendo que ya estamos en la página de login...")
       
        # 3. Buscar campo de usuario
        try:
            # Esperar un momento para que cargue el modal
            time.sleep(2)
        
            logger.info("Buscando campo de usuario...")
           
            # Intentar varias estrategias para encontrar el campo de usuario
            usuario_input = None
           
            # Buscar por placeholder "Usuario"
            username_fields = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Usuario']")
            if username_fields:
                usuario_input = username_fields[0]
                logger.info("Campo de usuario encontrado por placeholder")
           
            # Buscar por el primer campo de texto editable después de un label "Usuario"
            if not usuario_input:
                try:
                    user_labels = driver.find_elements(By.XPATH, "//label[text()='Usuario'] | //div[text()='Usuario']")
                    if user_labels:
                        # Buscar campos de entrada cercanos al label
                        nearby_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input:not([type])")
                        if nearby_inputs:
                            usuario_input = nearby_inputs[0]
                            logger.info("Campo de usuario encontrado por proximidad a label")
                except:
                    pass
           
            # Buscar el primer campo de entrada visible (último recurso)
            if not usuario_input:
                # Tomar todos los campos de entrada visibles
                all_inputs = driver.find_elements(By.CSS_SELECTOR, "input")
                visible_inputs = [input_field for input_field in all_inputs
                                if input_field.is_displayed()]
               
                if visible_inputs:
                    # El primer campo suele ser el usuario
                    usuario_input = visible_inputs[0]
                    logger.info("Usando primer campo de entrada visible como campo de usuario")
           
            # Si encontramos el campo, ingresar el usuario
            if usuario_input:
                usuario_input.clear()
                usuario_input.send_keys(USERNAME)
                logger.info(f"Usuario ingresado: {USERNAME}")
            else:
                logger.error("No se pudo encontrar el campo de usuario")
                driver.save_screenshot("error_no_campo_usuario.png")
                driver.quit()
                return None
           
            # 4. Buscar campo de contraseña
            logger.info("Buscando campo de contraseña...")
           
            # Buscar campo de tipo password
            password_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            password_input = None
           
            if password_fields:
                password_input = password_fields[0]
                logger.info("Campo de contraseña encontrado por tipo 'password'")
           
            # Si no encontramos por tipo, buscar por placeholder
            if not password_input:
                password_placeholders = driver.find_elements(By.CSS_SELECTOR, "input[placeholder='Contraseña']")
                if password_placeholders:
                    password_input = password_placeholders[0]
                    logger.info("Campo de contraseña encontrado por placeholder")
           
            # Si todavía no encontramos, buscar después de un label "Contraseña"
            if not password_input:
                try:
                    pwd_labels = driver.find_elements(By.XPATH, "//label[text()='Contraseña'] | //div[text()='Contraseña']")
                    if pwd_labels:
                        # Buscar campos de entrada cercanos al label
                        nearby_inputs = driver.find_elements(By.CSS_SELECTOR, "input")
                        if len(nearby_inputs) > 1:  # Asumiendo que el segundo campo es la contraseña
                            password_input = nearby_inputs[1]
                            logger.info("Campo de contraseña encontrado por proximidad a label")
                except:
                    pass
           
            # Si encontramos el campo, ingresar la contraseña
            if password_input:
                password_input.clear()
                password_input.send_keys(PASSWORD)
                logger.info("Contraseña ingresada")
            else:
                logger.error("No se pudo encontrar el campo de contraseña")
                driver.save_screenshot("error_no_campo_password.png")
                driver.quit()
                return None
           
            # 5. Buscar y hacer clic en el botón "Siguiente"
            logger.info("Buscando botón 'Siguiente'...")
           
            # Buscar botón con texto "Siguiente"
            siguiente_button = None
           
            # Por texto exacto
            siguiente_buttons = driver.find_elements(By.XPATH, "//button[text()='Siguiente']")
            if siguiente_buttons:
                siguiente_button = siguiente_buttons[0]
                logger.info("Botón 'Siguiente' encontrado por texto exacto")
           
            # Por contiene texto
            if not siguiente_button:
                siguiente_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Siguiente')]")
                if siguiente_buttons:
                    siguiente_button = siguiente_buttons[0]
                    logger.info("Botón 'Siguiente' encontrado por texto parcial")
           
            # Por clase similar a la mostrada en la imagen
            if not siguiente_button:
                siguiente_buttons = driver.find_elements(By.CSS_SELECTOR, ".btn-primary, .btn-login, .login-button, .difarmer-login-button")
                if siguiente_buttons:
                    siguiente_button = siguiente_buttons[0]
                    logger.info("Botón tipo 'Siguiente' encontrado por clase")
           
            # Si encontramos el botón, hacer clic
            if siguiente_button:
                siguiente_button.click()
                logger.info("Clic en botón 'Siguiente' realizado")
                time.sleep(5)  # Esperar a que se procese el login
            else:
                logger.error("No se pudo encontrar el botón 'Siguiente'")
                driver.save_screenshot("error_no_boton_siguiente.png")
                driver.quit()
                return None
           
            # 6. Verificar si el login fue exitoso
            current_url = driver.current_url
            logger.info(f"URL después de login: {current_url}")
           
            # Buscar indicadores de login exitoso
            success_indicators = [
                "mi cuenta" in driver.page_source.lower(),
                "cerrar sesión" in driver.page_source.lower(),
                "logout" in driver.page_source.lower(),
                "mi perfil" in driver.page_source.lower(),
                "bienvenido" in driver.page_source.lower(),
                "captura de pedidos" in driver.page_source.lower(),
                "carrito" in driver.page_source.lower(),
                bool(driver.find_elements(By.CSS_SELECTOR, ".user-profile, .logout-button, a[href*='logout'], .welcome-user, .user-menu"))
            ]
           
            # Determinar si el login fue exitoso
            login_exitoso = any(success_indicators)
           
            if login_exitoso:
                logger.info("¡LOGIN EXITOSO EN DIFARMER!")
                return driver
            else:
                logger.error("ERROR: Login en Difarmer fallido")
                driver.save_screenshot("error_login_fallido.png")
                driver.quit()
                return None
           
        except Exception as e:
            logger.error(f"Error durante el proceso de login: {e}")
            driver.save_screenshot("error_general_login.png")
            driver.quit()
            return None
           
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        if driver:
            driver.quit()
        return None
