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
    
    def format_whatsapp_number(self, phone_number):
        """
        Asegura que el número de teléfono tenga el formato correcto para WhatsApp API.
        Añade el signo "+" si no está presente.
        """
        # Eliminar cualquier espacio, guion u otro carácter no numérico excepto el "+"
        cleaned_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Asegurarse de que tiene el signo "+"
        if not cleaned_number.startswith('+'):
            cleaned_number = '+' + cleaned_number
            
        logger.info(f"WhatsAppService: Número formateado de {phone_number} a {cleaned_number}")
        return cleaned_number
    
    def is_allowed_number(self, phone_number):
        """
        Verifica si el número está en la lista de números permitidos para pruebas.
        """
        formatted_number = self.format_whatsapp_number(phone_number)
        is_allowed = formatted_number in ALLOWED_TEST_NUMBERS
        
        if not is_allowed:
            logger.warning(f"El número {formatted_number} no está en la lista de números permitidos para pruebas")
            logger.info(f"Números permitidos: {ALLOWED_TEST_NUMBERS}")
        
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
            # Formatear el número correctamente
            formatted_recipient = self.format_whatsapp_number(recipient)
            
            # Verificar si el número está permitido
            if not self.is_allowed_number(formatted_recipient):
                error_msg = f"No se puede enviar mensaje: el número {formatted_recipient} no está en la lista de números permitidos para pruebas"
                logger.error(error_msg)
                return {"error": error_msg, "sandbox_restriction": True}
            
            payload = {
                "messaging_product": "whatsapp",
                "to": formatted_recipient,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            logger.info(f"Enviando mensaje a {formatted_recipient}")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info(f"Mensaje enviado con éxito. Código: {response.status_code}")
            else:
                logger.error(f"Error al enviar mensaje. Código: {response.status_code}, Respuesta: {response_data}")
            
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
            # Formatear el número correctamente
            formatted_recipient = self.format_whatsapp_number(recipient)
            
            # Verificar si el número está permitido
            if not self.is_allowed_number(formatted_recipient):
                error_msg = f"No se puede enviar imagen: el número {formatted_recipient} no está en la lista de números permitidos para pruebas"
                logger.error(error_msg)
                return {"error": error_msg, "sandbox_restriction": True}
            
            payload = {
                "messaging_product": "whatsapp",
                "to": formatted_recipient,
                "type": "image",
                "image": {
                    "link": image_url
                }
            }
            
            # Agregar caption si se proporciona
            if caption:
                payload["image"]["caption"] = caption
            
            logger.info(f"Enviando imagen a {formatted_recipient}")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info(f"Imagen enviada con éxito. Código: {response.status_code}")
            else:
                logger.error(f"Error al enviar imagen. Código: {response.status_code}, Respuesta: {response_data}")
            
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
        
        # Si hay información del producto y tiene una imagen, enviarla también
        if product_info and product_info.get("imagen") and not text_result.get("sandbox_restriction"):
            image_url = product_info["imagen"]
            caption = f"Producto: {product_info.get('nombre', 'Medicamento')}"
            image_result = self.send_image_message(recipient, image_url, caption)
            results["image"] = image_result
        
        return results
