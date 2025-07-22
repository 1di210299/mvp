"""
Vistas para testing OAuth2 y configuración
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from inventory.services.n8n_integration_service import N8nIntegrationService
from inventory.models import TenantConfig

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])  # Para testing fácil
def test_oauth_token(request):
    """
    Test endpoint para probar OAuth2 token generation
    GET /api/inventory/oauth-test/test-oauth-token/
    """
    try:
        # Usar company del usuario autenticado o company por defecto
        if request.user.is_authenticated:
            company_id = request.user.company.id
        else:
            # Para testing sin autenticación, usar primer TenantConfig
            config = TenantConfig.objects.first()
            if not config:
                return Response({
                    'error': 'No hay configuraciones de tenant disponibles',
                    'suggestion': 'Crea una configuración primero'
                }, status=status.HTTP_404_NOT_FOUND)
            company_id = config.company.id
        
        # Obtener token OAuth2
        token_result = N8nIntegrationService.get_oauth_token(company_id)
        
        if token_result['success']:
            return Response({
                'success': True,
                'message': 'Token OAuth2 obtenido exitosamente',
                'company_id': company_id,
                'token_info': {
                    'access_token': token_result['access_token'][:20] + '...',  # Solo primeros 20 chars
                    'token_type': token_result['token_type'],
                    'expires_in': token_result['expires_in'],
                    'scope': token_result['scope']
                }
            })
        else:
            return Response({
                'success': False,
                'error': token_result['error'],
                'company_id': company_id
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error en test OAuth token: {str(e)}")
        return Response({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def test_client_credentials(request):
    """
    Test directo de Client Credentials Grant
    POST /api/inventory/oauth-test/test-client-credentials/
    
    Body:
    {
        "client_id": "...",
        "client_secret": "...",
        "token_url": "..."
    }
    """
    import requests
    
    try:
        data = request.data
        
        # Datos para Client Credentials Grant
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': data.get('client_id'),
            'client_secret': data.get('client_secret'),
            'scope': 'read write'
        }
        
        # Hacer request al token endpoint
        response = requests.post(
            data.get('token_url'),
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        return Response({
            'request_data': token_data,
            'response_status': response.status_code,
            'response_data': response.json() if response.status_code == 200 else response.text,
            'success': response.status_code == 200
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_full_config(request):
    """
    Test completo de configuración de tenant
    GET /api/inventory/oauth-test/test-full-config/
    """
    try:
        # Obtener todas las configuraciones
        configs = TenantConfig.objects.all()
        
        if not configs.exists():
            return Response({
                'error': 'No hay configuraciones de tenant',
                'suggestion': 'Crea una configuración primero'
            }, status=status.HTTP_404_NOT_FOUND)
        
        results = []
        for config in configs:
            # Obtener configuración
            tenant_config = N8nIntegrationService.get_tenant_config(config.company.id)
            
            # Test OAuth token
            token_result = N8nIntegrationService.get_oauth_token(config.company.id)
            
            results.append({
                'company': config.company.name,
                'company_id': config.company.id,
                'config': {
                    'oauth2_configured': bool(tenant_config['oauth2_client_id'] and tenant_config['oauth2_token_url']),
                    'whatsapp_configured': tenant_config['is_whatsapp_active'],
                    'gmail_configured': tenant_config['is_gmail_active'],
                    'n8n_webhook_configured': bool(tenant_config['n8n_webhook_url']),
                    'is_configured': tenant_config['is_configured']
                },
                'oauth_test': {
                    'success': token_result['success'],
                    'error': token_result.get('error'),
                    'has_token': 'access_token' in token_result
                }
            })
        
        return Response({
            'total_tenants': len(results),
            'tenants': results,
            'summary': {
                'total_configured': sum(1 for r in results if r['config']['is_configured']),
                'oauth_working': sum(1 for r in results if r['oauth_test']['success'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error en test full config: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
