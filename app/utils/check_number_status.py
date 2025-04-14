from twilio.rest import Client
import logging
from datetime import datetime
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

logger = logging.getLogger("app.utils.check_number")

def check_whatsapp_number_status(phone_number):
    """
    Verifica el estado de un número de WhatsApp, incluyendo si está activo
    en el sandbox, si ha enviado mensajes, si ha recibido mensajes, etc.
    
    Args:
        phone_number (str): Número a verificar (con o sin prefijo whatsapp:)
        
    Returns:
        dict: Información sobre el estado del número
    """
    if not phone_number.startswith("whatsapp:") and phone_number.startswith("+"):
        whatsapp_number = f"whatsapp:{phone_number}"
    else:
        whatsapp_number = phone_number
    
    results = {
        "number": phone_number,
        "whatsapp_formatted": whatsapp_number,
        "active_in_sandbox": False,
        "messages_received": 0,
        "messages_sent": 0,
        "last_message_received": None,
        "last_message_sent": None,
        "opt_out_status": "unknown",
        "issues": []
    }
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Buscar mensajes recibidos de este número
        messages_received = client.messages.list(
            from_=whatsapp_number, 
            to=f"whatsapp:{TWILIO_PHONE_NUMBER.replace('whatsapp:', '')}" 
                if not TWILIO_PHONE_NUMBER.startswith('whatsapp:') else TWILIO_PHONE_NUMBER,
            limit=20
        )
        
        # Buscar mensajes enviados a este número
        messages_sent = client.messages.list(
            to=whatsapp_number,
            from_=f"whatsapp:{TWILIO_PHONE_NUMBER.replace('whatsapp:', '')}" 
                if not TWILIO_PHONE_NUMBER.startswith('whatsapp:') else TWILIO_PHONE_NUMBER,
            limit=20
        )
        
        # Analizar mensajes recibidos
        join_message = None
        results["messages_received"] = len(messages_received)
        
        if messages_received:
            # Ordenar por fecha (más reciente primero)
            messages_received.sort(key=lambda x: x.date_created, reverse=True)
            results["last_message_received"] = {
                "date": messages_received[0].date_created.isoformat(),
                "body": messages_received[0].body,
                "status": messages_received[0].status
            }
            
            # Verificar si hay un mensaje de unión al sandbox
            join_message = next((msg for msg in messages_received if msg.body and 
                              any(keyword in msg.body.lower() for keyword in ["join", "unirse"])), None)
            
            if join_message:
                results["active_in_sandbox"] = True
            else:
                results["issues"].append("No se encontró un mensaje 'join' para activar el sandbox")
        else:
            results["issues"].append("No se han recibido mensajes de este número")
        
        # Analizar mensajes enviados
        results["messages_sent"] = len(messages_sent)
        
        if messages_sent:
            # Ordenar por fecha (más reciente primero)
            messages_sent.sort(key=lambda x: x.date_created, reverse=True)
            
            last_message = messages_sent[0]
            results["last_message_sent"] = {
                "date": last_message.date_created.isoformat(),
                "body": last_message.body,
                "status": last_message.status,
                "error_code": last_message.error_code,
                "error_message": last_message.error_message
            }
            
            # Verificar si hay errores en los mensajes enviados
            failed_messages = [m for m in messages_sent if m.status == "failed"]
            
            if failed_messages:
                for msg in failed_messages[:3]:  # Mostrar hasta 3 mensajes fallidos
                    results["issues"].append(f"Mensaje fallido ({msg.date_created.isoformat()}): {msg.error_message} (código: {msg.error_code})")
                
                # Verificar si el número ha optado por no recibir mensajes (STOP)
                if any("opt-out" in m.error_message.lower() if m.error_message else False for m in failed_messages):
                    results["opt_out_status"] = "opted_out"
                    results["issues"].append("El número ha optado por no recibir mensajes (envió STOP)")
                
                # Verificar si el número no está activo en WhatsApp
                if any("not an active" in m.error_message.lower() if m.error_message else False for m in failed_messages):
                    results["active_in_sandbox"] = False
                    results["issues"].append("El número no parece estar activo en WhatsApp o no ha enviado 'join' al sandbox")
            else:
                results["opt_out_status"] = "receiving_messages"
        else:
            results["issues"].append("No se han enviado mensajes a este número")
        
        # Determinar el estado general
        if not results["messages_received"] and not results["messages_sent"]:
            results["status"] = "unknown"
        elif results["active_in_sandbox"] and results["opt_out_status"] == "receiving_messages":
            results["status"] = "active"
        elif results["opt_out_status"] == "opted_out":
            results["status"] = "opted_out"
        elif not results["active_in_sandbox"]:
            results["status"] = "inactive_in_sandbox"
        else:
            results["status"] = "issues_detected"
            
        # Recomendaciones basadas en el estado
        results["recommendations"] = []
        
        if results["status"] == "unknown":
            results["recommendations"].append(f"Envíe 'join move-weather' (o el código de su sandbox) al número {TWILIO_PHONE_NUMBER}")
        elif results["status"] == "opted_out":
            results["recommendations"].append(f"Envíe 'START' al número {TWILIO_PHONE_NUMBER} para volver a recibir mensajes")
        elif results["status"] == "inactive_in_sandbox":
            results["recommendations"].append(f"Envíe 'join move-weather' (o el código de su sandbox) al número {TWILIO_PHONE_NUMBER}")
        
    except Exception as e:
        logger.error(f"Error al verificar estado del número: {str(e)}")
        results["issues"].append(f"Error en la verificación: {str(e)}")
        results["status"] = "error"
    
    return results
