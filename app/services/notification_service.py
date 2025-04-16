import logging
import smtplib
import requests
import json
import os
import threading
import queue
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
import jinja2

from app.config import (
    ADMIN_EMAIL,
    ADMIN_PHONE,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    SMS_API_KEY,
    SMS_API_SECRET,
    SMS_FROM_NUMBER,
)

# Configurar logging
logger = logging.getLogger(__name__)

# Cola de notificaciones para envío asíncrono
notification_queue = queue.Queue()
scheduled_notifications = []
is_worker_running = False
should_worker_stop = False

# Configuración de Jinja2 para plantillas
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates/notifications')),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)

# Asegurarse de que el directorio de plantillas existe
os.makedirs(os.path.join(os.path.dirname(__file__), '../templates/notifications'), exist_ok=True)

def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Renderiza una plantilla con el contexto proporcionado.
    
    Args:
        template_name: Nombre del archivo de plantilla
        context: Diccionario con las variables para la plantilla
        
    Returns:
        str: Plantilla renderizada
    """
    try:
        template = template_env.get_template(template_name)
        return template.render(**context)
    except jinja2.exceptions.TemplateNotFound:
        logger.warning(f"Plantilla {template_name} no encontrada, usando mensaje sin formato")
        # Fallback: devolver contexto como texto
        return "\n".join([f"{k}: {v}" for k, v in context.items()])
    except Exception as e:
        logger.error(f"Error renderizando plantilla {template_name}: {str(e)}")
        # Fallback: devolver contexto como texto
        return "\n".join([f"{k}: {v}" for k, v in context.items()])

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

def send_sms(to_phone: str, message: str) -> bool:
    """
    Envía un mensaje de texto SMS.
    
    Args:
        to_phone: Número de teléfono del destinatario
        message: Contenido del mensaje
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Verificar configuración de SMS
        if not SMS_API_KEY or not SMS_API_SECRET or not SMS_FROM_NUMBER:
            logger.warning("No se ha configurado el servicio de SMS")
            return False
            
        # Esta implementación es genérica, deberías adaptarla al proveedor de SMS que uses
        # Por ejemplo, Twilio, MessageBird, etc.
        
        # URL del API (ejemplo genérico)
        url = "https://api.sms-provider.com/send"
        
        # Datos para la solicitud
        data = {
            "api_key": SMS_API_KEY,
            "api_secret": SMS_API_SECRET,
            "from": SMS_FROM_NUMBER,
            "to": to_phone,
            "text": message
        }
        
        # Enviar solicitud
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logger.info(f"SMS enviado a {to_phone}")
            return True
        else:
            logger.error(f"Error enviando SMS: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error enviando SMS: {str(e)}")
        return False

def send_alert(
    content: str,
    level: str = "info",
    channels: List[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Envía una alerta por múltiples canales.
    
    Args:
        content: Contenido de la alerta
        level: Nivel de alerta (info, warning, error, critical)
        channels: Lista de canales a usar (email, telegram, whatsapp, sms)
        metadata: Información adicional para incluir en la alerta
        template: Nombre de la plantilla a usar (opcional)
        context: Contexto para renderizar la plantilla (opcional)
        
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
    
    # Usar plantilla si se especificó
    if template and context:
        message_content = render_template(template, context)
        # Si hay un mensaje explícito, usarlo como prefijo
        if content:
            message = f"{emoji} *{content}* {emoji}\n\n{message_content}"
        else:
            message = f"{emoji} *ALERTA* {emoji}\n\n{message_content}"
    else:
        # Formatear mensaje directamente
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
            
        elif channel == "sms" and ADMIN_PHONE:
            # SMS suele tener límites de caracteres, así que abreviamos
            sms_content = f"ALERTA [{level}]: {content[:100]}"
            if len(content) > 100:
                sms_content += "..."
            results["sms"] = send_sms(ADMIN_PHONE, sms_content)
            success = success or results["sms"]
    
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
    
    # Preparar contexto para la plantilla
    context = {
        "phone_number": phone_number,
        "message_content": message_content,
        "score": score,
        "threat_level": threat_analysis.get('threat_level', 'desconocido'),
        "threat_type": threat_analysis.get('threat_type', 'N/A'),
        "customer_info": customer_info or {},
        "threat_analysis": threat_analysis
    }
    
    # Enviar alerta usando la plantilla de amenazas
    return send_alert(
        content="AMENAZA DETECTADA",
        level=level,
        channels=["telegram", "email"],
        template="threat_alert.txt",
        context=context,
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

# -- Nueva funcionalidad: Notificaciones asíncronas y programadas -- #

def queue_notification(
    to: str,
    message: str,
    channel: str,
    template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    scheduled_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Encola una notificación para envío asíncrono.
    
    Args:
        to: Destinatario (email, teléfono, etc.)
        message: Mensaje o asunto
        channel: Canal de notificación (email, whatsapp, telegram, sms)
        template: Nombre de la plantilla (opcional)
        context: Contexto para la plantilla (opcional)
        scheduled_time: Momento programado para enviar (opcional)
        
    Returns:
        dict: Información sobre la notificación encolada
    """
    notification_id = f"{int(time.time())}_{channel}_{hash(to)}"
    
    notification = {
        "id": notification_id,
        "to": to,
        "message": message,
        "channel": channel,
        "template": template,
        "context": context,
        "created_at": datetime.now().isoformat(),
        "status": "queued"
    }
    
    if scheduled_time:
        notification["scheduled_time"] = scheduled_time.isoformat()
        scheduled_notifications.append(notification)
        logger.info(f"Notificación {notification_id} programada para {scheduled_time.isoformat()}")
    else:
        notification_queue.put(notification)
        logger.info(f"Notificación {notification_id} encolada para envío asíncrono")
        
        # Iniciar worker si no está corriendo
        start_notification_worker()
    
    return {
        "success": True,
        "notification_id": notification_id,
        "status": "scheduled" if scheduled_time else "queued"
    }

def process_notification(notification: Dict[str, Any]) -> bool:
    """
    Procesa y envía una notificación según el canal especificado.
    
    Args:
        notification: Diccionario con la información de la notificación
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    channel = notification["channel"]
    to = notification["to"]
    message = notification["message"]
    template = notification.get("template")
    context = notification.get("context", {})
    
    try:
        # Renderizar plantilla si existe
        if template and context:
            content = render_template(template, context)
        else:
            content = message
            
        # Enviar según el canal
        if channel == "email":
            subject = message  # En email, message es el asunto
            return send_email(to, subject, content, is_html=template.endswith('.html') if template else False)
            
        elif channel == "whatsapp":
            return send_whatsapp_message(to, content)
            
        elif channel == "telegram":
            return send_telegram_message(content)
            
        elif channel == "sms":
            return send_sms(to, content)
            
        else:
            logger.error(f"Canal no soportado: {channel}")
            return False
            
    except Exception as e:
        logger.error(f"Error procesando notificación {notification['id']}: {str(e)}")
        return False

def start_notification_worker():
    """Inicia el worker de notificaciones en un hilo separado si no está corriendo."""
    global is_worker_running, should_worker_stop
    
    if is_worker_running:
        return
        
    should_worker_stop = False
    
    def worker():
        global is_worker_running, should_worker_stop
        is_worker_running = True
        logger.info("Worker de notificaciones iniciado")
        
        while not should_worker_stop:
            try:
                # Procesar notificaciones programadas que llegaron a su tiempo
                now = datetime.now()
                for notification in list(scheduled_notifications):  # Usar una copia para poder modificar
                    if "scheduled_time" in notification:
                        scheduled_time = datetime.fromisoformat(notification["scheduled_time"])
                        if now >= scheduled_time:
                            # Es hora de enviar esta notificación
                            scheduled_notifications.remove(notification)
                            notification_queue.put(notification)
                
                # Procesar cola normal
                try:
                    # Obtener una notificación con timeout
                    notification = notification_queue.get(timeout=1)
                    
                    # Procesar la notificación
                    success = process_notification(notification)
                    
                    if success:
                        logger.info(f"Notificación {notification['id']} enviada correctamente")
                    else:
                        logger.error(f"Error enviando notificación {notification['id']}")
                        
                    # Marcar tarea como hecha
                    notification_queue.task_done()
                    
                except queue.Empty:
                    # No hay notificaciones en la cola, esperar
                    pass
                    
            except Exception as e:
                logger.error(f"Error en worker de notificaciones: {str(e)}")
            
            # Pequeña pausa para no consumir demasiados recursos
            time.sleep(0.1)
        
        logger.info("Worker de notificaciones detenido")
        is_worker_running = False
    
    # Iniciar hilo
    notification_thread = threading.Thread(target=worker, daemon=True)
    notification_thread.start()

def stop_notification_worker():
    """Detiene el worker de notificaciones."""
    global should_worker_stop
    should_worker_stop = True
    logger.info("Solicitando detención del worker de notificaciones")

# Iniciar el worker automáticamente al importar el módulo
start_notification_worker()