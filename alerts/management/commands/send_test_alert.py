from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from alerts.models import AlertRule, Alert
from alerts.services import NotificationService
from authentication.models import Company
from datalens_backend.utils import get_default_company

User = get_user_model()

class Command(BaseCommand):
    help = 'Envía una alerta de prueba'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email destinatario')
        parser.add_argument('--whatsapp', type=str, help='Número WhatsApp')
        parser.add_argument('--telegram', action='store_true', help='Enviar por Telegram')

    def handle(self, *args, **options):
        try:
            # Obtener o crear empresa por defecto
            company = get_default_company()
            
            # Crear usuario y regla de prueba si no existen
            user, created = User.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': options.get('email', 'admin@test.com'),
                    'first_name': 'Test',
                    'last_name': 'Admin',
                    'company': company,
                    'email_notifications': True,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Usuario de prueba creado: {user.email}')
            else:
                self.stdout.write(f'Usuario de prueba encontrado: {user.email}')
            
            rule, created = AlertRule.objects.get_or_create(
                name='Test Alert Rule',
                defaults={
                    'description': 'Regla de prueba para notificaciones',
                    'alert_type': 'low_stock',
                    'send_email': True,
                    'send_whatsapp': False,
                    'is_active': True,
                    'company': company,
                    'created_by': user,
                    'threshold_value': 10,
                    'frequency': 'immediate'
                }
            )
            
            # Agregar el usuario como destinatario de la regla
            rule.recipients.add(user)
            
            # Si se especificó un email adicional, agregarlo
            if options.get('email') and options['email'] != user.email:
                if rule.additional_emails:
                    emails = rule.additional_emails.split(',')
                    emails.append(options['email'])
                    rule.additional_emails = ','.join(set(emails))  # Eliminar duplicados
                else:
                    rule.additional_emails = options['email']
                rule.save()
            
            if created:
                self.stdout.write(f'Regla de alerta creada: {rule.name}')
            else:
                self.stdout.write(f'Regla de alerta encontrada: {rule.name}')
            
            # Mostrar información de destinatarios
            recipients = rule.get_recipient_emails()
            self.stdout.write(f'Destinatarios configurados: {recipients}')
            
            # Crear alerta de prueba
            alert = Alert.objects.create(
                rule=rule,
                company=company,
                title='🚨 Alerta de Prueba del Sistema',
                message='Esta es una alerta generada para probar el sistema de notificaciones de DataLens.',
                severity='high',
                status='active',
                current_value=5,
                threshold_value=10
            )
            
            self.stdout.write(f'Alerta de prueba creada: {alert.title}')
            
            # Enviar notificaciones
            notification_service = NotificationService()
            
            # Envío de email
            if options.get('email'):
                self.stdout.write(f"📧 Enviando email a {options['email']}...")
                result = notification_service.send_email_notification(alert)
                
                if result['status'] == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Email enviado exitosamente a {options["email"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error enviando email: {result["message"]}')
                    )
            
            # WhatsApp (si está configurado)
            if options.get('whatsapp'):
                self.stdout.write(f"📱 Enviando WhatsApp a {options['whatsapp']}...")
                # Implementar cuando tengas Twilio configurado
                self.stdout.write(self.style.WARNING('WhatsApp no configurado todavía'))
                
            # Telegram (si está configurado)
            if options.get('telegram'):
                self.stdout.write("📨 Enviando por Telegram...")
                # Implementar cuando tengas Telegram configurado
                self.stdout.write(self.style.WARNING('Telegram no configurado todavía'))
            
            self.stdout.write('\n🎉 Proceso completado!')
            self.stdout.write(f'   • Alerta ID: {alert.id}')
            self.stdout.write(f'   • Usuario: {user.email}')
            self.stdout.write(f'   • Empresa: {company.name}')
            self.stdout.write(f'   • Revisa tu bandeja de entrada: {options.get("email", user.email)}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la prueba: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
