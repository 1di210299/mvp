import requests
import logging
import json
import os
from datetime import datetime
from twilio.rest import Client
from pprint import pformat

from app.config import (
    TWILIO_ACCOUNT_SID, 
    TWILIO_AUTH_TOKEN, 
    TWILIO_PHONE_NUMBER,
    WEBHOOK_URL
)

logger = logging.getLogger("app.diagnose_whatsapp")

def diagnose_twilio_configuration():
    """
    Diagnostica la configuración de Twilio y WhatsApp de manera completa
    y detallada, verificando todos los aspectos posibles.
    
    Returns:
        dict: Resultados del diagnóstico
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "account_sid": mask_string(TWILIO_ACCOUNT_SID),
            "phone_number": TWILIO_PHONE_NUMBER,
            "webhook_url": WEBHOOK_URL
        },
        "account_status": None,
        "sandbox_status": None,
        "incoming_messages": [],
        "outgoing_messages": [],
        "webhook_config": None,
        "issues": [],
        "recommendations": []
    }
    
    # Verificar credenciales
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        results["issues"].append("Faltan credenciales de Twilio")
        return results
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Verificar estado de la cuenta
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        results["account_status"] = {
            "status": account.status,
            "name": account.friendly_name,
            "type": account.type
        }
        
        if account.status != "active":
            results["issues"].append(f"Cuenta Twilio no activa: {account.status}")
            results["recommendations"].append("Active su cuenta de Twilio o verifique sus pagos pendientes")
        
        # Verificar WhatsApp Sandbox
        try:
            # Obtener información del número de WhatsApp
            incoming_phone_numbers = client.incoming_phone_numbers.list(phone_number=TWILIO_PHONE_NUMBER)
            
            if not incoming_phone_numbers:
                # Si no encontramos exactamente ese número, intentamos listar todos
                incoming_phone_numbers = client.incoming_phone_numbers.list()
                
            if incoming_phone_numbers:
                number = incoming_phone_numbers[0]
                results["webhook_config"] = {
                    "sms_url": number.sms_url,
                    "sms_method": number.sms_method,
                    "voice_url": number.voice_url,
                    "status_callback": number.status_callback
                }
                
                # Verificar si el webhook coincide
                if number.sms_url != WEBHOOK_URL:
                    results["issues"].append(f"URL de webhook no coincide. Configurado: {number.sms_url}, Esperado: {WEBHOOK_URL}")
                    results["recommendations"].append(f"Configure el webhook en Twilio para que apunte a: {WEBHOOK_URL}")
            else:
                results["issues"].append("No se encontró el número en la cuenta de Twilio")
        except Exception as e:
            results["issues"].append(f"Error al verificar configuración del número: {str(e)}")
        
        # Verificar mensajes recientes (últimas 24 horas)
        try:
            messages = client.messages.list(to=TWILIO_PHONE_NUMBER, limit=20)
            for msg in messages:
                results["incoming_messages"].append({
                    "from": msg.from_,
                    "body": msg.body[:50] + "..." if msg.body and len(msg.body) > 50 else msg.body,
                    "status": msg.status,
                    "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                    "error_code": msg.error_code,
                    "error_message": msg.error_message
                })
                
                if msg.status == "failed":
                    results["issues"].append(f"Mensaje fallido: {msg.error_message} (código: {msg.error_code})")
            
            messages_from = client.messages.list(from_=TWILIO_PHONE_NUMBER, limit=20)
            for msg in messages_from:
                results["outgoing_messages"].append({
                    "to": msg.to,
                    "body": msg.body[:50] + "..." if msg.body and len(msg.body) > 50 else msg.body,
                    "status": msg.status,
                    "date_sent": msg.date_sent.isoformat() if msg.date_sent else None,
                    "error_code": msg.error_code,
                    "error_message": msg.error_message
                })
                
                if msg.status == "failed":
                    results["issues"].append(f"Mensaje fallido: {msg.error_message} (código: {msg.error_code})")
        except Exception as e:
            results["issues"].append(f"Error al verificar mensajes: {str(e)}")
        
        # Verificar estado específico de WhatsApp Sandbox
        try:
            # Esta es una aproximación, no hay una API directa para el estado del sandbox
            if not any(msg.get("from", "").startswith("whatsapp:") for msg in results["incoming_messages"]):
                results["issues"].append("No se han recibido mensajes de WhatsApp recientemente")
                results["recommendations"].append("Asegúrese de que su número está registrado en el Sandbox de WhatsApp enviando 'join <your-sandbox-code>' al número de WhatsApp")
            
            results["sandbox_status"] = "active" if not any(i.startswith("No se han recibido mensajes") for i in results["issues"]) else "inactive"
            
        except Exception as e:
            results["issues"].append(f"Error al verificar estado de WhatsApp: {str(e)}")
        
        # Verificar si el número del remitente está registrado (su número)
        try:
            if results["incoming_messages"]:
                sender_numbers = set(msg.get("from") for msg in results["incoming_messages"] if msg.get("from"))
                
                if not sender_numbers:
                    results["issues"].append("No se encontraron números de remitentes")
                    results["recommendations"].append("Intente enviar un mensaje de prueba al número de Twilio")
                else:
                    results["sender_numbers"] = list(sender_numbers)
                    
                    # Verificar si algún número está bloqueado o tiene problemas
                    for sender in sender_numbers:
                        if sender.startswith("whatsapp:"):
                            # Intentar encontrar mensajes fallidos de este remitente
                            failed_msgs = [m for m in results["outgoing_messages"] if m.get("to") == sender and m.get("status") == "failed"]
                            
                            if failed_msgs:
                                reasons = set(m.get("error_message") for m in failed_msgs if m.get("error_message"))
                                results["issues"].append(f"Mensajes fallidos a {sender}: {', '.join(reasons)}")
                                
                                if any("not an active" in r.lower() for r in reasons):
                                    results["recommendations"].append(f"El número {sender} no parece estar activo en WhatsApp o no ha enviado 'join' al sandbox")
                                elif any("opt-out" in r.lower() for r in reasons):
                                    results["recommendations"].append(f"El número {sender} ha optado por no recibir mensajes (STOP)")
        except Exception as e:
            results["issues"].append(f"Error al verificar números de remitentes: {str(e)}")
        
    except Exception as e:
        results["issues"].append(f"Error al conectar con la API de Twilio: {str(e)}")
        logger.error(f"Error en diagnóstico: {str(e)}", exc_info=True)
    
    # Verificación adicional: probar el webhook directamente
    try:
        # Hacer una solicitud GET al webhook para verificar que responde
        webhook_url = WEBHOOK_URL.split("/api/webhooks")[0] + "/health"  # Usar el endpoint de health
        response = requests.get(webhook_url, timeout=5)
        
        results["webhook_health_check"] = {
            "status_code": response.status_code,
            "response": response.text[:100] + "..." if len(response.text) > 100 else response.text
        }
        
        if response.status_code != 200:
            results["issues"].append(f"El endpoint de health check respondió con código {response.status_code}")
            results["recommendations"].append("Verifique que su servidor esté funcionando correctamente")
    except Exception as e:
        results["issues"].append(f"No se pudo conectar al webhook: {str(e)}")
        results["recommendations"].append("Verifique que su servidor esté en línea y accesible desde internet")
    
    # Resumen de problemas encontrados
    if not results["issues"]:
        results["status"] = "healthy"
        results["summary"] = "No se encontraron problemas en la configuración de Twilio/WhatsApp"
    else:
        results["status"] = "issues_found"
        results["summary"] = f"Se encontraron {len(results['issues'])} problemas que podrían afectar la funcionalidad"
    
    return results

def mask_string(text):
    """Enmascara una cadena para mostrar solo los primeros y últimos caracteres"""
    if not text:
        return ""
    if len(text) <= 8:
        return "****"
    return text[:4] + "****" + text[-4:]

def save_diagnostics(results):
    """Guarda los resultados del diagnóstico en un archivo"""
    try:
        os.makedirs(os.path.join("logs", "diagnostics"), exist_ok=True)
        
        filename = f"whatsapp_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join("logs", "diagnostics", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        return filepath
    except Exception as e:
        logger.error(f"Error al guardar diagnóstico: {str(e)}")
        return None

def test_send_message(to_number):
    """
    Envía un mensaje de prueba a un número específico
    
    Args:
        to_number (str): Número al que enviar el mensaje (con formato whatsapp:+123456789)
        
    Returns:
        dict: Resultado del intento de envío
    """
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"
    
    result = {
        "success": False,
        "message": "",
        "error": None,
        "sid": None,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Asegurar que tenemos el formato correcto para el número
        from_number = TWILIO_PHONE_NUMBER
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number.replace('+', '')}"
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=from_number,
            body="Este es un mensaje de prueba para verificar la conexión de WhatsApp. Por favor, responda con 'OK' si lo recibe.",
            to=to_number
        )
        
        result["success"] = True
        result["message"] = "Mensaje enviado correctamente"
        result["sid"] = message.sid
        result["details"] = {
            "status": message.status,
            "error_code": message.error_code,
            "error_message": message.error_message,
            "date_created": message.date_created.isoformat() if message.date_created else None,
        }
        
    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"Error al enviar mensaje: {str(e)}"
        logger.error(f"Error al enviar mensaje de prueba: {str(e)}", exc_info=True)
        
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Iniciando diagnóstico de WhatsApp/Twilio...")
    
    results = diagnose_twilio_configuration()
    filepath = save_diagnostics(results)
    
    logger.info(f"Diagnóstico completado. Archivo guardado en: {filepath}")
    logger.info(f"Estado: {results['status']}")
    
    if results['issues']:
        logger.info("Problemas encontrados:")
        for i, issue in enumerate(results['issues'], 1):
            logger.info(f"  {i}. {issue}")
    
    if results['recommendations']:
        logger.info("Recomendaciones:")
        for i, rec in enumerate(results['recommendations'], 1):
            logger.info(f"  {i}. {rec}")
    
    # Puedes descomentar estas líneas para probar el envío a un número específico
    # your_number = "+51955743403"  # Cambia esto por tu número
    # test_result = test_send_message(your_number)
    # logger.info(f"Resultado de prueba de envío: {test_result['message']}")
