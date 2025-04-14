import requests
import logging
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from app.config.settings import WEBHOOK_URL
from app.utils.whatsapp import check_whatsapp_connection

logger = logging.getLogger("app.utils.verify_config")

def verify_twilio_configuration():
    """
    Verifica la configuración completa de Twilio y retorna un informe
    """
    results = {
        "credentials": False,
        "account_active": False,
        "webhook_url_match": False,
        "phone_number_valid": False,
        "issues": []
    }
    
    # Verificar credenciales
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]):
        results["issues"].append("Faltan credenciales de Twilio (ACCOUNT_SID o AUTH_TOKEN)")
        return results
    
    results["credentials"] = True
    
    # Verificar que la cuenta está activa
    try:
        # Obtener estado de la conexión
        whatsapp_status = check_whatsapp_connection()
        results["account_active"] = whatsapp_status["status"] == "connected"
        
        if not results["account_active"]:
            results["issues"].append(f"Cuenta Twilio no activa: {whatsapp_status['details']}")
    except Exception as e:
        results["issues"].append(f"Error al verificar cuenta Twilio: {str(e)}")
    
    # Verificar número de teléfono
    if not TWILIO_PHONE_NUMBER:
        results["issues"].append("Falta configurar TWILIO_PHONE_NUMBER")
    else:
        results["phone_number_valid"] = True
        
    # Verificar webhook
    try:
        # Obtener la configuración actual del webhook en Twilio
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json"
        
        response = requests.get(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        
        if response.status_code == 200:
            phone_numbers = response.json().get("incoming_phone_numbers", [])
            
            # Buscar el número de WhatsApp/Sandbox
            for number in phone_numbers:
                if number.get("phone_number") == TWILIO_PHONE_NUMBER:
                    twilio_webhook = number.get("sms_url")
                    if twilio_webhook == WEBHOOK_URL:
                        results["webhook_url_match"] = True
                    else:
                        results["issues"].append(f"URL de webhook no coincide. Twilio: {twilio_webhook}, Local: {WEBHOOK_URL}")
        else:
            results["issues"].append(f"Error al verificar webhook: {response.status_code}")
    except Exception as e:
        results["issues"].append(f"Error al verificar configuración del webhook: {str(e)}")
    
    # Todo correcto si no hay problemas
    results["all_good"] = len(results["issues"]) == 0
    
    return results
