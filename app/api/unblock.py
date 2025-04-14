from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.security.access_control import (
    add_to_whitelist,
    is_whitelisted,
    block_number,
    is_blocked,
    get_blocked_numbers,
    get_whitelist as get_whitelist_numbers
)
from app.config import settings

# Intentar importar la sesión de base de datos
try:
    from app.db.session import get_db
except ImportError:
    # Crear un generador de DB simulado si no existe
    def get_db():
        yield None

router = APIRouter()

class UnblockRequest(BaseModel):
    phone_number: str
    reason: Optional[str] = "Desbloqueado manualmente"

class BlockRequest(BaseModel):
    phone_number: str
    reason: Optional[str] = "Bloqueado manualmente"

class ConfigUpdateRequest(BaseModel):
    min_suspicious_score: Optional[float] = None
    threat_score_threshold: Optional[float] = None
    enable_auto_blocking: Optional[bool] = None

@router.post("/unblock_number", status_code=200)
def unblock_number(request: UnblockRequest):
    """
    Desbloquea un número de teléfono específico añadiéndolo a la whitelist
    """
    # Limpiar el número
    phone = request.phone_number.strip()
    
    # Asegurarse de que tiene el formato correcto
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Si el número incluye "whatsapp:", extraerlo
    if phone.startswith("whatsapp:"):
        phone = phone[9:]  # Quitar el prefijo "whatsapp:"
    
    # Verificar si ya está en la whitelist
    if is_whitelisted(phone):
        return {"message": f"El número {phone} ya estaba en la whitelist"}
    
    # Añadir a la whitelist
    if add_to_whitelist(phone):
        return {
            "message": f"Número {phone} desbloqueado exitosamente",
            "whitelisted": True
        }
    else:
        raise HTTPException(status_code=500, detail="No se pudo desbloquear el número")

@router.post("/block_number", status_code=200)
def manual_block(request: BlockRequest):
    """
    Bloquea manualmente un número de teléfono
    """
    phone = request.phone_number.strip()
    
    # Asegurarse de que tiene el formato correcto
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Verificar si está en la whitelist
    if is_whitelisted(phone):
        raise HTTPException(
            status_code=400, 
            detail=f"El número {phone} está en la whitelist y no puede ser bloqueado"
        )
    
    # Bloquear el número
    if block_number(phone, request.reason):
        return {
            "message": f"Número {phone} bloqueado exitosamente",
            "blocked": True
        }
    else:
        raise HTTPException(status_code=500, detail="No se pudo bloquear el número")

@router.get("/whitelist", response_model=List[str])
def get_whitelist():
    """
    Obtiene la lista de números en la whitelist
    """
    return get_whitelist_numbers()

@router.get("/blocked_numbers", response_model=List[str])
def get_blocked():
    """
    Obtiene la lista de números bloqueados
    """
    return get_blocked_numbers()

@router.post("/update_security_config")
def update_security_config(request: ConfigUpdateRequest):
    """
    Actualiza la configuración de seguridad en tiempo de ejecución
    """
    updates = {}
    
    if request.min_suspicious_score is not None:
        updates["MIN_SUSPICIOUS_SCORE"] = request.min_suspicious_score
    
    if request.threat_score_threshold is not None:
        updates["THREAT_SCORE_THRESHOLD"] = request.threat_score_threshold
    
    if request.enable_auto_blocking is not None:
        updates["ENABLE_AUTO_BLOCKING"] = request.enable_auto_blocking
    
    # Actualizar configuración
    for key, value in updates.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    return {
        "message": "Configuración actualizada correctamente",
        "new_settings": {
            "min_suspicious_score": getattr(settings, "MIN_SUSPICIOUS_SCORE", None),
            "threat_score_threshold": getattr(settings, "THREAT_SCORE_THRESHOLD", None),
            "enable_auto_blocking": getattr(settings, "ENABLE_AUTO_BLOCKING", None)
        }
    }

@router.post("/force_unblock", status_code=200)
def force_unblock(request: UnblockRequest):
    """
    Fuerza el desbloqueo de un número en todas las posibles listas
    """
    phone = request.phone_number.strip()
    
    # Asegurarse de que tiene el formato correcto
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Lista para guardar acciones realizadas
    actions = []
    
    # 1. Añadir a whitelist
    add_to_whitelist(phone)
    actions.append("Añadido a whitelist")
    
    # 2. Añadir versión con prefijo whatsapp:
    add_to_whitelist(f"whatsapp:{phone}")
    actions.append("Añadido formato whatsapp: a whitelist")
    
    # 3. Intentar limpiar listas de bloqueo
    # Asumiendo que hay otras listas/módulos que podrían estar bloqueando
    
    try:
        # Intenta importar e interactuar con módulo blacklist si existe
        from app.security import blacklist
        if hasattr(blacklist, 'remove_from_blacklist'):
            try:
                db = next(get_db()) if 'get_db' in globals() else None
                if db:
                    blacklist.remove_from_blacklist(db, phone)
                    blacklist.remove_from_blacklist(db, f"whatsapp:{phone}")
                    actions.append("Eliminado de base de datos blacklist")
            except Exception as e:
                actions.append(f"Error al eliminar de BD: {str(e)}")
    except ImportError:
        actions.append("Módulo blacklist no encontrado")
    
    # Guardar la configuración para prevenir futuros bloqueos
    try:
        # Deshabilitar bloqueo automático
        if hasattr(settings, "ENABLE_AUTO_BLOCKING"):
            setattr(settings, "ENABLE_AUTO_BLOCKING", False)
            actions.append("Bloqueo automático deshabilitado")
        
        # Aumentar el umbral de detección
        if hasattr(settings, "THREAT_SCORE_THRESHOLD"):
            setattr(settings, "THREAT_SCORE_THRESHOLD", 0.95)
            actions.append("Umbral de amenaza aumentado a 0.95")
    except Exception as e:
        actions.append(f"Error al modificar configuración: {str(e)}")
    
    return {
        "message": f"Desbloqueo forzado aplicado para {phone}",
        "actions": actions,
        "next_steps": "Por favor, reinicia la aplicación para asegurar que los cambios surtan efecto."
    }

@router.get("/debug/{phone_number}")
def debug_phone_status(phone_number: str):
    """
    Depura el estado de un número para ver si está bloqueado y por qué
    """
    # Normalizar número
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number
    
    # Versiones del número
    plain_version = phone_number
    whatsapp_version = f"whatsapp:{phone_number}"
    
    # Verificar whitelist
    is_in_whitelist_plain = is_whitelisted(plain_version)
    is_in_whitelist_wa = is_whitelisted(whatsapp_version)
    
    # Verificar si está bloqueado
    is_blocked_plain = is_blocked(plain_version)
    is_blocked_wa = is_blocked(whatsapp_version)
    
    # Intentar verificar blacklist si existe
    blacklist_status = "No se pudo verificar blacklist"
    try:
        from app.security import blacklist
        if hasattr(blacklist, 'is_blacklisted'):
            try:
                db = next(get_db()) if 'get_db' in globals() else None
                if db:
                    blacklisted = blacklist.is_blacklisted(db, whatsapp_version)
                    blacklist_status = f"En blacklist: {blacklisted}"
            except Exception as e:
                blacklist_status = f"Error verificando blacklist: {str(e)}"
    except ImportError:
        blacklist_status = "Módulo blacklist no disponible"
    
    return {
        "phone_number": phone_number,
        "whatsapp_version": whatsapp_version,
        "whitelist_status": {
            "plain_version": is_in_whitelist_plain,
            "whatsapp_version": is_in_whitelist_wa
        },
        "blocked_status": {
            "plain_version": is_blocked_plain,
            "whatsapp_version": is_blocked_wa
        },
        "blacklist_status": blacklist_status,
        "security_config": {
            "auto_blocking": getattr(settings, "ENABLE_AUTO_BLOCKING", "No establecido"),
            "threat_threshold": getattr(settings, "THREAT_SCORE_THRESHOLD", "No establecido")
        }
    }

@router.post("/db_unblock", status_code=200)
def unblock_in_database(request: UnblockRequest, db: Session = Depends(get_db)):
    """
    Desbloquea un número directamente en la base de datos, buscando en todas las tablas relevantes
    """
    phone = request.phone_number.strip()
    
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Formatos posibles del número
    formats = [
        phone,
        f"whatsapp:{phone}",
        phone.lstrip("+"),
        phone.replace("+", "")
    ]
    
    results: Dict[str, Any] = {
        "message": f"Intentando desbloquear {phone} en la base de datos",
        "actions": [],
        "errors": []
    }
    
    # 1. Primero agregar a whitelist para evitar bloqueos futuros
    add_to_whitelist(phone)
    results["actions"].append("Añadido a whitelist en memoria")
    
    if db is None:
        results["errors"].append("No se pudo obtener conexión a la base de datos")
        return results
    
    # 2. Buscar en tabla blacklist_entries si existe
    try:
        results["actions"].append("Buscando en tablas de base de datos")
        
        # Verificar si la tabla existe
        tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        table_names = [t[0] for t in tables]
        results["tables_found"] = table_names
        
        # Buscar en blacklist_entries
        if 'blacklist_entries' in table_names:
            for fmt in formats:
                try:
                    # Buscar entradas con este número
                    entries = db.execute(
                        text("SELECT id, phone_number, is_active FROM blacklist_entries WHERE phone_number LIKE :phone"), 
                        {"phone": f"%{fmt}%"}
                    ).fetchall()
                    
                    if entries:
                        for entry in entries:
                            # Desactivar la entrada
                            db.execute(
                                text("UPDATE blacklist_entries SET is_active = 0 WHERE id = :id"),
                                {"id": entry[0]}
                            )
                            results["actions"].append(f"Desactivada entrada #{entry[0]} para número {entry[1]}")
                        
                        db.commit()
                except Exception as e:
                    results["errors"].append(f"Error actualizando blacklist_entries: {str(e)}")
        
        # Buscar en blocked_numbers si existe
        if 'blocked_numbers' in table_names:
            for fmt in formats:
                try:
                    # Eliminar entradas con este número
                    db.execute(
                        text("DELETE FROM blocked_numbers WHERE phone_number LIKE :phone"), 
                        {"phone": f"%{fmt}%"}
                    )
                    results["actions"].append(f"Eliminadas entradas de blocked_numbers para {fmt}")
                    db.commit()
                except Exception as e:
                    results["errors"].append(f"Error eliminando de blocked_numbers: {str(e)}")
        
        # 3. Intentar utilizar el módulo blacklist si existe
        try:
            from app.security import blacklist
            if hasattr(blacklist, 'remove_from_blacklist'):
                for fmt in formats:
                    success, message = blacklist.remove_from_blacklist(db, fmt)
                    if success:
                        results["actions"].append(f"Eliminado de blacklist usando API: {fmt}")
                    else:
                        results["errors"].append(f"No se pudo eliminar de blacklist: {message}")
        except ImportError:
            results["errors"].append("Módulo blacklist no encontrado")
        
        # 4. Buscar en webhooks_blockedphones si existe
        if 'webhooks_blockedphones' in table_names:
            for fmt in formats:
                try:
                    # Eliminar entradas con este número
                    db.execute(
                        text("DELETE FROM webhooks_blockedphones WHERE phone_number LIKE :phone"), 
                        {"phone": f"%{fmt}%"}
                    )
                    results["actions"].append(f"Eliminadas entradas de webhooks_blockedphones para {fmt}")
                    db.commit()
                except Exception as e:
                    results["errors"].append(f"Error eliminando de webhooks_blockedphones: {str(e)}")
        
        # Verificar si hay alguna tabla security_blockedphone
        if 'security_blockedphone' in table_names:
            for fmt in formats:
                try:
                    # Eliminar entradas con este número
                    db.execute(
                        text("DELETE FROM security_blockedphone WHERE phone_number LIKE :phone"), 
                        {"phone": f"%{fmt}%"}
                    )
                    results["actions"].append(f"Eliminadas entradas de security_blockedphone para {fmt}")
                    db.commit()
                except Exception as e:
                    results["errors"].append(f"Error eliminando de security_blockedphone: {str(e)}")
    
    except Exception as e:
        results["errors"].append(f"Error general: {str(e)}")
    
    # 5. Deshabilitar el bloqueo automático para evitar futuros problemas
    try:
        if hasattr(settings, "ENABLE_AUTO_BLOCKING"):
            setattr(settings, "ENABLE_AUTO_BLOCKING", False)
            results["actions"].append("Bloqueo automático deshabilitado")
    except Exception as e:
        results["errors"].append(f"Error al modificar configuración: {str(e)}")
    
    # Verificar directamente en el módulo webhooks.py
    try:
        from app.api import webhooks
        if hasattr(webhooks, 'BLOCKED_NUMBERS') and isinstance(webhooks.BLOCKED_NUMBERS, (list, set)):
            # Intentar eliminar el número de la lista de bloqueados
            for fmt in formats:
                if fmt in webhooks.BLOCKED_NUMBERS:
                    webhooks.BLOCKED_NUMBERS.remove(fmt)
                    results["actions"].append(f"Eliminado {fmt} de webhooks.BLOCKED_NUMBERS")
    except (ImportError, AttributeError) as e:
        results["errors"].append(f"No se pudo acceder a webhooks.BLOCKED_NUMBERS: {str(e)}")
    
    return results

@router.get("/list_tables")
def list_database_tables(db: Session = Depends(get_db)):
    """
    Lista todas las tablas en la base de datos para ayudar en el diagnóstico
    """
    if db is None:
        return {"error": "No se pudo conectar a la base de datos"}
    
    try:
        tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        table_info = {}
        
        for table in tables:
            table_name = table[0]
            try:
                # Obtener esquema de la tabla
                columns = db.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                
                # Contar filas
                count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                
                table_info[table_name] = {
                    "columns": [col[1] for col in columns],
                    "row_count": count
                }
                
                # Si es una tabla que podría contener números de teléfono, buscar
                phone_columns = [col[1] for col in columns if 'phone' in col[1].lower()]
                if phone_columns:
                    for col in phone_columns:
                        phones = db.execute(text(f"SELECT {col} FROM {table_name} LIMIT 10")).fetchall()
                        phone_examples = [p[0] for p in phones if p[0]]
                        if phone_examples:
                            table_info[table_name]["phone_examples"] = phone_examples
            except Exception as e:
                table_info[table_name] = {"error": str(e)}
        
        return {
            "tables": [t[0] for t in tables],
            "details": table_info
        }
    except Exception as e:
        return {"error": f"Error al listar tablas: {str(e)}"}

