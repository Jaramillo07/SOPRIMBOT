"""
Servicio para interactuar con la API de Gemini.
Encapsula toda la lógica relacionada con la generación de respuestas de IA.
"""
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_SYSTEM_INSTRUCTIONS

class GeminiService:
    """
    Clase que proporciona métodos para interactuar con la API de Gemini.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de Gemini configurando la API key.
        """
        self.api_key = GEMINI_API_KEY
        self.model_name = GEMINI_MODEL
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, user_message):
        """
        Genera una respuesta basada en el mensaje del usuario utilizando Gemini.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            # Agregar contexto o instrucciones del sistema si es necesario
            prompt = f"{GEMINI_SYSTEM_INSTRUCTIONS}\n\nMensaje del cliente: {user_message}"
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"
    
    def generate_product_response(self, user_message, product_info):
        """
        Genera una respuesta basada en el mensaje del usuario y la información del producto.
        
        Args:
            user_message (str): Mensaje del usuario para procesar
            product_info (dict): Información del producto obtenida mediante scraping
            
        Returns:
            str: Respuesta generada por Gemini
        """
        try:
            # Crear un prompt enriquecido con la información del producto
            product_details = ""
            
            if product_info:
                product_details = f"""
                Información del producto encontrado:
                - Nombre: {product_info.get('nombre', 'No disponible')}
                - Laboratorio: {product_info.get('laboratorio', 'No disponible')}
                - Código de barras: {product_info.get('codigo_barras', 'No disponible')}
                - Registro sanitario: {product_info.get('registro_sanitario', 'No disponible')}
                - URL del producto: {product_info.get('url', 'No disponible')}
                """
            else:
                product_details = "No se encontró información específica sobre este producto en nuestra base de datos."
            
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}

Mensaje del cliente: {user_message}

{product_details}

Basándote en esta información, proporciona una respuesta útil y profesional al cliente sobre el producto solicitado.
Si no tienes información específica sobre la disponibilidad actual, responde que verificarás si el producto está disponible
y que el cliente puede consultar llamando a la farmacia o visitando la tienda.
"""
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Lo siento, hubo un error al procesar tu solicitud: {e}"