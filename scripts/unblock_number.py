#!/usr/bin/env python3
"""
Utilidad para desbloquear números de teléfono en el sistema WhatsApp Sales Bot
"""
import sys
import os
import argparse
import requests
import logging
from pathlib import Path

# Add project root to path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('unblock_tool')

def normalize_phone(phone_number):
    """Normalize phone number format"""
    cleaned = ''.join(c for c in phone_number if c.isalnum() or c in ('+', ':'))
    if not cleaned.startswith("whatsapp:"):
        return f"whatsapp:{cleaned}"
    return cleaned

def submit_unblock_request(phone_number, reason, api_url="http://localhost:8000"):
    """Submit an unblock request to the API"""
    url = f"{api_url}/api/unblock/request"
    data = {
        "phone_number": normalize_phone(phone_number),
        "reason": reason
    }
    
    try:
        logger.info(f"Enviando solicitud a {url}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            logger.info("¡Solicitud registrada exitosamente!")
            if "verification_code" in result:
                logger.info(f"Código de verificación: {result['verification_code']}")
                logger.info("Guarda este código. Lo necesitarás para verificar cuando el administrador apruebe tu solicitud.")
            return True
        else:
            logger.error(f"Error: {result.get('message', 'Error desconocido')}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión: {str(e)}")
        logger.info("Verifica que el servidor esté ejecutándose y que la URL sea correcta.")
        return False

def verify_unblock_code(phone_number, code, api_url="http://localhost:8000"):
    """Verify an unblock code to unblock a number"""
    url = f"{api_url}/api/unblock/verify"
    data = {
        "phone_number": normalize_phone(phone_number),
        "code": code
    }
    
    try:
        logger.info(f"Enviando código de verificación a {url}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            logger.info("¡Tu número ha sido desbloqueado exitosamente!")
            return True
        else:
            logger.error(f"Error: {result.get('message', 'Error desconocido')}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión: {str(e)}")
        logger.info("Verifica que el servidor esté ejecutándose y que la URL sea correcta.")
        return False

def check_status(phone_number, api_url="http://localhost:8000"):
    """Check if a phone number is blocked"""
    # Try both with and without the whatsapp prefix
    urls = [
        f"{api_url}/api/whatsapp/unblock-instructions/{normalize_phone(phone_number)}",
        f"{api_url}/api/unblock/status/{normalize_phone(phone_number)}"
    ]
    
    for url in urls:
        try:
            logger.info(f"Verificando estado en {url}")
            response = requests.get(url)
            if response.status_code == 404:
                logger.info(f"Endpoint no encontrado: {url}")
                continue
                
            response.raise_for_status()
            result = response.json()
            
            if result.get("is_blocked", False):
                logger.info("Este número está bloqueado. Puedes solicitar su desbloqueo.")
                if "instructions" in result:
                    for instr in result["instructions"]:
                        logger.info(f"- {instr}")
            else:
                logger.info("¡Buenas noticias! Este número no está bloqueado.")
            
            return result
        
        except requests.exceptions.RequestException as e:
            continue
    
    # If we get here, both attempts failed
    logger.error("No se pudo comprobar el estado del número.")
    logger.error("Verifica que el servidor esté ejecutándose y que la URL sea correcta.")
    return {"error": "No se pudo conectar con la API"}

def main():
    parser = argparse.ArgumentParser(description="Herramienta para desbloqueo de números en WhatsApp Sales Bot")
    parser.add_argument("--api", default="http://localhost:8000", help="URL base de la API")
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Command: check
    check_parser = subparsers.add_parser("check", help="Verificar estado de bloqueo de un número")
    check_parser.add_argument("phone", help="Número de teléfono a verificar")
    
    # Command: request
    request_parser = subparsers.add_parser("request", help="Solicitar desbloqueo de un número")
    request_parser.add_argument("phone", help="Número de teléfono a desbloquear")
    request_parser.add_argument("--reason", "-r", default="", help="Razón para solicitar el desbloqueo")
    
    # Command: verify
    verify_parser = subparsers.add_parser("verify", help="Verificar código de desbloqueo")
    verify_parser.add_argument("phone", help="Número de teléfono")
    verify_parser.add_argument("code", help="Código de verificación recibido")
    
    args = parser.parse_args()
    
    if args.command == "check":
        check_status(args.phone, args.api)
    elif args.command == "request":
        if not args.reason:
            args.reason = input("Por favor, proporciona una razón para el desbloqueo: ")
        submit_unblock_request(args.phone, args.reason, args.api)
    elif args.command == "verify":
        verify_unblock_code(args.phone, args.code, args.api)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
