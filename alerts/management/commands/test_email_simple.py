from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Prueba simple de envío de email para verificar configuración de Gmail'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='gjuandiego213@gmail.com',
            help='Email destinatario para la prueba'
        )
        parser.add_argument(
            '--simple',
            action='store_true',
            help='Enviar email simple sin templates'
        )

    def handle(self, *args, **options):
        self.stdout.write('📧 Probando configuración de email...')
        
        recipient_email = options['email']
        
        # Mostrar configuración actual
        self.stdout.write('\n🔧 Configuración actual de email:')
        self.stdout.write(f'   • EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'   • EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'   • EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'   • EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'   • DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'   • Destinatario: {recipient_email}')
        
        # Verificar si la contraseña está configurada - MEJORADA
        password_placeholders = [
            'your-gmail-app-password-here',
            'REEMPLAZA_ESTO_CON_TU_CONTRASEÑA_DE_APLICACION_GMAIL',
            'PEGA_AQUI_TU_NUEVA_CONTRASEÑA_SIN_ESPACIOS',
            'AQUI_PEGA_TU_CONTRASEÑA_DE_16_DIGITOS_SIN_ESPACIOS'
        ]
        
        # Debug: Mostrar información sobre la contraseña
        self.stdout.write(f'   • EMAIL_HOST_PASSWORD configurado: {bool(settings.EMAIL_HOST_PASSWORD)}')
        self.stdout.write(f'   • Longitud de contraseña: {len(settings.EMAIL_HOST_PASSWORD)} caracteres')
        
        if not settings.EMAIL_HOST_PASSWORD or settings.EMAIL_HOST_PASSWORD in password_placeholders:
            self.stdout.write(
                self.style.ERROR(
                    '\n❌ EMAIL_HOST_PASSWORD no está configurado correctamente en el archivo .env'
                )
            )
            self.stdout.write('\n📝 Para configurar Gmail:')
            self.stdout.write('   1. Ve a https://myaccount.google.com/security')
            self.stdout.write('   2. Activa "Verificación en 2 pasos"')
            self.stdout.write('   3. Ve a "Contraseñas de aplicación"')
            self.stdout.write('   4. Genera una nueva contraseña para "Correo"')
            self.stdout.write('   5. Actualiza EMAIL_HOST_PASSWORD en tu .env con esa contraseña')
            return
        
        try:
            if options['simple']:
                # Prueba simple con send_mail
                self.stdout.write('\n📤 Enviando email simple...')
                
                subject = '🧪 Prueba Simple - DataLens'
                message = f'''
¡Hola!

Esta es una prueba simple del sistema de email de DataLens.

Si recibes este mensaje, la configuración de Gmail está funcionando correctamente.

Detalles del test:
• Fecha: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}
• Servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
• Desde: {settings.DEFAULT_FROM_EMAIL}
• Para: {recipient_email}

¡Saludos desde DataLens! 🚀
                '''
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ ¡Email simple enviado exitosamente a {recipient_email}!'
                    )
                )
                
            else:
                # Prueba con template HTML (simulando alerta)
                self.stdout.write('\n📤 Enviando email con template HTML...')
                
                # Crear contexto para el template
                context = {
                    'alert': {
                        'title': 'Prueba del Sistema de Alertas',
                        'message': 'Esta es una prueba del sistema de notificaciones por email de DataLens.',
                        'severity': 'high',
                        'created_at': timezone.now(),
                        'get_severity_display': lambda: 'ALTA',
                        'current_value': 5,
                        'threshold_value': 10
                    },
                    'rule': {
                        'name': 'Regla de Prueba',
                        'alert_type': 'low_stock',
                        'get_alert_type_display': lambda: 'Stock Bajo'
                    },
                    'product': {
                        'name': 'Producto de Prueba DataLens',
                        'sku': 'TEST-GMAIL-001'
                    },
                    'location': {
                        'name': 'Almacén Principal de Prueba'
                    },
                    'company': {
                        'name': 'DataLens MVP',
                        'email': recipient_email
                    },
                    'frontend_url': 'http://localhost:8081'
                }
                
                # Renderizar templates
                html_content = render_to_string('alerts/email_alert.html', context)
                text_content = f'''
DataLens - Alerta de Inventario

Tipo: {context['rule']['get_alert_type_display']()}
Severidad: {context['alert']['get_severity_display']()}
Producto: {context['product']['name']}
Ubicación: {context['location']['name']}
Valor actual: {context['alert']['current_value']}
Umbral: {context['alert']['threshold_value']}

Mensaje: {context['alert']['message']}

Esta es una prueba del sistema de notificaciones de DataLens.

¡Saludos!
Equipo DataLens
                '''
                
                # Crear email con contenido HTML
                subject = '[DataLens] 🧪 Prueba del Sistema de Alertas'
                
                email = EmailMessage(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ ¡Email con template HTML enviado exitosamente a {recipient_email}!'
                    )
                )
                self.stdout.write(f'💌 Asunto: {subject}')
            
            self.stdout.write('\n🎉 ¡Prueba completada exitosamente!')
            self.stdout.write(f'📬 Revisa tu bandeja de entrada en {recipient_email}')
            self.stdout.write('📋 Si no lo ves, revisa la carpeta de spam/promociones')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error enviando email: {str(e)}')
            )
            
            # Errores comunes y soluciones
            error_str = str(e).lower()
            
            if 'authentication failed' in error_str or 'invalid credentials' in error_str:
                self.stdout.write('\n🔧 Posibles soluciones:')
                self.stdout.write('   • Verifica que EMAIL_HOST_USER sea tu Gmail completo')
                self.stdout.write('   • Verifica que EMAIL_HOST_PASSWORD sea una contraseña de aplicación')
                self.stdout.write('   • Asegúrate de que la verificación en 2 pasos esté activada')
                
            elif 'connection' in error_str or 'network' in error_str:
                self.stdout.write('\n🌐 Problema de conexión:')
                self.stdout.write('   • Verifica tu conexión a internet')
                self.stdout.write('   • Verifica que EMAIL_HOST y EMAIL_PORT sean correctos')
                
            elif 'ssl' in error_str or 'tls' in error_str:
                self.stdout.write('\n🔒 Problema de seguridad:')
                self.stdout.write('   • Verifica que EMAIL_USE_TLS=True en tu .env')
                
            self.stdout.write(f'\n🐛 Error técnico: {str(e)}')
            logger.error(f'Error en prueba de email: {str(e)}')


# Importar timezone después de las otras importaciones
from django.utils import timezone