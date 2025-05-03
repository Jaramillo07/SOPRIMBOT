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
            # Formatear el número
            formatted_recipient = self.format_phone_number(recipient)
            
            # Nota: Se ha eliminado la verificación de números permitidos ya que estamos en producción
            
            payload = {
                "messaging_product": "whatsapp",
                "to": formatted_recipient,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            logger.info(f"Enviando mensaje a {formatted_recipient}")
            logger.debug(f"Headers: {self.headers}")
            logger.debug(f"Payload: {payload}")
            
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
            # Formatear el número
            formatted_recipient = self.format_phone_number(recipient)
            
            # Nota: Se ha eliminado la verificación de números permitidos ya que estamos en producción
            
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
        if product_info and product_info.get("imagen"):
            image_url = product_info["imagen"]
            caption = f"Producto: {product_info.get('nombre', 'Medicamento')}"
            image_result = self.send_image_message(recipient, image_url, caption)
            results["image"] = image_result
        
        return results
