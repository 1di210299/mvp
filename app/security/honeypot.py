"""
Módulo para implementar un sistema de honeypot para extorsionadores
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes para configuración
HONEYPOT_ENABLED = True
REDIRECT_URL = "https://t.me/TuBotDeTelegram?start=extorsion"
VERIFICATION_PAGE = "/security/verification"

# Almacenamiento de datos capturados (en producción, usar base de datos)
honeypot_records = {}

def should_deploy_honeypot(message: str, threat_score: float) -> bool:
    """
    Determina si se debe desplegar el honeypot basado en el contenido del mensaje
    y la puntuación de amenaza calculada.
    
    Args:
        message: Contenido del mensaje a analizar
        threat_score: Puntuación de amenaza calculada (0.0 a 1.0)
        
    Returns:
        bool: True si se debe desplegar el honeypot
    """
    # Solo desplegar si el honeypot está habilitado globalmente
    if not HONEYPOT_ENABLED:
        return False
    
    # Criterio basado en la puntuación de amenaza (ajustar según necesidades)
    if threat_score >= 0.85:
        return True
    
    # Palabras clave de alta sospecha (extorsión directa)
    high_risk_keywords = [
        "matar", "bomba", "secuestrar", "extorsión", "amenaza", "pagar o", 
        "dinero o", "consecuencias", "último aviso", "pagame", "págate"
    ]
    
    message_lower = message.lower()
    for keyword in high_risk_keywords:
        if keyword in message_lower:
            return True
    
    return False

def generate_honeypot_response(phone_number: str, message_id: str = None) -> Dict[str, Any]:
    """
    Genera una respuesta con el enlace del honeypot
    
    Args:
        phone_number: Número de teléfono del posible extorsionador
        message_id: ID del mensaje original (opcional)
        
    Returns:
        dict: Respuesta con el enlace del honeypot
    """
    # Generar un identificador único para este intento
    tracking_id = str(uuid.uuid4())
    
    # Registrar el intento de honeypot (en producción, guardar en base de datos)
    honeypot_records[tracking_id] = {
        "phone_number": phone_number,
        "message_id": message_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "created",
        "redirect_url": REDIRECT_URL,
        "clicks": 0,
        "telegram_info": None,
        "ip_addresses": []
    }
    
    # URL con el identificador para seguimiento
    verification_url = f"{VERIFICATION_PAGE}?id={tracking_id}"
    
    # Mensaje diseñado para parecer legítimo pero atraer al extorsionador
    response_message = (
        "Hola, soy Carlos del departamento de atención al cliente. He recibido una alerta de nuestro sistema "
        "sobre un posible problema en esta conversación. Para hablar con un representante y resolver esta "
        f"situación, haga clic aquí: {verification_url}\n\n"
        "Estaré pendiente de su caso para ayudarle personalmente."
    )
    
    return {
        "tracking_id": tracking_id,
        "message": response_message,
        "honeypot_deployed": True
    }

def record_honeypot_click(tracking_id: str, request: Request, telegram_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Registra un clic en el enlace del honeypot
    
    Args:
        tracking_id: ID de seguimiento del honeypot
        request: Objeto Request de FastAPI con datos de la petición
        telegram_data: Datos recibidos de Telegram (opcional)
        
    Returns:
        dict: Datos actualizados del registro
    """
    if tracking_id not in honeypot_records:
        logger.warning(f"Intento de acceso a un honeypot no registrado: {tracking_id}")
        return {"status": "error", "message": "ID no encontrado"}
    
    # Obtener información del cliente
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    referer = request.headers.get("referer", "unknown")
    
    # Actualizar registro
    record = honeypot_records[tracking_id]
    record["clicks"] += 1
    record["last_click_at"] = datetime.utcnow().isoformat()
    record["status"] = "clicked"
    
    # Registrar información del cliente
    ip_info = {
        "ip": client_host,
        "user_agent": user_agent,
        "referer": referer,
        "timestamp": datetime.utcnow().isoformat()
    }
    record["ip_addresses"].append(ip_info)
    
    # Si hay datos de Telegram, actualizarlos
    if telegram_data:
        record["telegram_info"] = telegram_data
        record["status"] = "completed"
    
    # Guardar en la base de datos cuando esté implementada
    # save_to_database(record)
    
    logger.info(f"Honeypot activado: {tracking_id} - IP: {client_host}")
    return record

def save_to_database(db: Session, record: Dict[str, Any]) -> bool:
    """
    Guarda el registro del honeypot en la base de datos
    
    Args:
        db: Sesión de base de datos
        record: Datos del registro a guardar
        
    Returns:
        bool: True si se guardó correctamente
    """
    try:
        # Aquí se implementaría la lógica para guardar en la base de datos
        # Por ahora, solo registramos en los logs
        logger.info(f"Guardando registro de honeypot en DB: {record['tracking_id']}")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error al guardar registro de honeypot: {str(e)}")
        return False

# Funciones auxiliares para análisis posterior

def get_honeypot_statistics() -> Dict[str, Any]:
    """
    Obtiene estadísticas sobre los honeypots desplegados
    
    Returns:
        dict: Estadísticas de honeypots
    """
    total = len(honeypot_records)
    clicked = sum(1 for r in honeypot_records.values() if r["clicks"] > 0)
    completed = sum(1 for r in honeypot_records.values() if r["status"] == "completed")
    
    return {
        "total_deployed": total,
        "total_clicked": clicked,
        "total_completed": completed,
        "click_rate": clicked / total if total > 0 else 0,
        "completion_rate": completed / total if total > 0 else 0
    }

def get_honeypot_record(tracking_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un registro específico de honeypot
    
    Args:
        tracking_id: ID de seguimiento del honeypot
        
    Returns:
        dict: Registro del honeypot o None si no existe
    """
    return honeypot_records.get(tracking_id)