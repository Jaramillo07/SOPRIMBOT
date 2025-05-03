"""
Servicio para interactuar con la API de WhatsApp Business.
Encapsula toda la lógica relacionada con el envío de mensajes a través de WhatsApp.
"""
import requests
import logging
from config.settings import WHATSAPP_API_URL, WHATSAPP_TOKEN, ALLOWED_TEST_NUMBERS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Clase que proporciona métodos para interactuar con la API de WhatsApp Business.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de WhatsApp configurando la URL y el token.
        """
        self.api_url = WHATSAPP_API_URL
        self.token = WHATSAPP_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.info(f"WhatsAppService inicializado. API URL: {self.api_url}")
        logger.info(f"Números permitidos para pruebas: {ALLOWED_TEST_NUMBERS}")
    
    def format_phone_number(self, phone_number):
        """
        Formatea el número de teléfono para asegurar que tenga el formato correcto para WhatsApp API.
        
        Args:
            phone_number (str): Número de teléfono a formatear
            
        Returns:
            str: Número de teléfono formateado
        """
        # Eliminar caracteres no numéricos excepto el signo "+"
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Asegurar que tiene el signo "+"
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        logger.info(f"Número formateado: {phone_number} -> {cleaned}")
        return cleaned
    
    def format_phone_number_for_api(self, phone_number):
        """
        Formatea el número de teléfono para enviar a la API (sin el signo +).
        
        Args:
            phone_number (str): Número de teléfono a formatear
            
        Returns:
            str: Número de teléfono formateado para API
        """
        # Primero formateamos normalmente
        formatted = self.format_phone_number(phone_number)
        
        # Luego eliminamos el signo "+" para la API
        if formatted.startswith('+'):
            api_formatted = formatted[1:]
        else:
            api_formatted = formatted
            
        logger.info(f"Número formateado para API: {formatted} -> {api_formatted}")
        return api_formatted
    
    def is_allowed_number(self, phone_number):
        """
        Verifica si el número está en la lista de números permitidos para pruebas.
        
        Args:
            phone_number (str): Número de teléfono a verificar
            
        Returns:
            bool: True si está permitido, False en caso contrario
        """
        formatted_number = self.format_phone_number(phone_number)
        
        # Verificar tanto con el signo "+" como sin él
        is_allowed = formatted_number in ALLOWED_TEST_NUMBERS
        
        # Si no está permitido con el signo "+", verificar sin el signo
        if not is_allowed and formatted_number.startswith('+'):
            is_allowed = formatted_number[1:] in ALLOWED_TEST_NUMBERS
        
        if is_allowed:
            logger.info(f"Número {formatted_number} está en la lista de permitidos")
        else:
            logger.warning(f"Número {formatted_number} NO está en la lista de permitidos")
            logger.info(f"Números permitidos actuales: {ALLOWED_TEST_NUMBERS}")
        
        return is_allowed
    
    def send_text_message(self, recipient, message):
        """
        Envía un mensaje de texto a un número de WhatsApp.
        
        Args:
            recipient (str): Número de teléfono del destinatario (con formato internacional, ej. +5219871234567)
            message (str): Contenido del mensaje a enviar
            
        Returns:
            dict: Respuesta de la API de WhatsApp
        """
        try:
            # Formatear y verificar el número
            formatted_recipient = self.format_phone_number(recipient)
            
            # Verificar si el número está en la lista de permitidos
            if not self.is_allowed_number(formatted_recipient):
                error_msg = f"Error de sandbox: El número {formatted_recipient} no está en la lista de números permitidos"
                logger.error(error_msg)
                return {
                    "error": error_msg,
                    "sandbox_restriction": True,
                    "suggestion": "Añade este número a la lista de números de prueba en Meta Developer y pide al propietario que envíe un mensaje al bot"
                }
            
            # Formatear el número específicamente para la API (sin el signo +)
            api_recipient = self.format_phone_number_for_api(formatted_recipient)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": api_recipient,  # Usar la versión sin el signo "+"
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            logger.info(f"Enviando mensaje a {api_recipient}")
            logger.debug(f"Headers: {self.headers}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info(f"Mensaje enviado con éxito. Código: {response.status_code}")
            else:
                logger.error(f"Error al enviar mensaje. Código: {response.status_code}, Respuesta: {response_data}")
                
                # Detectar específicamente el error de número no permitido
                if response.status_code == 400 and "error" in response_data:
                    error_info = response_data.get("error", {})
                    if error_info.get("code") == 131030:
                        logger.error("Error de WhatsApp: Recipient phone number not in allowed list")
                        response_data["sandbox_restriction"] = True
                        response_data["suggestion"] = "Añade este número a la lista de números de prueba en Meta Developer"
            
            return response_data
        except Exception as e:
            logger.error(f"Excepción al enviar mensaje: {e}")
            return {"error": str(e)}
    
    def send_image_message(self, recipient, image_url, caption=None):
        """
        Envía una imagen a un número de WhatsApp.
        
        Args:
            recipient (str): Número de teléfono del destinatario (con formato internacional)
            image_url (str): URL de la imagen a enviar
            caption (str, optional): Texto descriptivo para la imagen
            
        Returns:
            dict: Respuesta de la API de WhatsApp
        """
        try:
            # Formatear y verificar el número
            formatted_recipient = self.format_phone_number(recipient)
            
            # Verificar si el número está en la lista de permitidos
            if not self.is_allowed_number(formatted_recipient):
                error_msg = f"Error de sandbox: El número {formatted_recipient} no está en la lista de números permitidos"
                logger.error(error_msg)
                return {
                    "error": error_msg,
                    "sandbox_restriction": True,
                    "suggestion": "Añade este número a la lista de números de prueba en Meta Developer y pide al propietario que envíe un mensaje al bot"
                }
            
            # Formatear el número específicamente para la API (sin el signo +)
            api_recipient = self.format_phone_number_for_api(formatted_recipient)
            
            payload = {
                "messaging_product": "whatsapp",
                "to": api_recipient,  # Usar la versión sin el signo "+"
                "type": "image",
                "image": {
                    "link": image_url
                }
            }
            
            # Agregar caption si se proporciona
            if caption:
                payload["image"]["caption"] = caption
            
            logger.info(f"Enviando imagen a {api_recipient}")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info(f"Imagen enviada con éxito. Código: {response.status_code}")
            else:
                logger.error(f"Error al enviar imagen. Código: {response.status_code}, Respuesta: {response_data}")
                
                # Detectar específicamente el error de número no permitido
                if response.status_code == 400 and "error" in response_data:
                    error_info = response_data.get("error", {})
                    if error_info.get("code") == 131030:
                        logger.error("Error de WhatsApp: Recipient phone number not in allowed list")
                        response_data["sandbox_restriction"] = True
                        response_data["suggestion"] = "Añade este número a la lista de números de prueba en Meta Developer"
            
            return response_data
        except Exception as e:
            logger.error(f"Excepción al enviar imagen: {e}")
            return {"error": str(e)}
    
    def send_product_response(self, recipient, text_response, product_info=None):
        """
        Envía una respuesta completa sobre un producto, incluyendo texto e imagen si está disponible.
        
        Args:
            recipient (str): Número de teléfono del destinatario
            text_response (str): Respuesta textual sobre el producto
            product_info (dict, optional): Información del producto que puede incluir una imagen
            
        Returns:
            dict: Resultado de la operación
        """
        results = {}
        
        # Siempre enviar la respuesta de texto
        text_result = self.send_text_message(recipient, text_response)
        results["text"] = text_result
        
        # Si hay restricción de sandbox, no intentar enviar la imagen
        if text_result.get("sandbox_restriction"):
            logger.warning("No se enviará imagen debido a restricción de sandbox")
            results["image"] = {"error": "No enviada por restricción de sandbox"}
            return results
        
        # Si hay información del producto y tiene una imagen, enviarla también
        if product_info and product_info.get("imagen"):
            image_url = product_info["imagen"]
            caption = f"Producto: {product_info.get('nombre', 'Medicamento')}"
            image_result = self.send_image_message(recipient, image_url, caption)
            results["image"] = image_result
        
        return results
