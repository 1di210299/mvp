import logging
import csv
import os
from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session

from app.db import repositories
from app.db.models import BlacklistEntry

# Configurar logging
logger = logging.getLogger(__name__)

# Path para el archivo CSV de respaldo (opcional)
BLACKLIST_CSV_PATH = "data/blacklist.csv"

def load_from_csv() -> Set[str]:
    """
    Carga la lista negra desde un archivo CSV de respaldo.
    
    Returns:
        set: Conjunto de números en la lista negra
    """
    phones = set()
    try:
        if os.path.exists(BLACKLIST_CSV_PATH):
            with open(BLACKLIST_CSV_PATH, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'phone_number' in row and row['phone_number']:
                        phones.add(row['phone_number'])
            logger.info(f"Lista negra cargada desde CSV: {len(phones)} números")
        else:
            logger.warning(f"Archivo CSV de lista negra no encontrado: {BLACKLIST_CSV_PATH}")
    except Exception as e:
        logger.error(f"Error al cargar lista negra desde CSV: {str(e)}")
    
    return phones

def save_to_csv(db: Session) -> bool:
    """
    Guarda la lista negra actual a un archivo CSV de respaldo.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(BLACKLIST_CSV_PATH), exist_ok=True)
        
        # Obtener todos los registros de la lista negra
        blacklist_entries = db.query(BlacklistEntry).all()
        
        # Guardar en CSV
        with open(BLACKLIST_CSV_PATH, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['phone_number', 'reason', 'created_at'])
            writer.writeheader()
            for entry in blacklist_entries:
                writer.writerow({
                    'phone_number': entry.phone_number,
                    'reason': entry.reason or '',
                    'created_at': entry.created_at.isoformat() if entry.created_at else ''
                })
        
        logger.info(f"Lista negra guardada en CSV: {len(blacklist_entries)} números")
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar lista negra a CSV: {str(e)}")
        return False

def sync_with_csv(db: Session) -> int:
    """
    Sincroniza la base de datos con el archivo CSV de respaldo.
    
    Añade números que están en el CSV pero no en la base de datos.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        int: Número de registros añadidos
    """
    try:
        # Cargar números desde CSV
        csv_phones = load_from_csv()
        if not csv_phones:
            return 0
        
        # Verificar cuáles ya existen en la base de datos
        added_count = 0
        for phone in csv_phones:
            if not repositories.is_phone_blacklisted(db, phone):
                # Añadir a la base de datos
                repositories.add_to_blacklist(
                    db=db,
                    phone_number=phone,
                    reason="Importado desde CSV de respaldo"
                )
                added_count += 1
        
        logger.info(f"Sincronización completada: {added_count} números añadidos desde CSV")
        return added_count
        
    except Exception as e:
        logger.error(f"Error al sincronizar lista negra con CSV: {str(e)}")
        return 0

def is_blacklisted(db: Session, phone_number: str) -> bool:
    """
    Verifica si un número está en la lista negra.
    
    Esta es una función wrapper sobre el repositorio para añadir
    funcionalidad adicional si es necesario.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono a verificar
        
    Returns:
        bool: True si está en la lista negra, False en caso contrario
    """
    # Normalizar el número (eliminar espacios, guiones, etc)
    normalized_phone = phone_number.strip().replace(" ", "").replace("-", "")
    
    # Si comienza con "whatsapp:", usar todo el string
    # De lo contrario, intentar con ambas formas
    if normalized_phone.startswith("whatsapp:"):
        return repositories.is_phone_blacklisted(db, normalized_phone)
    else:
        # Verificar con y sin el prefijo
        return (
            repositories.is_phone_blacklisted(db, normalized_phone) or 
            repositories.is_phone_blacklisted(db, f"whatsapp:{normalized_phone}")
        )

def add_to_blacklist(db: Session, phone_number: str, reason: Optional[str] = None) -> bool:
    """
    Añade un número a la lista negra.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono a añadir
        reason: Motivo opcional
        
    Returns:
        bool: True si se añadió correctamente, False en caso contrario
    """
    try:
        # Normalizar el número
        normalized_phone = phone_number.strip().replace(" ", "").replace("-", "")
        if not normalized_phone.startswith("whatsapp:"):
            normalized_phone = f"whatsapp:{normalized_phone}"
        
        # Verificar si ya existe
        if repositories.is_phone_blacklisted(db, normalized_phone):
            logger.info(f"Número ya está en lista negra: {normalized_phone}")
            return True
        
        # Añadir a la base de datos
        entry = repositories.add_to_blacklist(db, normalized_phone, reason)
        
        # Actualizar CSV de respaldo
        save_to_csv(db)
        
        logger.info(f"Número añadido a lista negra: {normalized_phone}")
        return True
        
    except Exception as e:
        logger.error(f"Error al añadir a lista negra: {str(e)}")
        return False