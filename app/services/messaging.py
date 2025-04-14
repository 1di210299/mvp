from app.utils.whatsapp import update_message_sent

def send_whatsapp_message(to, message):
    """
    Envía un mensaje de WhatsApp utilizando Twilio.
    
    Args:
        to (str): Número de teléfono del destinatario en formato internacional.
        message (str): Contenido del mensaje a enviar.
    """
    # Código para enviar mensajes usando Twilio
    try:
        # Aquí iría la lógica para enviar el mensaje
        # Por ejemplo, utilizando Twilio API
        pass
    
        # Actualizar el estado después de enviar un mensaje
        update_message_sent()
    
    except Exception as e:
        # Manejo de errores
        raise e