"""
Vista para crear aplicación OAuth2 de testing sin hashing
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from oauth2_provider.models import Application
import secrets


@api_view(['POST'])
@permission_classes([AllowAny])
def create_test_oauth_app(request):
    """
    Crear aplicación OAuth2 de testing
    POST /api/inventory/oauth-test/create-test-app/
    """
    try:
        # Eliminar app anterior
        Application.objects.filter(name='n8n Integration Test').delete()
        
        # Generar credenciales simples para testing
        plain_secret = 'test-secret-123'
        
        # Crear aplicación con secret plano (para testing local)
        app = Application.objects.create(
            name='n8n Integration Test',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        )
        
        # Para testing, vamos a usar Basic Auth en lugar del secret hasheado
        return Response({
            'success': True,
            'message': 'Aplicación OAuth2 de testing creada',
            'credentials': {
                'client_id': app.client_id,
                'client_secret_display': 'Ver en admin panel',
                'grant_type': 'client_credentials',
                'token_url': 'https://016e520d8ade.ngrok-free.app/oauth/token/',
                'admin_url': 'https://016e520d8ade.ngrok-free.app/admin/oauth2_provider/application/'
            },
            'instructions': [
                '1. Ve al admin panel de Django',
                '2. OAuth2 Provider → Applications',
                '3. Haz clic en "n8n Integration Test"',
                '4. Copia el Client ID y Client Secret mostrados',
                '5. Usa esas credenciales para el Client Credentials Grant'
            ],
            'test_command': f'''
curl -X POST "https://016e520d8ade.ngrok-free.app/oauth/token/" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "grant_type=client_credentials&client_id={app.client_id}&client_secret=CLIENT_SECRET_FROM_ADMIN&scope=read write"
            '''.strip()
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_oauth_apps(request):
    """
    Listar aplicaciones OAuth2 existentes
    GET /api/inventory/oauth-test/list-apps/
    """
    try:
        apps = Application.objects.all()
        
        apps_data = []
        for app in apps:
            apps_data.append({
                'name': app.name,
                'client_id': app.client_id,
                'client_secret': app.client_secret[:20] + '...' if app.client_secret else None,
                'grant_type': app.authorization_grant_type,
                'created': app.created,
                'admin_url': f'https://016e520d8ade.ngrok-free.app/admin/oauth2_provider/application/{app.id}/change/'
            })
        
        return Response({
            'total_apps': len(apps_data),
            'applications': apps_data,
            'admin_panel': 'https://016e520d8ade.ngrok-free.app/admin/oauth2_provider/application/',
            'superuser': 'admin@testcompany.com'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
