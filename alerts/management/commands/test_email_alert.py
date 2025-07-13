from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from alerts.models import Alert, AlertRule
from alerts.services import NotificationService
from inventory.models import Product, InventoryItem, Location
from authentication.models import Company, User
from datalens_backend.utils import get_default_company
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Prueba el sistema de alertas enviando una alerta de prueba por email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='gjuandiego213@gmail.com',
            help='Email destinatario para la prueba'
        )
        parser.add_argument(
            '--alert-type',
            type=str,
            choices=['low_stock', 'high_stock', 'expiration'],
            default='low_stock',
            help='Tipo de alerta a simular'
        )
        parser.add_argument(
            '--severity',
            type=str,
            choices=['low', 'medium', 'high', 'critical'],
            default='high',
            help='Severidad de la alerta'
        )

    def handle(self, *args, **options):
        self.stdout.write('🧪 Iniciando prueba del sistema de alertas...')
        
        try:
            # Obtener o crear empresa por defecto
            company = get_default_company()
            
            # Obtener o crear usuario de prueba
            test_user, created = User.objects.get_or_create(
                email=options['email'],
                defaults={
                    'username': options['email'].split('@')[0],
                    'first_name': 'Usuario',
                    'last_name': 'Prueba',
                    'company': company,
                    'email_notifications': True,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'✅ Usuario de prueba creado: {test_user.email}')
            else:
                self.stdout.write(f'✅ Usuario de prueba encontrado: {test_user.email}')
            
            # Obtener o crear producto de prueba
            product, created = Product.objects.get_or_create(
                name='Producto de Prueba',
                defaults={
                    'sku': 'TEST-001',
                    'description': 'Producto para pruebas del sistema de alertas',
                    'category': 'Pruebas',
                    'price': 100.00,
                    'company': company
                }
            )
            
            # Obtener o crear ubicación de prueba
            location, created = Location.objects.get_or_create(
                name='Almacén Principal',
                defaults={
                    'location_type': 'warehouse',
                    'address': 'Dirección de prueba',
                    'company': company
                }
            )
            
            # Crear o obtener item de inventario
            inventory_item, created = InventoryItem.objects.get_or_create(
                product=product,
                location=location,
                defaults={
                    'quantity': 5,  # Stock bajo para simular alerta
                    'min_stock_level': 10,
                    'max_stock_level': 100
                }
            )
            
            # Crear regla de alerta de prueba
            alert_rule, created = AlertRule.objects.get_or_create(
                name=f'Regla de Prueba - {options["alert_type"]}',
                defaults={
                    'description': f'Regla de prueba para {options["alert_type"]}',
                    'alert_type': options['alert_type'],
                    'threshold_value': 10,
                    'comparison_operator': 'lt',
                    'severity': options['severity'],
                    'send_email': True,
                    'send_whatsapp': False,
                    'frequency': 'immediate',
                    'is_active': True,
                    'company': company,
                    'created_by': test_user,
                    'additional_emails': options['email']
                }
            )
            
            # Añadir usuario como destinatario
            alert_rule.recipients.add(test_user)
            
            # Crear alerta de prueba
            alert_data = self._get_alert_data(options['alert_type'], options['severity'])
            
            alert = Alert.objects.create(
                rule=alert_rule,
                title=alert_data['title'],
                message=alert_data['message'],
                alert_type=options['alert_type'],
                severity=options['severity'],
                status='active',
                product=product,
                location=location,
                current_value=alert_data['current_value'],
                threshold_value=alert_data['threshold_value'],
                created_at=timezone.now()
            )
            
            self.stdout.write(f'✅ Alerta de prueba creada: {alert.title}')
            
            # Enviar notificación por email
            notification_service = NotificationService()
            
            self.stdout.write('📧 Enviando email de prueba...')
            
            # Probar conexión de email primero
            email_test = notification_service.test_email_connection()
            self.stdout.write(f'🔌 Test de conexión email: {email_test["status"]} - {email_test["message"]}')
            
            if email_test['status'] == 'success':
                # Enviar notificación
                result = notification_service.send_email_notification(alert)
                
                if result['status'] == 'success':
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'🎉 ¡Email enviado exitosamente a {options["email"]}!'
                        )
                    )
                    self.stdout.write(f'📊 Destinatarios: {result["recipients"]}')
                    self.stdout.write(f'💌 Asunto: [DataLens] Alerta: {alert.title}')
                    
                    # Mostrar información adicional
                    self.stdout.write('\n📋 Detalles de la alerta enviada:')
                    self.stdout.write(f'   • Tipo: {alert.get_alert_type_display()}')
                    self.stdout.write(f'   • Severidad: {alert.get_severity_display()}')
                    self.stdout.write(f'   • Producto: {product.name}')
                    self.stdout.write(f'   • Ubicación: {location.name}')
                    self.stdout.write(f'   • Valor actual: {alert.current_value}')
                    self.stdout.write(f'   • Umbral: {alert.threshold_value}')
                    
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Error enviando email: {result["message"]}'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Error de conexión email: {email_test["message"]}'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️ Verifica la configuración de EMAIL_HOST_PASSWORD en tu archivo .env'
                    )
                )
            
            # Mostrar instrucciones para configurar Gmail
            self.stdout.write('\n📝 Para usar Gmail, necesitas:')
            self.stdout.write('   1. Activar verificación en 2 pasos en tu cuenta de Gmail')
            self.stdout.write('   2. Generar una "Contraseña de aplicación" en tu cuenta Google')
            self.stdout.write('   3. Usar esa contraseña en EMAIL_HOST_PASSWORD en tu .env')
            self.stdout.write('   4. Más info en: https://support.google.com/accounts/answer/185833')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la prueba: {str(e)}')
            )
            logger.error(f'Error en prueba de alertas: {str(e)}')
    
    def _get_alert_data(self, alert_type, severity):
        """Genera datos específicos según el tipo de alerta"""
        
        base_data = {
            'low_stock': {
                'title': 'Stock Bajo Detectado',
                'message': 'El inventario del producto ha alcanzado un nivel crítico. Se recomienda reabastecer inmediatamente para evitar desabastecimiento.',
                'current_value': 5,
                'threshold_value': 10
            },
            'high_stock': {
                'title': 'Exceso de Inventario',
                'message': 'Se ha detectado un exceso de inventario que puede generar costos adicionales de almacenamiento.',
                'current_value': 150,
                'threshold_value': 100
            },
            'expiration': {
                'title': 'Productos Próximos a Vencer',
                'message': 'Hay productos que vencerán en los próximos días. Se recomienda implementar estrategias de rotación FIFO.',
                'current_value': 3,  # días hasta vencimiento
                'threshold_value': 7
            }
        }
        
        return base_data.get(alert_type, base_data['low_stock'])