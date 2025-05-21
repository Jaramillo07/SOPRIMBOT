"""
Servicio para interactuar con Google Sheets como base de datos interna.
Proporciona funcionalidades para buscar productos en la hoja de cálculo
antes de recurrir a los scrapers.
"""
import os
import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

# Importaciones para Google Sheets
import google.auth
import gspread
from google.oauth2 import service_account

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SheetsService:
    """
    Servicio para interactuar con la base de datos interna en Google Sheets.
    Proporciona métodos para buscar productos por nombre o código.
    """
    
    def __init__(self):
        """
        Inicializa el servicio de Google Sheets utilizando las credenciales
        predeterminadas del entorno o un archivo específico.
        """
        # Inicializar variables críticas PRIMERO, antes de cualquier código que pueda fallar
        self.data = []
        self.last_refresh = 0
        self.cache_ttl = 300  # Segundos de validez del caché (5 minutos)
        self.sheet_id = None
        self.client = None
        self.spreadsheet = None
        self.sheet = None
        
        try:
            # ID de la hoja de cálculo (extraído de la URL)
            self.sheet_id = os.getenv('SHEETS_ID')
            if not self.sheet_id:
                logger.warning("SHEETS_ID no está configurado en las variables de entorno")
                return
            
            # Definir el alcance (scope) para la autenticación
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Usar Autenticación Predeterminada de Aplicaciones (ADC)
            try:
                credentials, project = google.auth.default(scopes=scopes)
                logger.info(f"Usando credenciales predeterminadas del proyecto: {project}")
            except Exception as e:
                logger.error(f"Error al cargar credenciales predeterminadas: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return
            
            # Inicializar cliente y conectar a la hoja
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            self.sheet = self.spreadsheet.sheet1  # Primera hoja por defecto
            
            # Cargar datos iniciales
            self.refresh_cache_if_needed(force=True)
            
            logger.info(f"SheetsService inicializado correctamente. Cargados {len(self.data)} productos.")
        except Exception as e:
            logger.error(f"Error al inicializar SheetsService: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def refresh_cache_if_needed(self, force=False) -> bool:
        """
        Actualiza el caché de datos si es necesario o si se fuerza.
        
        Args:
            force (bool): Si es True, fuerza la actualización sin importar el TTL
            
        Returns:
            bool: True si se actualizó el caché, False si no fue necesario o hubo error
        """
        current_time = time.time()
        
        # Si no es forzado y el caché aún es válido, no hacer nada
        if not force and (current_time - self.last_refresh) < self.cache_ttl:
            return False
        
        # Verificar que tengamos una conexión a la hoja
        if not self.sheet:
            logger.error("No hay conexión a la hoja de cálculo, no se puede actualizar caché")
            return False
        
        try:
            self.data = self.sheet.get_all_records()
            self.last_refresh = current_time
            logger.info(f"Caché actualizado: {len(self.data)} registros cargados")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar caché: {e}")
            return False
    
    def normalize_product_name(self, product_name: str) -> str:
        """
        Normaliza el nombre de un producto para búsquedas más consistentes.
        
        Args:
            product_name (str): Nombre del producto a normalizar
            
        Returns:
            str: Nombre del producto normalizado
        """
        if not product_name:
            return ""
        
        # Convertir a minúsculas
        normalized = product_name.lower()
        
        # Eliminar artículos y palabras comunes al inicio
        words_to_remove = ["el ", "la ", "los ", "las ", "un ", "una ", "unos ", "unas ", "de ", "del "]
        for word in words_to_remove:
            if normalized.startswith(word):
                normalized = normalized[len(word):]
        
        # Eliminar caracteres especiales y espacios múltiples
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Normalizar nombres comunes de medicamentos y sus variantes
        replacements = {
            "acido": "ácido",
            "acetato": "ac",
            "capsulas": "cap",
            "tabletas": "tab",
            "solucion": "sol",
            "inyectable": "iny",
            "miligramos": "mg",
            "mililitros": "ml",
            "microgramos": "mcg"
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def calculate_similarity(self, query: str, target: str) -> float:
        """
        Calcula la similitud entre dos cadenas de texto.
        Usa un enfoque híbrido de palabras coincidentes y posición.
        
        Args:
            query (str): Consulta normalizada
            target (str): Texto objetivo normalizado
            
        Returns:
            float: Puntuación de similitud entre 0 y 1
        """
        if not query or not target:
            return 0.0
        
        # Convertir a conjuntos de palabras
        query_words = set(query.split())
        target_words = set(target.split())
        
        # Si no hay palabras, no hay similitud
        if not query_words or not target_words:
            return 0.0
        
        # Calcular intersección
        common_words = query_words.intersection(target_words)
        
        # Calcular puntuación base por palabras coincidentes
        score = len(common_words) / max(len(query_words), len(target_words))
        
        # Bonificación por coincidencia al inicio
        if target.startswith(query[:min(5, len(query))]):
            score += 0.2
        
        # Bonificación por longitud similar (max 0.1)
        len_ratio = min(len(query), len(target)) / max(len(query), len(target))
        score += len_ratio * 0.1
        
        # Limitar puntuación a 1.0 máximo
        return min(score, 1.0)
    
    def search_product(self, product_name: str, threshold: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Busca un producto en los datos de la hoja usando coincidencia parcial
        y comparación de similitud.
        
        Args:
            product_name (str): Nombre del producto a buscar
            threshold (float): Umbral de similitud (0-1)
            
        Returns:
            dict or None: Producto encontrado o None
        """
        # Asegurar que los datos estén actualizados
        self.refresh_cache_if_needed()
        
        if not product_name or not self.data:
            logger.warning(f"[DEBUG] No hay búsqueda posible: producto='{product_name}', datos={len(self.data)}")
            return None
        
        normalized_query = self.normalize_product_name(product_name)
        if not normalized_query:
            logger.warning(f"[DEBUG] Búsqueda normalizada vacía para: '{product_name}'")
            return None
        
        logger.info(f"[DEBUG] Búsqueda normalizada: '{normalized_query}' (original: '{product_name}')")
        
        # Dividir en palabras para búsqueda por tokens
        query_words = set(normalized_query.split())
        
        # Mantener mejor coincidencia
        best_match = None
        best_score = 0
        
        for product in self.data:
            desc = product.get('DESCRIPCION', '')
            if not desc:
                continue
                
            normalized_desc = self.normalize_product_name(desc)
            
            # Verificar coincidencia exacta primero
            if normalized_query == normalized_desc:
                logger.info(f"[DEBUG] Coincidencia EXACTA encontrada: '{desc}'")
                return product
                
            # Si no es exacta, calcular similitud
            score = self.calculate_similarity(normalized_query, normalized_desc)
            
            # Bonus para código/clave coincidente
            product_code = str(product.get('CLAVE', '')).lower()
            if product_code and normalized_query == product_code:
                score += 0.5
                logger.info(f"[DEBUG] Bonus por código coincidente: {product_code}")
                
            # Debug para puntuaciones altas
            if score > 0.5:
                logger.info(f"[DEBUG] Puntuación alta ({score:.2f}): '{desc}' para consulta '{normalized_query}'")
                
            # Actualizar mejor coincidencia si supera el umbral y la puntuación anterior
            if score > best_score and score >= threshold:
                best_score = score
                best_match = product
        
        if best_match:
            logger.info(f"[DEBUG] Mejor coincidencia ({best_score:.2f}): '{best_match.get('DESCRIPCION', '')}'")
        else:
            logger.info(f"[DEBUG] No se encontraron coincidencias que superen el umbral ({threshold}) para '{normalized_query}'")
        
        return best_match
    
    def format_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea los datos del producto de la hoja de cálculo al formato
        estándar utilizado por el bot.
        
        Args:
            product_data (dict): Datos del producto de la hoja
            
        Returns:
            dict: Producto formateado
        """
        # Extraer y formatear precio
        price = product_data.get('PRECIO', 0)
        if isinstance(price, str) and price.startswith('$'):
            price_str = price.strip()
        else:
            price_str = f"${float(price):.2f}" if price else "$0.00"
        
        # Extraer valor numérico del precio para ordenamiento
        price_value = 0.0
        try:
            if isinstance(price, (int, float)):
                price_value = float(price)
            elif isinstance(price, str):
                # Eliminar símbolos de moneda y convertir
                clean_price = price.replace('$', '').replace(',', '').strip()
                price_value = float(clean_price)
        except (ValueError, TypeError):
            pass
        
        # Extraer y formatear existencia
        stock = product_data.get('EXISTENCIA', 0)
        stock_value = 0
        try:
            stock_value = int(float(stock))
        except (ValueError, TypeError):
            # Si no es número, verificar si es texto que indica disponibilidad
            if isinstance(stock, str) and any(word in stock.lower() for word in ['si', 'disponible']):
                stock_value = 1
        
        # Crear el objeto producto estandarizado
        return {
            "nombre": product_data.get('DESCRIPCION', ''),
            "codigo_barras": str(product_data.get('CLAVE', '')),
            "laboratorio": product_data.get('LABORATORIO', ''),
            "registro_sanitario": product_data.get('REGISTRO', ''),
            "precio": price_str,
            "existencia": str(stock_value),
            "existencia_numerica": stock_value,
            "precio_numerico": price_value,
            "fuente": "Base Interna",
            "nombre_farmacia": "SOPRIM",
            "estado": "encontrado"
        }
    
    def buscar_producto(self, nombre_producto: str, threshold: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Método principal para buscar un producto en la base de datos interna.
        Interfaz unificada para el handler principal.
        
        Args:
            nombre_producto (str): Nombre del producto a buscar
            threshold (float): Umbral de similitud (0-1)
            
        Returns:
            dict or None: Información del producto encontrado o None
        """
        try:
            # Si no hay hoja configurada, retornar None inmediatamente
            if not self.sheet_id:
                logger.warning("[DEBUG] No hay hoja de cálculo configurada. Omitiendo búsqueda interna.")
                return None
            
            logger.info(f"[DEBUG] Iniciando búsqueda para: '{nombre_producto}' con umbral {threshold}")
            
            # Buscar el producto
            producto = self.search_product(nombre_producto, threshold)
            
            if producto:
                # Formatear al estándar del bot
                resultado = self.format_product(producto)
                logger.info(f"[DEBUG] Producto encontrado en base interna: {resultado['nombre']} (similitud >= {threshold})")
                return resultado
            
            logger.info(f"[DEBUG] No se encontró '{nombre_producto}' en la base interna (umbral: {threshold})")
            return None
        except Exception as e:
            logger.error(f"[DEBUG] Error buscando producto '{nombre_producto}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Busca un producto por su código o clave exacta.
        
        Args:
            codigo (str): Código del producto a buscar
            
        Returns:
            dict or None: Información del producto encontrado o None
        """
        try:
            # Asegurar que los datos estén actualizados
            self.refresh_cache_if_needed()
            
            # Normalizar código
            codigo_norm = str(codigo).strip().upper()
            
            # Búsqueda exacta por código
            for producto in self.data:
                producto_codigo = str(producto.get('CLAVE', '')).strip().upper()
                if producto_codigo == codigo_norm:
                    resultado = self.format_product(producto)
                    logger.info(f"Producto encontrado por código '{codigo}': {resultado['nombre']}")
                    return resultado
            
            logger.info(f"No se encontró producto con código '{codigo}' en la base interna")
            return None
        except Exception as e:
            logger.error(f"Error buscando producto por código '{codigo}': {e}")
            return None
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos de la base de datos.
        
        Returns:
            list: Lista de productos formateados
        """
        try:
            # Asegurar que los datos estén actualizados
            self.refresh_cache_if_needed()
            
            # Formatear y retornar todos los productos
            return [self.format_product(p) for p in self.data]
        except Exception as e:
            logger.error(f"Error obteniendo todos los productos: {e}")
            return []
    
    def get_products_with_stock(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos con existencia positiva.
        
        Returns:
            list: Lista de productos con stock, formateados
        """
        try:
            # Asegurar que los datos estén actualizados
            self.refresh_cache_if_needed()
            
            # Filtrar productos con existencia > 0
            productos_con_stock = []
            for p in self.data:
                try:
                    existencia = float(p.get('EXISTENCIA', 0))
                    if existencia > 0:
                        productos_con_stock.append(self.format_product(p))
                except (ValueError, TypeError):
                    # Verificar si la existencia es texto que indica disponibilidad
                    existencia_str = str(p.get('EXISTENCIA', '')).lower()
                    if any(word in existencia_str for word in ['si', 'disponible']):
                        productos_con_stock.append(self.format_product(p))
            
            return productos_con_stock
        except Exception as e:
            logger.error(f"Error obteniendo productos con stock: {e}")
            return []
