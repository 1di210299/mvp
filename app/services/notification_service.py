import logging
import smtplib
import requests
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from app.config import (
    ADMIN_EMAIL,
    ADMIN_PHONE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

# Configurar logging
logger = logging.getLogger(__name__)

def send_email(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
    from_email: Optional[str] = None
) -> bool:
    """
    Envía un correo electrónico de notificación.
    
    Args:
        to_email: Correo electrónico del destinatario
        subject: Asunto del correo
        body: Contenido del correo
        is_html: Si es True, el cuerpo se trata como HTML
        from_email: Correo del remitente (opcional)
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    # Implementación básica usando smtplib
    # En producción, deberías usar un servicio como SendGrid, Mailgun, etc.
    try:
        # Si no hay correo configurado, loguear y salir
        if not ADMIN_EMAIL:
            logger.warning("No se ha configurado ADMIN_EMAIL. No se puede enviar correo.")
            return False
            
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = from_email or "sistema@botventas.com"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Añadir cuerpo
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Esta función es solo un ejemplo. Deberías implementar
        # tu propia lógica de envío de correos usando un servicio real.
        # Por ejemplo, si usas Gmail:
        """
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('tu_correo@gmail.com', 'tu_contraseña')
            server.send_message(msg)
        """
        
        # Por ahora, solo logueamos el intento
        logger.info(f"SIMULACIÓN: Correo enviado a {to_email} - Asunto: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo: {str(e)}")
        return False

def send_telegram_message(message: str) -> bool:
    """
    Envía un mensaje a través de Telegram.
    
    Args:
        message: Contenido del mensaje
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Verificar que tengamos token y chat_id configurados
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("No se ha configurado Telegram (TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID)")
            return False
        
        # Preparar URL y datos
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        # Enviar mensaje
        response = requests.post(url, data=data)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("ok"):
            logger.info(f"Mensaje enviado a Telegram (chat_id: {TELEGRAM_CHAT_ID})")
            return True
        else:
            error_msg = response_data.get("description", "Error desconocido")
            logger.error(f"Error enviando mensaje a Telegram: {error_msg}")
            return False
    
    except Exception as e:
        logger.error(f"Error enviando mensaje a Telegram: {str(e)}")
        return False

def send_whatsapp_message(to_phone: str, message: str) -> bool:
    """
    Envía un mensaje a través de WhatsApp usando Twilio.
    
    Args:
        to_phone: Número de teléfono del destinatario
        message: Contenido del mensaje
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Importar aquí para evitar dependencias circulares
        from app.services.twilio_service import send_message
        
        # Normalizar número si es necesario
        if not to_phone.startswith("whatsapp:"):
            to_phone = f"whatsapp:{to_phone}"
        
        # Enviar mensaje
        result = send_message(to=to_phone, message=message)
        
        if result:
            logger.info(f"Mensaje enviado a WhatsApp ({to_phone})")
            return True
        else:
            logger.error(f"Error enviando mensaje a WhatsApp ({to_phone})")
            return False
    
    except Exception as e:
        logger.error(f"Error enviando mensaje a WhatsApp: {str(e)}")
        return False

def send_alert(
    content: str,
    level: str = "info",
    channels: List[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Envía una alerta por múltiples canales.
    
    Args:
        content: Contenido de la alerta
        level: Nivel de alerta (info, warning, error, critical)
        channels: Lista de canales a usar (email, telegram, whatsapp)
        metadata: Información adicional para incluir en la alerta
        
    Returns:
        bool: True si se envió al menos por un canal, False si falló en todos
    """
    # Canales predeterminados
    if channels is None:
        channels = ["telegram"]  # Por defecto, solo Telegram
    
    # Emoji según nivel
    emoji_map = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "🚫",
        "critical": "🔥",
        "success": "✅"
    }
    emoji = emoji_map.get(level, "")
    
    # Formatear mensaje
    message = f"{emoji} *ALERTA* {emoji}\n\n{content}"
    
    # Añadir metadata si existe
    if metadata:
        message += "\n\n📊 *Detalles adicionales*:\n"
        for key, value in metadata.items():
            if isinstance(value, dict) or isinstance(value, list):
                value = json.dumps(value, indent=2, ensure_ascii=False)
            message += f"• *{key}*: {value}\n"
    
    # Formatear para HTML (Telegram)
    html_message = message.replace("*", "<b>").replace("*", "</b>")
    
    # Variables para rastrear éxito
    success = False
    results = {}
    
    # Enviar por cada canal
    for channel in channels:
        if channel == "email" and ADMIN_EMAIL:
            subject = f"Alerta {level.upper()} - Bot de Ventas"
            results["email"] = send_email(ADMIN_EMAIL, subject, message)
            success = success or results["email"]
        
        elif channel == "telegram":
            results["telegram"] = send_telegram_message(html_message)
            success = success or results["telegram"]
        
        elif channel == "whatsapp" and ADMIN_PHONE:
            results["whatsapp"] = send_whatsapp_message(ADMIN_PHONE, message)
            success = success or results["whatsapp"]
    
    # Loguear resultados
    channels_str = ", ".join(channels)
    if success:
        logger.info(f"Alerta '{level}' enviada por canales: {channels_str}")
    else:
        logger.error(f"Error enviando alerta '{level}' por canales: {channels_str}")
    
    return success

def send_threat_alert(
    phone_number: str,
    message_content: str,
    threat_analysis: Dict[str, Any],
    customer_info: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Envía una alerta específica para amenazas detectadas.
    
    Args:
        phone_number: Número de teléfono origen de la amenaza
        message_content: Contenido del mensaje amenazante
        threat_analysis: Análisis de la amenaza
        customer_info: Información del cliente (opcional)
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    # Determinar nivel según score
    score = threat_analysis.get("score", 0)
    level = "info"
    if score >= 0.8:
        level = "critical"
    elif score >= 0.6:
        level = "error"
    elif score >= 0.4:
        level = "warning"
    
    # Construir contenido
    content = (
        f"*AMENAZA DETECTADA*\n\n"
        f"• *Número*: {phone_number}\n"
        f"• *Score*: {score:.2f}\n"
        f"• *Nivel*: {threat_analysis.get('threat_level', 'desconocido')}\n"
        f"• *Tipo*: {threat_analysis.get('threat_type', 'N/A')}\n\n"
        f"*Mensaje*:\n```\n{message_content}\n```\n\n"
    )
    
    # Añadir información del cliente si está disponible
    if customer_info:
        content += (
            f"*Información del cliente*:\n"
            f"• *Nombre*: {customer_info.get('name', 'No registrado')}\n"
            f"• *Cliente desde*: {customer_info.get('created_at', 'Desconocido')}\n"
        )
    
    # Enviar alerta por todos los canales disponibles
    return send_alert(
        content=content,
        level=level,
        channels=["telegram", "email"],
        metadata={
            "keywords": threat_analysis.get("keywords", []),
            "explanation": threat_analysis.get("explanation", ""),
            "analysis": threat_analysis.get("ai_analysis", {})
        }
    )

def notify_admins(message: str, level: str = "info", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Notify administrators about important events
    
    Args:
        message: The notification message
        level: Priority level (info, warning, error, critical)
        details: Additional details
        
    Returns:
        dict: Result of the notification
    """
    try:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Log to notifications file
        notification_log = os.path.join("logs", "notifications.log")
        
        notification = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        
        with open(notification_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(notification) + "\n")
        
        # Log to application logs too
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"NOTIFICATION: {message}")
        
        return {
            "success": True,
            "notification_id": notification["timestamp"],
            "message": "Notification sent to admins"
        }
    
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }