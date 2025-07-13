from django.test import TestCase, override_settings
from django.core.mail import send_mail
from django.conf import settings
import requests
import os
from alerts.models import AlertRule, Alert
from alerts.services import NotificationService
from alerts.tests.factories import UserFactory, AlertRuleFactory, AlertFactory

class LiveNotificationTest(TestCase):
    """
    Tests que envían notificaciones reales - úsalos con cuidado
    Configura las variables de entorno antes de ejecutar
    """
    
    def setUp(self):
        self.user = UserFactory()
        self.rule = AlertRuleFactory(created_by=self.user)
        self.alert = AlertFactory(rule=self.rule)
        self.notification_service = NotificationService()

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='smtp.gmail.com',
        EMAIL_PORT=587,
        EMAIL_USE_TLS=True,
        EMAIL_HOST_USER=os.getenv('EMAIL_HOST_USER'),
        EMAIL_HOST_PASSWORD=os.getenv('EMAIL_HOST_PASSWORD')
    )
    def test_send_real_email(self):
        """
        Test que envía email real
        Configura EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en .env
        """
        recipient_email = os.getenv('TEST_EMAIL_RECIPIENT', 'tu-email@gmail.com')
        
        if not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
            self.skipTest("Email credentials not configured")
        
        try:
            send_mail(
                subject=f'[TEST ALERT] {self.alert.title}',
                message=f'''
                🚨 ALERTA DE PRUEBA 🚨
                
                Regla: {self.alert.rule.name}
                Título: {self.alert.title}
                Mensaje: {self.alert.message}
                Severidad: {self.alert.severity}
                Estado: {self.alert.status}
                
                Esta es una prueba del sistema de alertas.
                ''',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            print(f"✅ Email enviado exitosamente a {recipient_email}")
            self.assertTrue(True)  # Si llega aquí, el email se envió
            
        except Exception as e:
            self.fail(f"Error enviando email: {str(e)}")

    def test_send_whatsapp_twilio(self):
        """
        Test que envía WhatsApp usando Twilio
        Configura TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
        """
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        whatsapp_to = os.getenv('TEST_WHATSAPP_TO', 'whatsapp:+1234567890')
        
        if not all([account_sid, auth_token]):
            self.skipTest("Twilio credentials not configured")
        
        try:
            from twilio.rest import Client
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=f'''
🚨 *ALERTA DE PRUEBA* 🚨

*Regla:* {self.alert.rule.name}
*Título:* {self.alert.title}
*Severidad:* {self.alert.severity.upper()}
*Estado:* {self.alert.status}

_{self.alert.message}_

Esta es una prueba del sistema de alertas.
                ''',
                from_=whatsapp_from,
                to=whatsapp_to
            )
            
            print(f"✅ WhatsApp enviado exitosamente. SID: {message.sid}")
            self.assertIsNotNone(message.sid)
            
        except ImportError:
            self.skipTest("Twilio library not installed. Run: pip install twilio")
        except Exception as e:
            self.fail(f"Error enviando WhatsApp: {str(e)}")

    def test_send_whatsapp_api_direct(self):
        """
        Test que envía WhatsApp usando API directa de WhatsApp Business
        Configura WHATSAPP_TOKEN y WHATSAPP_PHONE_ID
        """
        token = os.getenv('WHATSAPP_TOKEN')
        phone_id = os.getenv('WHATSAPP_PHONE_ID')
        recipient_phone = os.getenv('TEST_WHATSAPP_RECIPIENT', '1234567890')
        
        if not all([token, phone_id]):
            self.skipTest("WhatsApp API credentials not configured")
        
        url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "body": f"""🚨 *ALERTA DE PRUEBA* 🚨

*Regla:* {self.alert.rule.name}
*Título:* {self.alert.title}
*Severidad:* {self.alert.severity.upper()}
*Estado:* {self.alert.status}

_{self.alert.message}_

Esta es una prueba del sistema de alertas."""
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            print(f"✅ WhatsApp enviado exitosamente. Response: {response.json()}")
            self.assertEqual(response.status_code, 200)
            
        except Exception as e:
            self.fail(f"Error enviando WhatsApp: {str(e)}")

    def test_send_telegram_notification(self):
        """
        Test que envía notificación por Telegram
        Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID
        """
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not all([bot_token, chat_id]):
            self.skipTest("Telegram credentials not configured")
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        message = f"""
🚨 <b>ALERTA DE PRUEBA</b> 🚨

<b>Regla:</b> {self.alert.rule.name}
<b>Título:</b> {self.alert.title}
<b>Severidad:</b> {self.alert.severity.upper()}
<b>Estado:</b> {self.alert.status}

<i>{self.alert.message}</i>

Esta es una prueba del sistema de alertas.
        """
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            print(f"✅ Telegram enviado exitosamente. Response: {response.json()}")
            self.assertEqual(response.status_code, 200)
            
        except Exception as e:
            self.fail(f"Error enviando Telegram: {str(e)}")

class NotificationIntegrationTest(TestCase):
    """
    Tests de integración para verificar que el servicio funciona end-to-end
    """
    
    def test_full_alert_flow_with_notifications(self):
        """
        Test que simula el flujo completo: crear regla -> evaluar -> crear alerta -> notificar
        """
        user = UserFactory()
        rule = AlertRuleFactory(created_by=user, is_active=True)
        
        # Simular que la regla se activa
        from alerts.services import AlertService
        alert_service = AlertService()
        
        # Mock para que la regla se evalúe como True
        with patch.object(alert_service, 'evaluate_rule', return_value=True):
            # Mock para las notificaciones si no queremos enviar reales
            with patch('alerts.services.NotificationService.send_alert_notification') as mock_notify:
                result = alert_service.check_all_rules()
                
                self.assertEqual(result['alerts_triggered'], 1)
                self.assertEqual(Alert.objects.count(), 1)
                mock_notify.assert_called_once()
                
                # Verificar que se creó la alerta correctamente
                alert = Alert.objects.first()
                self.assertEqual(alert.rule, rule)
                self.assertEqual(alert.status, 'active')