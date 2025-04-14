# filepath: /Users/juandiegogutierrezcortez/mvp/app/routes/whatsapp.py
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.db.session import get_db
from app.services import openai_service
from app.security import blacklist

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook", response_model=Dict[str, Any])
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint para recibir webhooks de WhatsApp
    """
    try:
        # Obtener el cuerpo del mensaje
        body = await request.json()
        logger.info(f"Webhook de WhatsApp recibido: {body}")
        
        # Procesar el mensaje según la estructura del webhook
        # Este procesamiento depende de la integración específica
        return {"status": "success", "message": "Webhook procesado correctamente"}
    
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message", response_model=Dict[str, Any])
async def process_message(
    phone_number: str = Body(...),
    message: str = Body(...),
    customer_name: str = Body("Cliente"),
    db: Session = Depends(get_db)
):
    """
    Procesa un mensaje entrante de WhatsApp
    """
    try:
        logger.info(f"Mensaje recibido de {phone_number}: {message}")
        
        # Verificar si el número está en la lista negra
        is_blacklisted = blacklist.is_blacklisted(db, phone_number)
        
        if is_blacklisted:
            # Si es una solicitud de desbloqueo, procesarla
            unblock_request = openai_service.detect_unblock_request(message)
            
            if unblock_request["is_unblock_request"]:
                # Procesar la solicitud de desbloqueo
                if unblock_request["verification_code"]:
                    # Intentar desbloquear con el código
                    result = blacklist.verify_and_unblock(db, phone_number, unblock_request["verification_code"])
                    success = result.get("success", False)
                    
                    response_message = result.get("message", "Código procesado.")
                    return {
                        "success": True,
                        "message": response_message,
                        "unblocked": success
                    }
                else:
                    # Crear solicitud de desbloqueo
                    result = blacklist.request_unblock(db, phone_number, unblock_request["reason"])
                    
                    response_message = openai_service.generate_response(
                        customer_name=customer_name,
                        customer_message=message,
                        conversation_history=[],
                        is_blacklisted=True
                    )
                    
                    return {
                        "success": True,
                        "message": response_message,
                        "unblock_requested": result.get("success", False)
                    }
            
            # Número bloqueado, responder con mensaje genérico de bloqueo
            response_message = "Lo sentimos, este número ha sido bloqueado por motivos de seguridad. Para solicitar el desbloqueo, envía un mensaje con la palabra 'DESBLOQUEAR'."
            
            return {
                "success": False,
                "message": response_message,
                "blocked": True
            }
        
        # Analizar si el mensaje contiene amenazas
        threat_analysis = openai_service.detect_threats(message)
        is_threat = threat_analysis.get("is_threat", False)
        
        # Si es una amenaza, bloquear el número
        if is_threat:
            threat_score = threat_analysis.get("score", 0)
            threat_type = threat_analysis.get("threat_type", "desconocida")
            
            # Solo bloquear si la amenaza es grave (score > 0.7)
            if threat_score > 0.7:
                blacklist.add_to_blacklist(
                    db, 
                    phone_number, 
                    f"Amenaza detectada automáticamente: {threat_type}. Score: {threat_score}",
                    "automatic"
                )
                
                logger.warning(f"Número bloqueado por amenaza: {phone_number}. Score: {threat_score}")
                
                return {
                    "success": False,
                    "message": "Lo sentimos, no podemos procesar este tipo de mensajes.",
                    "blocked": True,
                    "threat_detected": True
                }
        
        # Generar respuesta usando el servicio de OpenAI
        response_message = openai_service.generate_response(
            customer_name=customer_name,
            customer_message=message,
            conversation_history=[],
            is_suspicious=(threat_analysis.get("score", 0) > 0.3)
        )
        
        return {
            "success": True,
            "message": response_message,
            "threat_score": threat_analysis.get("score", 0)
        }
    
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        return {
            "success": False,
            "message": "Lo sentimos, ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente más tarde.",
            "error": str(e)
        }

@router.get("/unblock-instructions/{phone_number}")
async def get_unblock_instructions(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene instrucciones sobre cómo desbloquear un número
    """
    try:
        # Verificar si el número está bloqueado
        is_blocked = blacklist.is_blacklisted(db, phone_number)
        
        if not is_blocked:
            return {
                "success": True,
                "is_blocked": False,
                "message": "Este número no está bloqueado."
            }
        
        # Proporcionar instrucciones de desbloqueo
        return {
            "success": True,
            "is_blocked": True,
            "message": "Tu número está bloqueado por motivos de seguridad.",
            "instructions": [
                "Para solicitar el desbloqueo, envía un mensaje con la palabra 'SOLICITUD DESBLOQUEO' seguido de una breve explicación.",
                "Si ya tienes un código de verificación, envía 'VERIFICAR' seguido del código.",
                "También puedes contactar al soporte técnico para más ayuda."
            ]
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo instrucciones de desbloqueo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))