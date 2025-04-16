from fastapi import APIRouter, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json
import logging
import os

from app.db.session import get_db
from app.services import twilio_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Crear un directorio de logs si no existe
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "webhook_debug.log")

# Configurar el logger específico para diagnóstico
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

debug_logger = logging.getLogger("webhook_debug")
debug_logger.setLevel(logging.DEBUG)
debug_logger.addHandler(file_handler)

@router.post("/debug")
async def debug_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint de diagnóstico para registrar exactamente cómo llegan los mensajes de WhatsApp.
    Simplemente registra todos los datos y responde con un mensaje fijo.
    """
    try:
        # Guardar el formulario completo
        form_data = await request.form()
        form_dict = {key: value for key, value in form_data.items()}
        
        # Extraer información clave
        from_number = form_data.get("From", "").strip()
        to_number = form_data.get("To", "").strip()
        message_body = form_data.get("Body", "").strip()
        
        # Registrar toda la información en el archivo de diagnóstico
        debug_logger.info(f"===== NUEVO MENSAJE RECIBIDO =====")
        debug_logger.info(f"De: {from_number}")
        debug_logger.info(f"A: {to_number}")
        debug_logger.info(f"Mensaje: {message_body}")
        debug_logger.info(f"Datos completos: {json.dumps(form_dict, indent=2)}")
        
        # Registrar información de cabeceras
        headers = {k: v for k, v in request.headers.items()}
        debug_logger.info(f"Cabeceras: {json.dumps(headers, indent=2)}")
        
        # Responder con un mensaje fijo para diagnóstico
        background_tasks.add_task(
            twilio_service.send_message,
            to=from_number,
            message="✅ DIAGNÓSTICO: Tu mensaje ha sido recibido correctamente. Revisar logs para detalles."
        )
        
        return JSONResponse(
            content={"status": "success", "message": "Mensaje de diagnóstico procesado"},
            status_code=200
        )
        
    except Exception as e:
        debug_logger.error(f"Error en webhook de diagnóstico: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": "Error en procesamiento de diagnóstico"},
            status_code=500
        )

@router.get("/status")
def check_status():
    """
    Endpoint simple para verificar que el servidor está funcionando.
    """
    return {"status": "running", "debug_log": log_file}