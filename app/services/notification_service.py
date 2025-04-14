import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

from app.config import (
    ADMIN_EMAIL,
    NOTIFICATION_TELEGRAM_BOT_TOKEN,
    NOTIFICATION_TELEGRAM_CHAT_ID
)

# Configurar logging
logger = logging.getLogger(__name__)

def send_email_alert(subject: str, message: str, to_email: str = ADMIN_EMAIL) -> bool:
    """
    Envía una alerta por correo electrónico.
    
    Esta función está comentada porque requiere configuración adicional de SMTP.
    Para implementarla, descomentar y añadir las variables de entorno necesarias.
    
    Args:
        subject: Asunto del correo
        message: Contenido del mensaje
        to_email: Dirección de correo del destinatario
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    # NOTA: Esta es una implementación básica que requiere configuración adicional
    # para un entorno de producción. Por ahora se deja comentada.
    """
    try:
        # Configurar servidor SMTP (ejemplo con Gmail)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_user = "tu_correo@gmail.com"  # Añadir a variables de entorno
        smtp_password = "tu_password"       # Añadir a variables de entorno
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Añadir cuerpo del mensaje
        msg.attach(MIMEText(message, 'plain'))
        
        # Conectar y enviar
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Alerta enviada por correo a {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return False
    """
    # Simulamos el envío en modo desarrollo
    logger.info(f"[SIMULACIÓN] Email enviado a {to_email}:")
    logger.info(f"Asunto: {subject}")
    logger.info(f"Mensaje: {message}")
    return True

def send_telegram_alert(message: str) -> bool:
    """
    Envía una alerta por Telegram.
    
    Args:
        message: Contenido del mensaje
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    if not NOTIFICATION_TELEGRAM_BOT_TOKEN or not NOTIFICATION_TELEGRAM_CHAT_ID:
        # Si no hay configuración de Telegram, simulamos el envío
        logger.info(f"[SIMULACIÓN] Telegram enviado:")
        logger.info(f"Mensaje: {message}")
        return True
    
    try:
        url = f"https://api.telegram.org/bot{NOTIFICATION_TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": NOTIFICATION_TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            logger.info(f"Alerta enviada por Telegram")
            return True
        else:
            logger.error(f"Error al enviar alerta Telegram: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error al enviar alerta Telegram: {str(e)}")
        return False

def send_alert(
    message: str, 
    subject: str = "Alerta de WhatsApp Sales Bot", 
    use_email: bool = True, 
    use_telegram: bool = True
) -> bool:
    """
    Envía una alerta por los canales disponibles.
    
    Args:
        message: Contenido del mensaje
        subject: Asunto (para correo)
        use_email: Indica si enviar por correo
        use_telegram: Indica si enviar por Telegram
        
    Returns:
        bool: True si al menos un canal fue exitoso
    """
    success = False
    
    # Enviar por correo si está habilitado
    if use_email and ADMIN_EMAIL:
        email_success = send_email_alert(subject, message)
        success = success or email_success
    
    # Enviar por Telegram si está habilitado
    if use_telegram:
        telegram_success = send_telegram_alert(message)
        success = success or telegram_success
    
    return success