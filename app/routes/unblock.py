# filepath: /Users/juandiegogutierrezcortez/mvp/app/routes/unblock.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from pydantic import BaseModel

from app.db.session import get_db
from app.security import blacklist
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class UnblockRequestModel(BaseModel):
    phone_number: str
    reason: str = ""

class VerifyCodeModel(BaseModel):
    phone_number: str
    code: str

@router.post("/request", response_model=Dict[str, Any])
async def request_unblock(
    data: UnblockRequestModel,
    db: Session = Depends(get_db)
):
    """
    Registra una solicitud para desbloquear un número
    """
    logger.info(f"Solicitud de desbloqueo recibida para {data.phone_number}")
    result = blacklist.request_unblock(db, data.phone_number, data.reason)
    return result

@router.post("/verify", response_model=Dict[str, Any])
async def verify_code(
    data: VerifyCodeModel,
    db: Session = Depends(get_db)
):
    """
    Verifica un código de desbloqueo y desbloquea el número si es válido
    """
    logger.info(f"Verificación de código de desbloqueo para {data.phone_number}")
    result = blacklist.verify_and_unblock(db, data.phone_number, data.code)
    return result

@router.get("/requests", response_model=List[Dict[str, Any]])
async def get_requests(
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las solicitudes de desbloqueo
    """
    logger.info("Obteniendo solicitudes de desbloqueo")
    requests = blacklist.get_unblock_requests(db, status)
    return requests

@router.post("/approve/{request_id}", response_model=Dict[str, Any])
async def approve_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Aprueba una solicitud de desbloqueo
    """
    logger.info(f"Aprobando solicitud de desbloqueo #{request_id}")
    
    # Check if the function exists
    if not hasattr(blacklist, 'approve_unblock_request'):
        # Basic implementation if the function doesn't exist
        try:
            # Find the request
            requests = blacklist.get_unblock_requests(db)
            request = next((r for r in requests if r["id"] == request_id), None)
            
            if not request:
                return {"success": False, "message": "Solicitud no encontrada"}
            
            # Unblock the number
            success, message = blacklist.remove_from_blacklist(db, request["phone_number"])
            
            return {"success": success, "message": message}
        except Exception as e:
            logger.error(f"Error aprobando solicitud: {str(e)}")
            return {"success": False, "message": str(e)}
    else:
        result = blacklist.approve_unblock_request(db, request_id)
        return result

@router.post("/reject/{request_id}", response_model=Dict[str, Any])
async def reject_request(
    request_id: int,
    reason: str = Body("", embed=True),
    db: Session = Depends(get_db)
):
    """
    Rechaza una solicitud de desbloqueo
    """
    logger.info(f"Rechazando solicitud de desbloqueo #{request_id}")
    
    # Check if the function exists
    if not hasattr(blacklist, 'reject_unblock_request'):
        return {"success": False, "message": "Función no implementada"}
    
    result = blacklist.reject_unblock_request(db, request_id, reason)
    return result