"""
Vista específica para autenticación de tenants en N8N
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
import logging

from ..models import TenantConfig
from ..serializers import TenantAuthSerializer
from ..auth import TenantJWTAuthentication

logger = logging.getLogger(__name__)


class TenantAuthView(APIView):
    """
    Autenticación específica para tenants de N8N
    Permite que sistemas externos obtengan JWT para usar APIs de tenant
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Autenticación de tenant para N8N",
        description="Obtiene JWT token usando client_id (tenant_id) y client_secret",
        request=TenantAuthSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "expires_in": {"type": "integer"},
                    "tenant_id": {"type": "string"},
                    "tenant_name": {"type": "string"}
                }
            },
            401: {
                "type": "object", 
                "properties": {
                    "error": {"type": "string"}
                }
            }
        }
    )
    def post(self, request):
        """
        Autentica un tenant y devuelve JWT token
        
        Body:
        {
            "client_id": "tenant_id_uuid",
            "client_secret": "tenant_secret"
        }
        """
        client_id = request.data.get('client_id')
        client_secret = request.data.get('client_secret')
        
        if not client_id or not client_secret:
            return Response({
                'error': 'client_id and client_secret are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Buscar el tenant por ID
            tenant = TenantConfig.objects.get(tenant_id=client_id)
            
            # Verificar que el tenant está activo
            if not tenant.is_active:
                return Response({
                    'error': 'Tenant is not active'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verificar client_secret
            if not tenant.client_secret:
                logger.warning(f"Tenant {client_id} has no client_secret configured")
                return Response({
                    'error': 'Tenant not configured for API access'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if client_secret != tenant.client_secret:
                logger.warning(f"Invalid client_secret for tenant {client_id}")
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generar JWT token personalizado para el tenant
            refresh = RefreshToken()
            refresh['tenant_id'] = str(tenant.tenant_id)
            refresh['tenant_name'] = tenant.name
            refresh['scope'] = 'n8n:access'
            
            access_token = refresh.access_token
            access_token['tenant_id'] = str(tenant.tenant_id)
            access_token['tenant_name'] = tenant.name
            access_token['scope'] = 'n8n:access'
            
            logger.info(f"Successful tenant authentication: {tenant.name} ({client_id})")
            
            return Response({
                'access_token': str(access_token),
                'expires_in': 3600,  # 1 hora
                'tenant_id': str(tenant.tenant_id),
                'tenant_name': tenant.name
            })
            
        except TenantConfig.DoesNotExist:
            logger.warning(f"Tenant not found: {client_id}")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error in tenant auth: {str(e)}")
            return Response({
                'error': 'Authentication failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TenantConfigView(APIView):
    """
    Vista para que los tenants obtengan su propia configuración usando JWT
    """
    authentication_classes = [TenantJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener configuración del tenant autenticado",
        description="Devuelve la configuración del tenant usando JWT de tenant",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'tenant_id': {'type': 'string'},
                    'name': {'type': 'string'},
                    'domain': {'type': 'string'},
                    'email_address': {'type': 'string'},
                    'whatsapp_number': {'type': 'string'},
                    'is_active': {'type': 'boolean'},
                }
            },
            401: {'description': 'No autorizado'},
            404: {'description': 'Tenant no encontrado'}
        }
    )
    def get(self, request):
        """
        Obtiene la configuración del tenant autenticado
        """
        try:
            # El usuario ya fue autenticado por TenantJWTAuthentication
            tenant_user = request.user
            if not hasattr(tenant_user, 'tenant_id'):
                return Response({
                    'error': 'Token inválido'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            tenant_id = tenant_user.tenant_id
            
            # Buscar el tenant
            tenant = TenantConfig.objects.get(tenant_id=tenant_id, is_active=True)
            
            logger.info(f"Tenant config request: {tenant.name} ({tenant_id})")
            
            return Response({
                'tenant_id': str(tenant.tenant_id),
                'name': tenant.name,
                'domain': tenant.domain,
                'email_address': tenant.email_address,
                'phone': getattr(tenant, 'phone', ''),
                'is_active': tenant.is_active,
                'created_at': tenant.created_at.isoformat() if tenant.created_at else None
            })
            
        except TenantConfig.DoesNotExist:
            logger.warning(f"Tenant not found or inactive: {tenant_id}")
            return Response({
                'error': 'Tenant no encontrado o inactivo'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting tenant config: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
