import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

# Configurar logging
logger = logging.getLogger(__name__)

# Inicializar cliente de Twilio
try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Cliente Twilio inicializado correctamente")
except Exception as e:
    client = None
    logger.error(f"Error al inicializar cliente Twilio: {str(e)}")

def send_message(to: str, message: str, media_url: str = None) -> dict:
    """
    Envía un mensaje de WhatsApp usando la API de Twilio.
    
    Args:
        to: Número de teléfono de destino (debe incluir 'whatsapp:' como prefijo)
        message: Texto del mensaje a enviar
        media_url: URL opcional de una imagen para adjuntar
        
    Returns:
        dict: Información sobre el mensaje enviado
    """
    if not client:
        logger.error("Cliente Twilio no inicializado. Verifique las credenciales.")
        return {
            "status": "error",
            "message": "Cliente Twilio no inicializado"
        }
    
    try:
        # Asegurarse de que el número tenga el formato correcto
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        
        # Crear parámetros del mensaje
        params = {
            "from_": TWILIO_PHONE_NUMBER,
            "body": message,
            "to": to
        }
        
        # Añadir media_url si se proporciona
        if media_url:
            params["media_url"] = [media_url]
        
        # Enviar mensaje
        twilio_message = client.messages.create(**params)
        
        logger.info(f"Mensaje enviado a {to}: SID {twilio_message.sid}")
        
        return {
            "status": "success",
            "message_sid": twilio_message.sid,
            "to": to
        }
        
    except TwilioRestException as e:
        logger.error(f"Error de Twilio al enviar mensaje a {to}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error de Twilio: {str(e)}",
            "code": e.code
        }
    except Exception as e:
        logger.error(f"Error desconocido al enviar mensaje a {to}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error inesperado: {str(e)}"
        }

def send_template_message(to: str, template_name: str, language: str = "es", params: list = None) -> dict:
    """
    Envía un mensaje de plantilla de WhatsApp.
    
    Args:
        to: Número de teléfono de destino (debe incluir 'whatsapp:' como prefijo)
        template_name: Nombre de la plantilla aprobada en WhatsApp Business
        language: Código de idioma de la plantilla
        params: Lista de parámetros para la plantilla
        
    Returns:
        dict: Información sobre el mensaje enviado
    """
    if not client:
        logger.error("Cliente Twilio no inicializado. Verifique las credenciales.")
        return {
            "status": "error",
            "message": "Cliente Twilio no inicializado"
        }
    
    try:
        # Asegurarse de que el número tenga el formato correcto
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        
        # Crear la estructura de componentes para la plantilla
        components = []
        if params:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params]
            })
        
        # Enviar mensaje de plantilla
        twilio_message = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=to,
            content_sid=template_name,
            content_variables=components
        )
        
        logger.info(f"Mensaje de plantilla enviado a {to}: SID {twilio_message.sid}")
        
        return {
            "status": "success",
            "message_sid": twilio_message.sid,
            "to": to
        }
        
    except TwilioRestException as e:
        logger.error(f"Error de Twilio al enviar plantilla a {to}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error de Twilio: {str(e)}",
            "code": e.code
        }
    except Exception as e:
        logger.error(f"Error desconocido al enviar plantilla a {to}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error inesperado: {str(e)}"
        }