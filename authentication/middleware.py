"""
Middleware para validación de tenant_id en el flujo N8N
"""
import json
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import TenantConfig

logger = logging.getLogger(__name__)


class TenantValidationMiddleware(MiddlewareMixin):
    """
    Middleware para validar tenant_id en rutas de N8N
    """
    
    # Rutas que requieren validación de tenant
    TENANT_PROTECTED_PATHS = [
        'authentication:n8n:whatsapp-send',
        'authentication:n8n:email-send',
        'authentication:n8n:tenant-usage',
        'authentication:n8n:usage-logs',
        'authentication:n8n:verify-domain',
        'authentication:n8n:setup-whatsapp',
        'authentication:n8n:tenant-detail',
    ]
    
    # Rutas que no requieren validación de tenant
    EXEMPT_PATHS = [
        'authentication:n8n:tenant-create',
        'authentication:n8n:tenant-list',
        'authentication:n8n:whatsapp-webhook',
    ]
    
    def process_request(self, request):
        """Procesar petición antes de la vista"""
        try:
            # Resolver la URL para obtener el nombre de la vista
            resolved = resolve(request.path_info)
            view_name = f"{resolved.namespace}:{resolved.url_name}" if resolved.namespace else resolved.url_name
            
            # Verificar si la ruta necesita validación de tenant
            if view_name in self.TENANT_PROTECTED_PATHS:
                return self.validate_tenant(request, resolved)
            
            return None
            
        except Exception as e:
            logger.error(f"Error en TenantValidationMiddleware: {str(e)}")
            return None
    
    def validate_tenant(self, request, resolved):
        """Validar que el tenant existe y está activo"""
        try:
            # Obtener tenant_id de los parámetros de la URL
            tenant_id = resolved.kwargs.get('tenant_id')
            
            if not tenant_id:
                return JsonResponse({
                    'success': False,
                    'error': 'tenant_id requerido'
                }, status=400)
            
            # Verificar que el tenant existe y está activo
            try:
                tenant = TenantConfig.objects.get(tenant_id=tenant_id)
                
                if not tenant.is_active:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tenant inactivo'
                    }, status=403)
                
                # Agregar tenant al request para uso en las vistas
                request.tenant = tenant
                
            except TenantConfig.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Tenant no encontrado'
                }, status=404)
            
            return None
            
        except Exception as e:
            logger.error(f"Error validando tenant: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad para APIs de N8N
    """
    
    def process_request(self, request):
        """Validaciones de seguridad"""
        try:
            # Verificar content-type para APIs POST/PUT
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_type = request.content_type
                
                # APIs que esperan JSON
                if '/n8n/' in request.path_info:
                    if not content_type.startswith('application/json'):
                        # Permitir multipart/form-data para archivos
                        if not content_type.startswith('multipart/form-data'):
                            return JsonResponse({
                                'success': False,
                                'error': 'Content-Type debe ser application/json'
                            }, status=400)
            
            # Validar tamaño del payload para prevenir ataques DoS
            if hasattr(request, 'body'):
                content_length = len(request.body)
                max_size = 10 * 1024 * 1024  # 10MB
                
                if content_length > max_size:
                    return JsonResponse({
                        'success': False,
                        'error': 'Payload demasiado grande'
                    }, status=413)
            
            return None
            
        except Exception as e:
            logger.error(f"Error en SecurityMiddleware: {str(e)}")
            return None
    
    def process_response(self, request, response):
        """Agregar headers de seguridad"""
        try:
            # Headers de seguridad para APIs de N8N
            if '/n8n/' in request.path_info:
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'
                response['X-XSS-Protection'] = '1; mode=block'
                
                # CORS para webhooks
                if '/webhook/' in request.path_info:
                    response['Access-Control-Allow-Origin'] = '*'
                    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            return response
            
        except Exception as e:
            logger.error(f"Error agregando headers de seguridad: {str(e)}")
            return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para logging de peticiones N8N
    """
    
    def process_request(self, request):
        """Log de peticiones entrantes"""
        try:
            if '/n8n/' in request.path_info:
                logger.info(f"N8N Request: {request.method} {request.path_info}")
                
                # Log de headers importantes (sin mostrar tokens completos)
                auth_header = request.headers.get('Authorization', '')
                if auth_header:
                    # Mostrar solo los primeros y últimos caracteres del token
                    if len(auth_header) > 20:
                        masked_auth = f"{auth_header[:10]}...{auth_header[-6:]}"
                    else:
                        masked_auth = "***"
                    logger.debug(f"Authorization: {masked_auth}")
                
                user_agent = request.headers.get('User-Agent', 'Unknown')
                logger.debug(f"User-Agent: {user_agent}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error en RequestLoggingMiddleware: {str(e)}")
            return None
    
    def process_response(self, request, response):
        """Log de respuestas"""
        try:
            if '/n8n/' in request.path_info:
                logger.info(f"N8N Response: {response.status_code}")
                
                # Log de errores con más detalle
                if response.status_code >= 400:
                    try:
                        content = response.content.decode('utf-8')[:500]  # Primeros 500 caracteres
                        logger.warning(f"Error response content: {content}")
                    except:
                        pass
            
            return response
            
        except Exception as e:
            logger.error(f"Error logging response: {str(e)}")
            return response
