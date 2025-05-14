"""
Script de diagnóstico para verificar los métodos disponibles en MessageHandler
Añade este archivo a tu proyecto y ejecútalo en Google Cloud para verificar la configuración.
"""
import os
import json
import inspect
import logging
import sys
import importlib.util
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Diagnóstico SOPRIM BOT", description="Herramienta de diagnóstico")

@app.get("/")
async def diagnostico():
    """
    Realiza un diagnóstico completo de la aplicación.
    """
    result = {
        "status": "running",
        "python_version": sys.version,
        "modules": {},
        "handlers": {},
        "services": {},
    }
    
    # Verificar módulos
    modules_to_check = [
        "handlers.message_handler", 
        "services.gemini_service", 
        "services.whatsapp_service",
        "services.scraping_service"
    ]
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            result["modules"][module_name] = {
                "status": "loaded",
                "path": getattr(module, "__file__", "unknown"),
                "classes": []
            }
            
            # Examinar clases en el módulo
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj.__module__ == module.__name__:
                    class_info = {
                        "name": name,
                        "methods": []
                    }
                    
                    # Examinar métodos en la clase
                    for method_name, method_obj in inspect.getmembers(obj):
                        if inspect.isfunction(method_obj) and not method_name.startswith("_"):
                            try:
                                signature = str(inspect.signature(method_obj))
                                class_info["methods"].append({
                                    "name": method_name,
                                    "signature": signature,
                                    "async": inspect.iscoroutinefunction(method_obj)
                                })
                            except Exception as e:
                                class_info["methods"].append({
                                    "name": method_name,
                                    "error": str(e)
                                })
                    
                    result["modules"][module_name]["classes"].append(class_info)
        except Exception as e:
            result["modules"][module_name] = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    # Verificar MessageHandler específicamente
    try:
        from handlers.message_handler import MessageHandler
        handler = MessageHandler()
        result["handlers"]["MessageHandler"] = {
            "status": "initialized",
            "dir": dir(handler),
            "methods": {}
        }
        
        # Verificar métodos específicos
        methods_to_check = ["procesar_mensaje", "es_mensaje_a_ignorar", "detectar_tipo_mensaje"]
        for method_name in methods_to_check:
            if hasattr(handler, method_name):
                method = getattr(handler, method_name)
                result["handlers"]["MessageHandler"]["methods"][method_name] = {
                    "exists": True,
                    "callable": callable(method),
                    "async": inspect.iscoroutinefunction(method) if callable(method) else False,
                    "signature": str(inspect.signature(method)) if callable(method) else "N/A"
                }
            else:
                result["handlers"]["MessageHandler"]["methods"][method_name] = {
                    "exists": False
                }
    except Exception as e:
        result["handlers"]["MessageHandler"] = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    
    # Verificar estructura de directorios
    result["directory_structure"] = {}
    dirs_to_check = [".", "handlers", "services", "config"]
    for directory in dirs_to_check:
        if os.path.exists(directory):
            try:
                files = os.listdir(directory)
                result["directory_structure"][directory] = files
            except Exception as e:
                result["directory_structure"][directory] = f"Error: {str(e)}"
        else:
            result["directory_structure"][directory] = "No existe"
    
    return result

# Si se ejecuta directamente
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8081))  # Usar un puerto diferente para no interferir
    uvicorn.run("diagnostico:app", host="0.0.0.0", port=port, reload=True)