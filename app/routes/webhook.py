# filepath: /Users/juandiegogutierrezcortez/mvp/app/routes/webhook.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/twilio", response_model=Dict[str, Any])
async def twilio_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook para recibir notificaciones de Twilio
    """
    try:
        # Obtener datos del webhook
        payload = await request.form()
        
        # Extraer información relevante
        message_sid = payload.get("MessageSid", "")
        from_number = payload.get("From", "")
        body = payload.get("Body", "")
        
        logger.info(f"Webhook de Twilio recibido: From={from_number}, Body={body}")
        
        # Aquí procesarías el mensaje
        
        return {
            "success": True,
            "message": "Webhook procesado correctamente"
        }
    
    except Exception as e:
        logger.error(f"Error procesando webhook de Twilio: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }