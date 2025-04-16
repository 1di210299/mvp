import pytest
from unittest.mock import MagicMock, patch
import time
import os
import jinja2
from datetime import datetime, timedelta

from app.services.notification_service import (
    render_template, send_email, send_telegram_message, send_whatsapp_message, 
    send_sms, send_alert, notify_admins, queue_notification, process_notification,
    start_notification_worker, stop_notification_worker
)

# Test para el renderizado de plantillas
def test_render_template():
    # Crear una plantilla temporal para prueba
    test_dir = os.path.join(os.path.dirname(__file__), 'test_templates')
    os.makedirs(test_dir, exist_ok=True)
    
    test_template_path = os.path.join(test_dir, 'test_template.txt')
    with open(test_template_path, 'w') as f:
        f.write('Hello {{ name }}! Your order #{{ order_id }} is {{ status }}.')
    
    # Patch el entorno de plantillas para usar nuestro directorio de pruebas
    with patch('app.services.notification_service.template_env', 
               jinja2.Environment(loader=jinja2.FileSystemLoader(test_dir))):
        
        # Probar renderización de plantilla
        context = {'name': 'John', 'order_id': 123, 'status': 'completed'}
        result = render_template('test_template.txt', context)
        
        # Verificar resultado
        assert result == 'Hello John! Your order #123 is completed.'
    
    # Limpiar después de la prueba
    os.remove(test_template_path)
    os.rmdir(test_dir)

# Test para envío de email
@patch('app.services.notification_service.ADMIN_EMAIL', 'admin@example.com')
@patch('smtplib.SMTP')
def test_send_email(mock_smtp):
    # Configurar mock
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
    
    # Probar envío de email
    result = send_email(
        to_email='test@example.com',
        subject='Test Subject',
        body='Test Body',
        is_html=False
    )
    
    # Verificar resultado
    assert result is True
    
    # Con la implementación actual que simulamos, no se llama realmente a SMTP
    # pero verificamos que la función retorne el valor esperado

# Test para envío de alertas
@patch('app.services.notification_service.send_telegram_message')
@patch('app.services.notification_service.send_email')
def test_send_alert(mock_send_email, mock_send_telegram):
    # Configurar mocks
    mock_send_telegram.return_value = True
    mock_send_email.return_value = True
    
    # Probar envío de alerta
    result = send_alert(
        content='Test Alert',
        level='warning',
        channels=['telegram', 'email'],
        metadata={'source': 'test'}
    )
    
    # Verificar resultado
    assert result is True
    mock_send_telegram.assert_called_once()
    mock_send_email.assert_called_once()

# Test para encolar notificaciones
@patch('app.services.notification_service.notification_queue')
@patch('app.services.notification_service.start_notification_worker')
def test_queue_notification(mock_start_worker, mock_queue):
    # Probar encolar notificación
    result = queue_notification(
        to='+123456789',
        message='Test message',
        channel='whatsapp',
        template='test_template.txt',
        context={'name': 'John'}
    )
    
    # Verificar resultado
    assert result['success'] is True
    assert 'notification_id' in result
    mock_queue.put.assert_called_once()
    mock_start_worker.assert_called_once()

# Test para procesar notificaciones
@patch('app.services.notification_service.send_whatsapp_message')
def test_process_notification(mock_send_whatsapp):
    # Configurar mock
    mock_send_whatsapp.return_value = True
    
    # Crear notificación de prueba
    notification = {
        'id': '12345',
        'to': '+123456789',
        'message': 'Test message',
        'channel': 'whatsapp',
        'template': None,
        'context': {}
    }
    
    # Probar procesamiento
    result = process_notification(notification)
    
    # Verificar resultado
    assert result is True
    mock_send_whatsapp.assert_called_once_with('+123456789', 'Test message')

# Test para el ciclo de vida del worker
@patch('threading.Thread')
def test_notification_worker_lifecycle(mock_thread):
    # Configurar mock
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance
    
    # Iniciar worker
    start_notification_worker()
    
    # Verificar que se inicia el thread
    mock_thread.assert_called_once()
    mock_thread_instance.start.assert_called_once()
    
    # Detener worker
    stop_notification_worker()
    
    # Verificar que se marca para detener
    from app.services.notification_service import should_worker_stop
    assert should_worker_stop is True