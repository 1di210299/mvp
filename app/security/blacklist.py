import logging
import csv
import os
import datetime
import secrets
from typing import List, Dict, Optional, Set, Any, Tuple
from sqlalchemy.orm import Session

from app.db import repositories
from app.db.models import BlacklistEntry, UnblockRequest
from app.db.session import get_db
from app.config import BLACKLIST_PATH

# Configurar logging
logger = logging.getLogger(__name__)

def load_from_csv() -> Set[str]:
    """
    Carga la lista negra desde un archivo CSV de respaldo.
    
    Returns:
        set: Conjunto de números en la lista negra
    """
    phones = set()
    try:
        if os.path.exists(BLACKLIST_PATH):
            with open(BLACKLIST_PATH, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'phone_number' in row and row['phone_number']:
                        phones.add(row['phone_number'])
            logger.info(f"Lista negra cargada desde CSV: {len(phones)} números")
        else:
            logger.warning(f"Archivo CSV de lista negra no encontrado: {BLACKLIST_PATH}")
    except Exception as e:
        logger.error(f"Error al cargar lista negra desde CSV: {str(e)}")
    
    return phones

def export_to_csv(db: Session) -> Tuple[bool, str]:
    """
    Exporta la lista negra a un archivo CSV.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        entries = get_blacklist(db, active_only=False)
        
        with open(BLACKLIST_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=[
                "phone_number", "reason", "source", "is_active", 
                "created_at", "updated_at", "expiration_date"
            ])
            writer.writeheader()
            
            for entry in entries:
                writer.writerow({
                    "phone_number": entry["phone_number"],
                    "reason": entry["reason"],
                    "source": entry["source"],
                    "is_active": "1" if entry["is_active"] else "0",
                    "created_at": entry["created_at"],
                    "updated_at": entry["updated_at"],
                    "expiration_date": entry["expiration_date"] or ""
                })
        
        logger.info(f"Lista negra exportada a {BLACKLIST_PATH} ({len(entries)} entradas)")
        return True, f"Lista negra exportada exitosamente ({len(entries)} entradas)"
    
    except Exception as e:
        logger.error(f"Error exportando lista negra a CSV: {str(e)}")
        return False, f"Error exportando lista negra: {str(e)}"

def import_from_csv(db: Session) -> Tuple[bool, str]:
    """
    Importa la lista negra desde un archivo CSV.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        imported = 0
        updated = 0
        
        with open(BLACKLIST_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                phone_number = row["phone_number"]
                
                # Normalizar el número
                if not phone_number.startswith("whatsapp:"):
                    phone_number = f"whatsapp:{phone_number}"
                
                # Convertir campos de fecha
                expiration_date = None
                if row.get("expiration_date"):
                    try:
                        expiration_date = datetime.datetime.fromisoformat(row["expiration_date"])
                    except (ValueError, TypeError):
                        pass
                
                # Verificar si ya existe
                existing = db.query(BlacklistEntry).filter(
                    BlacklistEntry.phone_number == phone_number
                ).first()
                
                if existing:
                    # Actualizar
                    existing.reason = row["reason"]
                    existing.source = row.get("source", "import")
                    existing.is_active = row.get("is_active", "1") in ["1", "true", "True", True]
                    existing.updated_at = datetime.datetime.utcnow()
                    existing.expiration_date = expiration_date
                    updated += 1
                else:
                    # Crear nuevo
                    new_entry = BlacklistEntry(
                        phone_number=phone_number,
                        reason=row["reason"],
                        source=row.get("source", "import"),
                        is_active=row.get("is_active", "1") in ["1", "true", "True", True],
                        expiration_date=expiration_date
                    )
                    db.add(new_entry)
                    imported += 1
            
            db.commit()
        
        logger.info(f"Lista negra importada: {imported} nuevas entradas, {updated} actualizadas")
        return True, f"Lista negra importada: {imported} nuevas entradas, {updated} actualizadas"
    
    except FileNotFoundError:
        logger.warning(f"Archivo de lista negra no encontrado: {BLACKLIST_PATH}")
        return False, f"Archivo de lista negra no encontrado: {BLACKLIST_PATH}"
    except Exception as e:
        logger.error(f"Error importando lista negra desde CSV: {str(e)}")
        return False, f"Error importando lista negra: {str(e)}"

def initialize_blacklist() -> None:
    """
    Inicializa la lista negra importando desde CSV si existe.
    Esta función se debe llamar al inicio de la aplicación.
    """
    try:
        db = next(get_db())
        import_from_csv(db)
    except Exception as e:
        logger.error(f"Error inicializando lista negra: {str(e)}")

def add_to_blacklist(db: Session, phone_number: str, reason: str, source: str = "manual", 
                     expiration_date: Optional[datetime.datetime] = None) -> Tuple[bool, str]:
    """
    Añade un número a la lista negra.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono a bloquear
        reason: Razón del bloqueo
        source: Fuente que origina el bloqueo (manual, automatic, api)
        expiration_date: Fecha opcional de expiración del bloqueo
        
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        # Normalizar el número de teléfono
        if not phone_number.startswith("whatsapp:"):
            normalized_phone = f"whatsapp:{phone_number}"
        else:
            normalized_phone = phone_number
        
        # Verificar si ya existe
        existing = db.query(BlacklistEntry).filter(
            BlacklistEntry.phone_number == normalized_phone
        ).first()
        
        if existing:
            # Actualizar razón y fecha de expiración si ya existe
            existing.reason = reason
            existing.source = source
            existing.updated_at = datetime.datetime.utcnow()
            existing.expiration_date = expiration_date
            existing.is_active = True
            db.commit()
            
            logger.info(f"Actualizado número en lista negra: {normalized_phone}, razón: {reason}")
            return True, f"Número actualizado en lista negra: {normalized_phone}"
        
        # Crear nueva entrada
        new_entry = BlacklistEntry(
            phone_number=normalized_phone,
            reason=reason,
            source=source,
            expiration_date=expiration_date,
            is_active=True
        )
        
        db.add(new_entry)
        db.commit()
        
        # También guardar en archivo CSV para redundancia
        export_to_csv(db)
        
        logger.info(f"Número añadido a lista negra: {normalized_phone}, razón: {reason}")
        return True, f"Número añadido a lista negra: {normalized_phone}"
    
    except Exception as e:
        logger.error(f"Error añadiendo número a lista negra: {str(e)}")
        return False, f"Error: {str(e)}"

def remove_from_blacklist(db: Session, phone_number: str) -> Tuple[bool, str]:
    """
    Elimina un número de la lista negra.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono a desbloquear
        
    Returns:
        tuple: (éxito, mensaje)
    """
    try:
        # Normalizar el número de teléfono
        if not phone_number.startswith("whatsapp:"):
            normalized_phone = f"whatsapp:{phone_number}"
        else:
            normalized_phone = phone_number
        
        # Buscar entrada
        entry = db.query(BlacklistEntry).filter(
            BlacklistEntry.phone_number == normalized_phone
        ).first()
        
        if not entry:
            return False, f"Número no encontrado en lista negra: {normalized_phone}"
        
        # Desactivar en lugar de eliminar para mantener historial
        entry.is_active = False
        entry.updated_at = datetime.datetime.utcnow()
        db.commit()
        
        # Actualizar archivo CSV
        export_to_csv(db)
        
        logger.info(f"Número removido de lista negra: {normalized_phone}")
        return True, f"Número removido de lista negra: {normalized_phone}"
    
    except Exception as e:
        logger.error(f"Error removiendo número de lista negra: {str(e)}")
        return False, f"Error: {str(e)}"

def is_blacklisted(db: Session, phone_number: str) -> bool:
    """
    Verifica si un número está en la lista negra.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número a verificar
        
    Returns:
        bool: True si está en lista negra activa, False en caso contrario
    """
    try:
        # Normalizar el número de teléfono
        if not phone_number.startswith("whatsapp:"):
            normalized_phone = f"whatsapp:{phone_number}"
        else:
            normalized_phone = phone_number
        
        logger.debug(f"Verificando si {normalized_phone} está en lista negra")
        
        # Usar una consulta SQL directa como fallback para diagnóstico
        try:
            # Consulta directa para verificar si la tabla tiene la estructura esperada
            result = db.execute("PRAGMA table_info(blacklist_entries)").fetchall()
            columns = [row[1] for row in result]  # El nombre de la columna está en el índice 1
            logger.info(f"Columnas existentes en blacklist_entries: {columns}")
            
            # Verificar si las columnas necesarias existen
            if 'created_at' not in columns or 'updated_at' not in columns or 'expiration_date' not in columns:
                logger.warning("La tabla blacklist_entries no tiene todas las columnas necesarias. "
                              "Usando consulta SQL alternativa sin las columnas nuevas.")
                # Usar una consulta SQL directa sin las columnas que podrían faltar
                result = db.execute(
                    "SELECT id, phone_number, is_active FROM blacklist_entries "
                    "WHERE phone_number = ? AND is_active = 1", 
                    (normalized_phone,)
                ).fetchone()
                
                return result is not None
        except Exception as sql_error:
            logger.error(f"Error en consulta SQL directa: {str(sql_error)}")
        
        # Buscar entrada activa usando ORM
        entry = db.query(BlacklistEntry).filter(
            BlacklistEntry.phone_number == normalized_phone,
            BlacklistEntry.is_active == True
        ).first()
        
        # Verificar si existe y no ha expirado
        if entry:
            logger.info(f"Entrada encontrada para {normalized_phone}, is_active={entry.is_active}")
            if hasattr(entry, 'expiration_date') and entry.expiration_date and entry.expiration_date < datetime.datetime.utcnow():
                # Expirado, desactivar automáticamente
                entry.is_active = False
                if hasattr(entry, 'updated_at'):
                    entry.updated_at = datetime.datetime.utcnow()
                db.commit()
                logger.info(f"Entrada expirada para {normalized_phone}, desactivada")
                return False
            return True
        
        logger.debug(f"{normalized_phone} no está en lista negra")
        return False
    
    except Exception as e:
        logger.error(f"Error verificando lista negra para {phone_number}: {str(e)}")
        # En caso de error, mejor prevenir: consideramos que no está bloqueado
        return False

def get_blacklist(db: Session, active_only: bool = True) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de números en lista negra.
    
    Args:
        db: Sesión de base de datos
        active_only: Si es True, solo devuelve entradas activas
        
    Returns:
        list: Lista de entradas en la lista negra
    """
    try:
        query = db.query(BlacklistEntry)
        
        if active_only:
            query = query.filter(BlacklistEntry.is_active == True)
        
        entries = query.order_by(BlacklistEntry.created_at.desc()).all()
        
        # Convertir a formato serializable
        result = []
        for entry in entries:
            # Verificar expiración
            is_expired = False
            if entry.expiration_date and entry.expiration_date < datetime.datetime.utcnow():
                is_expired = True
                if entry.is_active:
                    # Actualizar estado si ha expirado
                    entry.is_active = False
                    entry.updated_at = datetime.datetime.utcnow()
            
            result.append({
                "id": entry.id,
                "phone_number": entry.phone_number,
                "reason": entry.reason,
                "source": entry.source,
                "is_active": entry.is_active and not is_expired,
                "is_expired": is_expired,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
                "expiration_date": entry.expiration_date.isoformat() if entry.expiration_date else None
            })
        
        # Guardar cambios si se actualizó algún estado
        if any(r["is_expired"] for r in result):
            db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error obteniendo lista negra: {str(e)}")
        return []

def request_unblock(db: Session, phone_number: str, reason: str = "") -> Dict[str, Any]:
    """
    Registra una solicitud de desbloqueo para un número.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número que solicita ser desbloqueado
        reason: Razón proporcionada por el usuario
        
    Returns:
        dict: Resultado de la solicitud
    """
    try:
        # Normalizar el número de teléfono
        if not phone_number.startswith("whatsapp:"):
            normalized_phone = f"whatsapp:{phone_number}"
        else:
            normalized_phone = phone_number
        
        # Verificar si está realmente en la lista negra
        if not is_blacklisted(db, normalized_phone):
            return {
                "success": False,
                "message": "Tu número no está en la lista negra"
            }
        
        # Crear código de verificación para futuro uso
        verification_code = generate_verification_code()
        
        # Registrar la solicitud
        new_request = UnblockRequest(
            phone_number=normalized_phone,
            reason=reason,
            status="pending",
            verification_code=verification_code,
            request_date=datetime.datetime.utcnow()
        )
        
        db.add(new_request)
        db.commit()
        
        logger.info(f"Solicitud de desbloqueo registrada para {normalized_phone}")
        
        return {
            "success": True,
            "request_id": new_request.id,
            "message": "Tu solicitud de desbloqueo ha sido registrada. Un administrador la revisará pronto.",
            "verification_code": verification_code
        }
    
    except Exception as e:
        logger.error(f"Error al registrar solicitud de desbloqueo: {str(e)}")
        return {
            "success": False,
            "message": f"Error al procesar tu solicitud: {str(e)}"
        }

def generate_verification_code() -> str:
    """
    Genera un código de verificación para desbloqueo.
    
    Returns:
        str: Código de verificación (alfanumérico, 8 caracteres)
    """
    return ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

def verify_and_unblock(db: Session, phone_number: str, code: str) -> Dict[str, Any]:
    """
    Verifica un código de desbloqueo y desbloquea el número si es válido.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono a desbloquear
        code: Código de verificación proporcionado
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Normalizar el número de teléfono
        if not phone_number.startswith("whatsapp:"):
            normalized_phone = f"whatsapp:{phone_number}"
        else:
            normalized_phone = phone_number
        
        # Buscar solicitud de desbloqueo pendiente con ese código
        request = db.query(UnblockRequest).filter(
            UnblockRequest.phone_number == normalized_phone,
            UnblockRequest.verification_code == code,
            UnblockRequest.status == "pending"
        ).first()
        
        if not request:
            return {
                "success": False,
                "message": "Código de verificación inválido o expirado"
            }
        
        # Actualizar estado de la solicitud
        request.status = "approved"
        request.processed_date = datetime.datetime.utcnow()
        
        # Desbloquear el número
        success, message = remove_from_blacklist(db, normalized_phone)
        
        if not success:
            request.status = "failed"
            db.commit()
            return {
                "success": False,
                "message": f"Error al desbloquear: {message}"
            }
        
        db.commit()
        
        logger.info(f"Número desbloqueado con código de verificación: {normalized_phone}")
        
        return {
            "success": True,
            "message": "Tu número ha sido desbloqueado exitosamente"
        }
    
    except Exception as e:
        logger.error(f"Error al verificar código de desbloqueo: {str(e)}")
        return {
            "success": False,
            "message": f"Error al procesar tu solicitud: {str(e)}"
        }

def get_unblock_requests(db: Session, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Obtiene las solicitudes de desbloqueo registradas.
    
    Args:
        db: Sesión de base de datos
        status: Filtrar por estado (pending, approved, rejected)
        
    Returns:
        list: Lista de solicitudes de desbloqueo
    """
    try:
        query = db.query(UnblockRequest)
        
        if status:
            query = query.filter(UnblockRequest.status == status)
        
        requests = query.order_by(UnblockRequest.request_date.desc()).all()
        
        # Convertir a formato serializable
        result = []
        for req in requests:
            result.append({
                "id": req.id,
                "phone_number": req.phone_number,
                "reason": req.reason,
                "status": req.status,
                "verification_code": req.verification_code,
                "request_date": req.request_date.isoformat() if req.request_date else None,
                "processed_date": req.processed_date.isoformat() if req.processed_date else None
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error obteniendo solicitudes de desbloqueo: {str(e)}")
        return []

def approve_unblock_request(db: Session, request_id: int) -> Dict[str, Any]:
    """
    Aprueba una solicitud de desbloqueo y desbloquea el número.
    
    Args:
        db: Sesión de base de datos
        request_id: ID de la solicitud a aprobar
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Buscar solicitud
        request = db.query(UnblockRequest).filter(
            UnblockRequest.id == request_id
        ).first()
        
        if not request:
            return {
                "success": False,
                "message": f"Solicitud #{request_id} no encontrada"
            }
        
        # Verificar si no está ya procesada
        if request.status != "pending":
            return {
                "success": False,
                "message": f"La solicitud ya fue {request.status}"
            }
        
        # Desbloquear el número
        success, message = remove_from_blacklist(db, request.phone_number)
        
        # Actualizar estado de la solicitud
        request.status = "approved" if success else "failed"
        request.processed_date = datetime.datetime.utcnow()
        db.commit()
        
        if success:
            logger.info(f"Solicitud #{request_id} aprobada y número {request.phone_number} desbloqueado")
            return {
                "success": True,
                "message": f"Número {request.phone_number} desbloqueado exitosamente"
            }
        else:
            logger.error(f"Error al aprobar solicitud #{request_id}: {message}")
            return {
                "success": False,
                "message": f"Error al desbloquear: {message}"
            }
    
    except Exception as e:
        logger.error(f"Error aprobando solicitud de desbloqueo: {str(e)}")
        return {
            "success": False,
            "message": f"Error al procesar: {str(e)}"
        }

def reject_unblock_request(db: Session, request_id: int, reason: str = "") -> Dict[str, Any]:
    """
    Rechaza una solicitud de desbloqueo.
    
    Args:
        db: Sesión de base de datos
        request_id: ID de la solicitud a rechazar
        reason: Razón del rechazo
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Buscar solicitud
        request = db.query(UnblockRequest).filter(
            UnblockRequest.id == request_id
        ).first()
        
        if not request:
            return {
                "success": False,
                "message": f"Solicitud #{request_id} no encontrada"
            }
        
        # Verificar si no está ya procesada
        if request.status != "pending":
            return {
                "success": False,
                "message": f"La solicitud ya fue {request.status}"
            }
        
        # Actualizar estado de la solicitud
        request.status = "rejected"
        request.rejection_reason = reason
        request.processed_date = datetime.datetime.utcnow()
        db.commit()
        
        logger.info(f"Solicitud #{request_id} rechazada. Razón: {reason}")
        
        return {
            "success": True,
            "message": f"Solicitud rechazada exitosamente"
        }
    
    except Exception as e:
        logger.error(f"Error rechazando solicitud de desbloqueo: {str(e)}")
        return {
            "success": False,
            "message": f"Error al procesar: {str(e)}"
        }