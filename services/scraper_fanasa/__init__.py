"""
Paquete scraper_fanasa para SOPRIM BOT.
Proporciona funcionalidad para extraer información de productos farmacéuticos del portal FANASA.
"""

from .main import buscar_info_medicamento, login_fanasa_carrito, buscar_producto, extraer_info_producto

# Exposición de funciones principales para importación directa
__all__ = ['buscar_info_medicamento', 'login_fanasa_carrito', 'buscar_producto', 'extraer_info_producto']