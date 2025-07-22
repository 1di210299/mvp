"""
Management command para configurar OAuth2 para n8n
"""
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application
import secrets
import string


class Command(BaseCommand):
    help = 'Configura OAuth2 para n8n'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Regenerar credenciales OAuth2',
        )
        parser.add_argument(
            '--ngrok-domain',
            type=str,
            default='016e520d8ade.ngrok-free.app',
            help='Dominio ngrok actual',
        )

    def handle(self, *args, **options):
        ngrok_domain = options['ngrok_domain']
        
        # Buscar o crear aplicación OAuth2
        if options['regenerate']:
            Application.objects.filter(name='n8n Integration').delete()
            self.stdout.write(self.style.WARNING('Aplicación OAuth2 anterior eliminada'))

        app, created = Application.objects.get_or_create(
            name='n8n Integration',
            defaults={
                'client_type': Application.CLIENT_CONFIDENTIAL,
                'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                'skip_authorization': False,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('✅ Aplicación OAuth2 creada para n8n'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Aplicación OAuth2 ya existía'))

        # Mostrar configuración
        self.stdout.write('\n📋 CONFIGURACIÓN OAUTH2 PARA N8N:')
        self.stdout.write('')
        self.stdout.write(f'🔑 Client ID: {app.client_id}')
        self.stdout.write(f'🔐 Client Secret: {app.client_secret}')
        self.stdout.write('')
        self.stdout.write('🌐 ENDPOINTS OAUTH2:')
        self.stdout.write(f'🔗 Authorization URL: https://{ngrok_domain}/oauth/authorize/')
        self.stdout.write(f'🎫 Access Token URL: https://{ngrok_domain}/oauth/token/')
        self.stdout.write(f'🚫 Revoke Token URL: https://{ngrok_domain}/oauth/revoke_token/')
        self.stdout.write(f'🔍 Introspect URL: https://{ngrok_domain}/oauth/introspect/')
        self.stdout.write('')
        self.stdout.write('⚙️ CONFIGURACIÓN EN N8N:')
        self.stdout.write('- Grant Type: Authorization Code')
        self.stdout.write('- Client Authentication: Send client credentials in body')
        self.stdout.write('- Scope: read write')
        self.stdout.write('- Authentication: Basic Auth')
        self.stdout.write('')
        self.stdout.write('💡 Redirect URI para n8n: https://TU_N8N_DOMAIN/rest/oauth2-credential/callback')
        self.stdout.write('')
        self.stdout.write('🧪 EJEMPLO DE FLUJO OAUTH2:')
        self.stdout.write('1. n8n redirige usuario a Authorization URL')
        self.stdout.write('2. Usuario autoriza la aplicación')
        self.stdout.write('3. Django redirige a n8n con authorization code')
        self.stdout.write('4. n8n intercambia code por access token en Token URL')
        self.stdout.write('5. n8n usa access token para llamar APIs protegidas')
