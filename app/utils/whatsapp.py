import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

logger = logging.getLogger("app.utils.whatsapp")

# Almacenamiento en memoria para el estado de la conexión
_connection_status = {
    "status": "unknown",
    "last_check": None,
    "last_active": None,
    "last_message_received": None,
    "last_message_sent": None,
    "details": ""
}

def check_whatsapp_connection() -> Dict[str, Any]:
    """
    Verifica el estado de la conexión de WhatsApp/Twilio
    
    Returns:
        Dict con información sobre el estado de la conexión
    """
    now = datetime.now()
    
    # Evitar demasiadas verificaciones consecutivas (máximo cada 30 segundos)
    if (_connection_status["last_check"] and 
        (now - _connection_status["last_check"]) < timedelta(seconds=30)):
        return _connection_status
    
    _connection_status["last_check"] = now
    
    # Verificar credenciales de Twilio
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        _connection_status["status"] = "not_configured"
        _connection_status["details"] = "Faltan credenciales de Twilio"
        return _connection_status
    
    # Verificar API de Twilio
    try:
        # URL para verificar el estado de la cuenta de Twilio
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}.json"
        
        response = requests.get(
            url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=5
        )
        
        if response.status_code == 200:
            account_info = response.json()
            _connection_status["status"] = "connected" if account_info.get("status") == "active" else "inactive"
            _connection_status["last_active"] = now.isoformat()
            _connection_status["details"] = f"Cuenta Twilio activa: {account_info.get('friendly_name')}"
        else:
            _connection_status["status"] = "error"
            _connection_status["details"] = f"Error al verificar Twilio: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error al verificar la conexión de WhatsApp: {str(e)}")
        _connection_status["status"] = "error"
        _connection_status["details"] = f"Error de conexión: {str(e)}"
    
    return _connection_status

def update_message_received():
    """Actualiza el registro de último mensaje recibido"""
    now = datetime.now()
    _connection_status["last_message_received"] = now.isoformat()
    _connection_status["last_active"] = now.isoformat()
    _connection_status["status"] = "connected"
    _connection_status["details"] = "Conexión activa (mensaje recibido)"

def update_message_sent():
    """Actualiza el registro de último mensaje enviado"""
    now = datetime.now()
    _connection_status["last_message_sent"] = now.isoformat()
    _connection_status["last_active"] = now.isoformat()
