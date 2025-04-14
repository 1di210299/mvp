import logging
import os
from typing import List, Set

logger = logging.getLogger("app.security.access_control")

# Whitelist de números para evitar que sean bloqueados
WHITELISTED_NUMBERS: Set[str] = set(phone.strip() for phone in os.getenv("WHITELISTED_NUMBERS", "").split(",") if phone.strip())
BLOCKED_NUMBERS: Set[str] = set()  # Lista dinámica de números bloqueados

def is_whitelisted(phone_number: str) -> bool:
    """Verifica si un número está en la whitelist"""
    if not phone_number:
        return False
    
    # Normalizar el número (eliminar espacios, '+', etc.)
    if phone_number.startswith("whatsapp:"):
        phone_number = phone_number[9:]  # Remove "whatsapp:" prefix
    
    normalized = ''.join(c for c in phone_number if c.isdigit())
    
    # Comprobar si el número normalizado está en la whitelist
    for white in WHITELISTED_NUMBERS:
        if not white:
            continue
        white_normalized = ''.join(c for c in white if c.isdigit())
        if normalized.endswith(white_normalized) or white_normalized.endswith(normalized):
            return True
    
    return False

def add_to_whitelist(phone_number: str) -> bool:
    """Añade un número a la whitelist"""
    global WHITELISTED_NUMBERS
    if not phone_number:
        return False
    
    # Ensure we store with + format but without whatsapp: prefix
    if phone_number.startswith("whatsapp:"):
        phone_number = phone_number[9:]
    
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number
    
    WHITELISTED_NUMBERS.add(phone_number)
    
    # Si estaba en la lista de bloqueados, lo quitamos
    if phone_number in BLOCKED_NUMBERS:
        BLOCKED_NUMBERS.remove(phone_number)
    
    logger.info(f"Número {phone_number} añadido a la whitelist")
    return True

def block_number(phone_number: str, reason: str = "Threat detection system") -> bool:
    """Add a number to the blocked list"""
    global BLOCKED_NUMBERS
    if not phone_number or is_whitelisted(phone_number):
        return False
    
    BLOCKED_NUMBERS.add(phone_number)
    logger.info(f"Number {phone_number} blocked. Reason: {reason}")
    return True

def is_blocked(phone_number: str) -> bool:
    """Check if a number is blocked"""
    if not phone_number:
        return False
    
    # If it's in the whitelist, it's never blocked
    if is_whitelisted(phone_number):
        return False
    
    return phone_number in BLOCKED_NUMBERS

def get_blocked_numbers() -> List[str]:
    """Returns the list of blocked numbers"""
    return list(BLOCKED_NUMBERS)

def get_whitelist() -> List[str]:
    """Returns the list of whitelisted numbers"""
    return list(WHITELISTED_NUMBERS)
