"""
Servicio para interactuar con la API de Gemini.
VERSIÓN CORREGIDA: Mejor manejo de contexto, cantidad, e identificación de intención.
Incluye lógica para identificar producto principal de OCR.
ACTUALIZADO: Aplicación de márgenes de ganancia por proveedor.
"""
import logging
import re
import json
import traceback 
import google.generativeai as genai

# ✅ IMPORTAR FUNCIONES DE MÁRGENES
from config.settings import (
    GEMINI_API_KEY, 
    GEMINI_MODEL, 
    GEMINI_SYSTEM_INSTRUCTIONS,
    extraer_precio_numerico,
    calcular_precio_con_margen,
    formatear_precio_mexicano,
    MARGENES_GANANCIA
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeminiService:
    """
    Clase que proporciona métodos para interactuar con la API de Gemini.
    """
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model_name = GEMINI_MODEL
        
        api_key_preview = self.api_key[:4] + "..." if self.api_key and len(self.api_key) > 8 else "No disponible"
        logger.info(f"Inicializando GeminiService con modelo: {self.model_name}")
        logger.info(f"API Key (primeros caracteres): {api_key_preview}")
        
        try:
            genai.configure(api_key=self.api_key)
            self.safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            self.model = genai.GenerativeModel(self.model_name, safety_settings=self.safety_settings)
            logger.info(f"Modelo Gemini ({self.model_name}) inicializado correctamente con safety_settings ajustados.")
        except Exception as e:
            logger.error(f"Error al inicializar el modelo Gemini: {e}\n{traceback.format_exc()}")
            raise
    
    def _format_conversation_history(self, history):
        if not history:
            return "No hay historial previo."
        
        formatted_history = ""
        recent_history = history[-6:] 
        for turn in recent_history:
            role = turn.get("role", "").lower()
            content = turn.get("content", "")
            if role and content:
                if role == "user":
                    formatted_history += f"Usuario: {content}\n"
                elif role in ["assistant", "bot", "model"]: 
                    formatted_history += f"Bot: {content}\n"
        
        return formatted_history.strip() if formatted_history else "No hay historial previo relevante."

    def analizar_contexto_con_gemini(self, user_message, conversation_history, is_ocr_text=False): # Nuevo parámetro
        historial_formateado = self._format_conversation_history(conversation_history)
        
        tarea_especifica = "analiza la intención principal del usuario."
        json_output_fields = """
  "tipo_consulta": "string",
  "producto_contexto_anterior": "string_o_null",
  "productos_mencionados_ahora": ["string_o_null"],
  "producto_principal_ocr": null,
  "es_pregunta_sobre_producto": true/false,
  "cantidad_solicitada": "integer_o_null",
  "frase_clave_accion": "string_o_null"
"""
        instrucciones_productos_mencionados = """
- **"productos_mencionados_ahora":** Lista de nombres de productos que el usuario haya escrito EXPLÍCITAMENTE en su mensaje de texto. NO intentes listar aquí productos que solo aparecen en una anotación de imagen como "[Texto de imagen]: ...". Si el usuario solo envió una imagen sin texto adicional, o si su texto no menciona productos explícitamente, esta lista debe ser `[]`.
- **"producto_principal_ocr":** Este campo es SOLO para cuando el `MENSAJE ACTUAL DEL USUARIO` contiene una anotación como "[Texto de imagen]: ...". En ese caso, del texto DENTRO de esa anotación de imagen, extrae el nombre del producto más completo, prominente o específico que consideres el candidato principal para una búsqueda. Por ejemplo, de "[Texto de imagen]: KitosCell LP Pirfenidona Tabletas 600 mg", un buen candidato sería "KitosCell LP 600 mg" o "Kitoscell LP". Si hay una lista clara en la imagen, elige el primer ítem más completo. Si no hay texto de imagen o no puedes determinar uno claro, devuelve `null`."""
        
        ejemplos_especificos = """
1. Usuario: "Tienes paracetamol y losartan?"
   JSON: {{"tipo_consulta": "consulta_producto_nuevo", "producto_contexto_anterior": null, "productos_mencionados_ahora": ["paracetamol", "losartan"], "producto_principal_ocr": null, "es_pregunta_sobre_producto": true, "cantidad_solicitada": null, "frase_clave_accion": "Tienes paracetamol y losartan?"}}
2. Bot: "Claro, para el paracetamol, ¿cuántas unidades necesitas?"
   Usuario: "unas 2 cajas"
   JSON: {{"tipo_consulta": "consulta_cantidad", "producto_contexto_anterior": "paracetamol", "productos_mencionados_ahora": [], "producto_principal_ocr": null, "es_pregunta_sobre_producto": true, "cantidad_solicitada": 2, "frase_clave_accion": "unas 2 cajas"}}
3. Usuario: "[Texto de imagen]: Kitoscell LP\\nPirfenidona 600 mg\\nAnalgen 10 tabs" (Solo imagen, sin texto adicional del usuario)
   JSON: {{"tipo_consulta": "consulta_producto_nuevo", "producto_contexto_anterior": null, "productos_mencionados_ahora": [], "producto_principal_ocr": "Kitoscell LP", "es_pregunta_sobre_producto": true, "cantidad_solicitada": null, "frase_clave_accion": null}}
4. Usuario: "Busca esto porfa [Texto de imagen]: KitosCell Pirfenidona 600 mg. También necesito aspirina"
   JSON: {{"tipo_consulta": "consulta_producto_nuevo", "producto_contexto_anterior": null, "productos_mencionados_ahora": ["aspirina"], "producto_principal_ocr": "KitosCell Pirfenidona 600 mg", "es_pregunta_sobre_producto": true, "cantidad_solicitada": null, "frase_clave_accion": "Busca esto porfa"}}
5. Usuario (mensaje podría incluir texto de OCR de receta): "[Texto de imagen]: - DOXORRUBICINA 50mg, 2 AMP.\\n- CICLOFOSFAMIDA 1000mg 1 AMP.]"
    JSON: {{"tipo_consulta": "consulta_producto_nuevo", "producto_contexto_anterior": null, "productos_mencionados_ahora": [], "producto_principal_ocr": "DOXORRUBICINA 50mg, 2 AMP.", "es_pregunta_sobre_producto": true, "cantidad_solicitada": null, "frase_clave_accion": null}}
"""

        if is_ocr_text: # Ajusta la tarea si el mensaje contiene texto de OCR.
            tarea_especifica = "el MENSAJE ACTUAL DEL USUARIO contiene texto extraído de una imagen (anotado como '[Texto de imagen]: ...'). Tu tarea principal es identificar el nombre del producto más prominente o completo en ESE TEXTO DE IMAGEN para una búsqueda. También identifica si el usuario escribió algún producto adicional fuera de la anotación de la imagen."
            # Los json_output_fields y ejemplos ya están preparados para "producto_principal_ocr".
            # Las instrucciones para "productos_mencionados_ahora" y "producto_principal_ocr" ya diferencian su origen.

        prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}

**Tarea de Análisis de Consulta Específica:**
Basado en el HISTORIAL PREVIO y el MENSAJE ACTUAL DEL USUARIO, {tarea_especifica}

**HISTORIAL PREVIO:**
{historial_formateado}

**MENSAJE ACTUAL DEL USUARIO:** "{user_message}"

**Analiza y responde SOLAMENTE en el siguiente formato JSON:**
{{{json_output_fields}
}}

**Instrucciones Detalladas para el JSON:**
- **"tipo_consulta":** Categoriza la intención principal del usuario a partir de su texto escrito o la naturaleza de la imagen si es el único input. Si el usuario envía una imagen de un producto, el `tipo_consulta` es "consulta_producto_nuevo".
    (Valores posibles: "consulta_producto_nuevo", "consulta_cantidad", "confirmacion_pedido", "solicitud_direccion_contacto", "pregunta_general_farmacia", "pregunta_sobre_producto_en_contexto", "saludo", "despedida", "agradecimiento", "queja_problema", "respuesta_a_pregunta_bot", "no_entiendo_o_irrelevante")
- **"producto_contexto_anterior":** Nombre del producto discutido PREVIAMENTE.
{instrucciones_productos_mencionados}
- **"es_pregunta_sobre_producto":** true si la intención general es saber sobre un producto. Si se envía una imagen de producto, esto es `true`.
- **"cantidad_solicitada":** Cantidad numérica si se especifica en el texto del usuario.
- **"frase_clave_accion":** Frase clave del texto del usuario si aplica.

**Ejemplos de Respuesta JSON:**
{ejemplos_especificos}
Analiza cuidadosamente y proporciona SOLAMENTE el JSON. Asegúrate que todos los campos del JSON estén presentes, usando `null` si un campo de string no aplica, o `[]` para listas vacías.
"""
        logger.debug(f"Enviando prompt a Gemini para análisis de contexto (is_ocr_text={is_ocr_text}, longitud: {len(prompt)}): {prompt[:600]}...")
        default_fallback_response = {
            "tipo_consulta": "no_entiendo_o_irrelevante", "producto_contexto_anterior": None,
            "productos_mencionados_ahora": [], 
            "producto_principal_ocr": None, 
            "es_pregunta_sobre_producto": False,
            "cantidad_solicitada": None, "frase_clave_accion": None
        }
        try:
            response = self.model.generate_content(prompt)
            resp_text = ""
            if response.parts:
                resp_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text'):
                resp_text = response.text
            
            resp_text = resp_text.strip()
            logger.info(f"Respuesta de análisis de contexto Gemini (raw): {resp_text}")

            json_match = re.search(r'\{[\s\S]*\}', resp_text) 
            if json_match:
                json_str = json_match.group(0)
                try:
                    resultado = json.loads(json_str)
                    for key, default_val in default_fallback_response.items():
                        resultado.setdefault(key, default_val)
                    
                    productos_ahora = resultado.get("productos_mencionados_ahora", [])
                    if isinstance(productos_ahora, str):
                        productos_ahora = [productos_ahora] if productos_ahora and productos_ahora.lower() != "null" else []
                    elif not isinstance(productos_ahora, list):
                        productos_ahora = []
                    resultado["productos_mencionados_ahora"] = [p for p in productos_ahora if isinstance(p, str) and p.strip() and p.strip().lower() != "null"]

                    prod_ocr = resultado.get("producto_principal_ocr")
                    if not isinstance(prod_ocr, str) or (isinstance(prod_ocr, str) and prod_ocr.lower() == "null"):
                        resultado["producto_principal_ocr"] = None
                    elif isinstance(prod_ocr, str):
                         resultado["producto_principal_ocr"] = prod_ocr.strip()

                    logger.info(f"📊 Análisis de contexto Gemini (procesado): {resultado}")
                    return resultado
                except json.JSONDecodeError as je:
                    logger.error(f"Error decodificando JSON de Gemini: {je} - Respuesta: {json_str}")
            else:
                logger.warning(f"⚠️ No se pudo extraer JSON de la respuesta de análisis de contexto: {resp_text}")
            
        except Exception as e:
            logger.error(f"❌ Error severo en análisis de contexto con Gemini: {e}\n{traceback.format_exc()}")

        return default_fallback_response
    
    def generate_response(self, user_message, conversation_history=None):
        try:
            historial_formateado = self._format_conversation_history(conversation_history)
            
            prompt = f"""{GEMINI_SYSTEM_INSTRUCTIONS}

Considerando el siguiente intercambio:
HISTORIAL PREVIO:
{historial_formateado}

MENSAJE ACTUAL DEL USUARIO: "{user_message}"

Genera una respuesta apropiada y útil como asistente de INSUMOS JIP.
Si el mensaje es una pregunta general sobre la empresa (horarios, servicios generales), respóndela basándote en tus instrucciones.
Si es un saludo, saluda cordialmente.
Si es un agradecimiento, responde cortésmente ("De nada, ¡estamos para servirte!").
Si te piden confirmar un pedido, o detalles de contacto/dirección, usa la información específica de INSUMOS JIP y de Isaac que tienes en tus instrucciones.
Si la pregunta es irrelevante o no la entiendes, indica amablemente que no puedes ayudar con eso y reenfoca a temas de la empresa.
NO des información médica.
"""
            logger.info(f"Enviando prompt a Gemini para respuesta general. Mensaje: '{user_message[:100]}...'")
            
            response = self.model.generate_content(prompt)
            response_text = ""
            if response.parts:
                response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif hasattr(response, 'text'):
                response_text = response.text
            
            response_text = response_text.strip()
            logger.info(f"Respuesta general recibida de Gemini ({len(response_text)} caracteres)")
            return response_text
        except Exception as e:
            logger.error(f"Error en generate_response: {e}\n{traceback.format_exc()}")
            return "Lo siento, estoy experimentando dificultades técnicas. Por favor, intenta de nuevo más tarde."

    def generate_product_response(self, user_message, producto_info, additional_context="", conversation_history=None, es_consulta_cantidad=False, cantidad_solicitada=None):
        try:
            producto_nombre_original_consulta = additional_context 
            
            mensaje_final_accion = ("Para confirmar tu pedido o si tienes más preguntas, por favor responde a este mensaje, "
                                 "o contacta a Isaac al +52 1 477 677 5291 (WhatsApp/llamada). "
                                 "Nuestra dirección para recolecciones es Baya #503, Col. Arboledas de San José, León, México.")

            if not producto_info or (not producto_info.get("opcion_entrega_inmediata") and not producto_info.get("opcion_mejor_precio")):
                logger.warning(f"No se encontraron opciones de producto para '{producto_nombre_original_consulta}' en generate_product_response")
                return (f"Lo siento, no encontré información para el producto '{producto_nombre_original_consulta}' en este momento. "
                        f"¿Podrías verificar el nombre o proporcionar más detalles? {mensaje_final_accion}")

            cantidad_calc = cantidad_solicitada if es_consulta_cantidad and isinstance(cantidad_solicitada, int) and cantidad_solicitada > 0 else 1

            # ✅ NUEVA FUNCIÓN CON MÁRGENES APLICADOS (FÓRMULA CORRECTA)
            def aplicar_margen_y_formatear_precio(precio_str, fuente, cantidad_local=1):
                """
                Aplica el margen correspondiente al proveedor y formatea el precio.
                FÓRMULA CORRECTA: Margen sobre precio de venta
                
                Args:
                    precio_str (str): Precio original del proveedor
                    fuente (str): Nombre del proveedor
                    cantidad_local (int): Cantidad de productos
                    
                Returns:
                    str: Precio final formateado con margen aplicado
                """
                try:
                    # 1. Extraer precio numérico del string
                    precio_compra = extraer_precio_numerico(precio_str)
                    
                    if precio_compra <= 0:
                        logger.warning(f"💰 Precio inválido o cero: '{precio_str}' para fuente '{fuente}'")
                        return "Precio no disponible"
                    
                    # 2. Aplicar margen según el proveedor (FÓRMULA CORRECTA)
                    precio_con_margen = calcular_precio_con_margen(precio_compra, fuente)
                    
                    # 3. Calcular precio total por cantidad
                    precio_total = precio_con_margen * cantidad_local
                    
                    # 4. Formatear precio
                    precio_formateado = formatear_precio_mexicano(precio_total)
                    
                    # 5. Log detallado para tracking y debugging
                    margen_porcentaje = MARGENES_GANANCIA.get(fuente, 0)
                    ganancia_pesos = precio_con_margen - precio_compra
                    logger.info(f"💰 PRECIO CALCULADO (FÓRMULA CORRECTA):")
                    logger.info(f"   📍 Fuente: {fuente}")
                    logger.info(f"   💵 Precio original: ${precio_compra:.2f}")
                    logger.info(f"   📈 Margen aplicado: {margen_porcentaje}% (sobre precio de venta)")
                    logger.info(f"   💎 Precio con margen: ${precio_con_margen:.2f}")
                    logger.info(f"   💸 Ganancia: ${ganancia_pesos:.2f}")
                    logger.info(f"   🔢 Cantidad: {cantidad_local}")
                    logger.info(f"   🏷️ Precio final: {precio_formateado}")
                    
                    return precio_formateado
                    
                except Exception as e:
                    logger.error(f"❌ Error calculando precio con margen: '{precio_str}' para fuente '{fuente}', "
                                f"cantidad '{cantidad_local}'. Error: {e}")
                    return "Precio no disponible"

            fuente_mapping = {
                "Sufarmed": "SF", "Difarmer": "DF", "Fanasa": "FN",
                "Nadro": "ND", "FANASA": "FN", "NADRO": "ND", 
                "Base Interna": "INSUMOS JIP (Nuestra Base)",
                "Farmacia del Ahorro": "FA", "Farmacias Guadalajara": "FG", 
            }
            producto_display_nombre = (producto_info.get("opcion_mejor_precio", {}).get("nombre") or
                                     producto_info.get("opcion_entrega_inmediata", {}).get("nombre") or
                                     producto_nombre_original_consulta or "el producto consultado")

            respuesta_partes = []
            if es_consulta_cantidad and cantidad_solicitada:
                respuesta_partes.append(f"Para {cantidad_solicitada} unidad(es) de '{producto_display_nombre}':")
            else:
                respuesta_partes.append(f"Información sobre '{producto_display_nombre}':")

            opciones_presentadas = 0
            op_ei = producto_info.get("opcion_entrega_inmediata")
            if op_ei and op_ei.get('precio'):
                # ✅ APLICAR MARGEN AQUÍ
                precio_ei_str = aplicar_margen_y_formatear_precio(op_ei['precio'], op_ei.get('fuente', ''), cantidad_calc)
                fuente_ei_original = op_ei.get('fuente', 'Base Interna')
                fuente_ei_cod = fuente_mapping.get(fuente_ei_original, fuente_ei_original)
                mensaje_origen_ei = f"(Origen: {fuente_ei_cod})"
                if fuente_ei_original == "Base Interna":
                    entrega_ei_msg = "disponible directamente con nosotros (INSUMOS JIP) para entrega HOY mismo"
                    mensaje_origen_ei = "" 
                elif fuente_ei_original == "Sufarmed":
                     entrega_ei_msg = f"para entrega HOY mismo (vía {fuente_ei_cod})"
                     mensaje_origen_ei = "" 
                else:
                    entrega_ei_msg = f"para entrega MAÑANA (prioritaria, vía {fuente_ei_cod})"
                    mensaje_origen_ei = ""
                respuesta_partes.append(f"• Opción entrega rápida: Precio total {precio_ei_str}, {entrega_ei_msg} {mensaje_origen_ei}".strip())
                opciones_presentadas +=1

            op_mp = producto_info.get("opcion_mejor_precio")
            if op_mp and op_mp.get('precio'):
                mostrar_op_mp = True
                if op_ei and op_ei.get('precio') == op_mp.get('precio') and op_ei.get('fuente') == op_mp.get('fuente'):
                    if opciones_presentadas > 0 : 
                        mostrar_op_mp = False
                
                if mostrar_op_mp:
                    # ✅ APLICAR MARGEN AQUÍ
                    precio_mp_str = aplicar_margen_y_formatear_precio(op_mp['precio'], op_mp.get('fuente', ''), cantidad_calc)
                    fuente_mp_original = op_mp.get('fuente', '')
                    fuente_mp_cod = fuente_mapping.get(fuente_mp_original, fuente_mp_original)
                    mensaje_origen_mp = f"(Origen: {fuente_mp_cod})"
                    entrega_mp_msg = "MAÑANA" 
                    if fuente_mp_original == "Base Interna":
                        entrega_mp_msg = "disponible directamente con nosotros (INSUMOS JIP) para entrega HOY mismo"
                        mensaje_origen_mp = ""
                    elif fuente_mp_original == "Sufarmed" and not op_ei : 
                        entrega_mp_msg = f"para entrega HOY mismo (vía {fuente_mp_cod})"
                        mensaje_origen_mp = ""
                    elif fuente_mp_original not in ["Sufarmed", "Base Interna"]:
                         entrega_mp_msg = f"con entrega estimada {entrega_mp_msg} (vía {fuente_mp_cod})"
                         mensaje_origen_mp = ""
                    
                    prefijo_opcion = "• Opción mejor precio" if opciones_presentadas > 0 else "• Precio"
                    respuesta_partes.append(f"{prefijo_opcion}: {precio_mp_str} {entrega_mp_msg} {mensaje_origen_mp}".strip())
                    opciones_presentadas +=1
            
            if opciones_presentadas == 0: 
                 logger.warning(f"No se encontraron opciones válidas con precio para '{producto_display_nombre}'")
                 return (f"No pude obtener información detallada del precio o disponibilidad para '{producto_display_nombre}' en este momento. "
                         f"Por favor, intenta más tarde. {mensaje_final_accion}")

            fuente_principal_opcion = op_ei if op_ei and op_ei.get("fuente") == "Base Interna" else op_mp if op_mp and op_mp.get("fuente") == "Base Interna" else None
            if fuente_principal_opcion:
                stock_disp_str = fuente_principal_opcion.get('existencia', '0')
                try:
                    stock_num = fuente_principal_opcion.get('existencia_numerica', int(float(stock_disp_str)))
                    respuesta_partes.append(f"📦 Disponibles en nuestra base (INSUMOS JIP): {stock_num if stock_num > 0 else 'Agotado o consultar'}")
                except:
                    respuesta_partes.append("📦 Disponibilidad en nuestra base (INSUMOS JIP): Por favor, consultar.")
            
            producto_referencia_receta = op_ei or op_mp # Tomar la primera opción válida que tengamos
            if producto_referencia_receta and producto_referencia_receta.get('requiere_receta', False): 
                respuesta_partes.append("⚠️ Este producto requiere presentar receta para su venta.")

            respuesta_partes.append(f"\n{mensaje_final_accion}")
            return "\n".join(respuesta_partes)

        except Exception as e:
            logger.error(f"Error severo en generate_product_response: {e}\n{traceback.format_exc()}")
            return ("Lo siento, tuve un problema al generar la información del producto. "
                    "Por favor, intenta de nuevo o contacta a Isaac para asistencia.")
