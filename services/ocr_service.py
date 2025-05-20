"""
Servicio OCR para extraer texto de imágenes en SOPRIM BOT.
Utiliza Google Cloud Vision API para procesar imágenes recibidas por WhatsApp.
"""
import io
import logging
import requests
from google.cloud import vision
from google.cloud.vision_v1 import types
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OCRService:
    """
    Servicio para extraer texto de imágenes mediante OCR.
    """
    
    def __init__(self):
        """
        Inicializa el servicio OCR con Google Cloud Vision.
        Asume que las credenciales están configuradas mediante GOOGLE_APPLICATION_CREDENTIALS.
        """
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Servicio OCR inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar servicio OCR: {e}")
            self.client = None
    
    def download_image(self, image_url):
        """
        Descarga una imagen desde una URL.
        
        Args:
            image_url (str): URL de la imagen
            
        Returns:
            bytes: Contenido de la imagen en bytes o None si hay error
        """
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                logger.info(f"Imagen descargada con éxito: {len(response.content)} bytes")
                return response.content
            else:
                logger.error(f"Error al descargar imagen. Código: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error durante la descarga de la imagen: {e}")
            return None
    
    def extract_text_from_image(self, image_content):
        """
        Extrae texto de una imagen utilizando Google Cloud Vision.
        
        Args:
            image_content (bytes): Contenido de la imagen en bytes
            
        Returns:
            str: Texto extraído de la imagen o mensaje de error
        """
        if not self.client:
            return "Error: Servicio OCR no inicializado correctamente."
        
        try:
            # Crear imagen para Vision API
            image = types.Image(content=image_content)
            
            # Realizar detección de texto
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                logger.warning("No se detectó texto en la imagen")
                return ""
            
            # El primer texto contiene todo el contenido detectado
            detected_text = texts[0].description
            logger.info(f"Texto extraído de la imagen: {detected_text[:100]}...")
            return detected_text
            
        except Exception as e:
            logger.error(f"Error al extraer texto de la imagen: {e}")
            return f"Error al procesar la imagen: {str(e)}"
    
    async def process_image(self, image_url):
        """
        Procesa una imagen desde URL para extraer su texto.
        
        Args:
            image_url (str): URL de la imagen a procesar
            
        Returns:
            str: Texto extraído de la imagen o mensaje de error
        """
        try:
            # 1. Descargar la imagen
            image_content = self.download_image(image_url)
            if not image_content:
                return "No se pudo descargar la imagen para procesarla."
            
            # 2. Extraer texto
            extracted_text = self.extract_text_from_image(image_content)
            
            return extracted_text
        except Exception as e:
            logger.error(f"Error al procesar imagen: {e}")
            return f"Error al procesar la imagen: {str(e)}"
    
    async def process_images(self, image_urls):
        """
        Procesa múltiples imágenes y concatena el texto extraído.
        
        Args:
            image_urls (list): Lista de URLs de imágenes
            
        Returns:
            str: Texto combinado de todas las imágenes
        """
        if not image_urls:
            return ""
            
        all_text = []
        
        for url in image_urls:
            text = await self.process_image(url)
            if text and not text.startswith("Error"):
                all_text.append(text)
        
        return "\n\n".join(all_text)
