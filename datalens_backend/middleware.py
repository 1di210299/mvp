"""
Middleware personalizado para optimizar el servidor de desarrollo
y detectar problemas de headers que causan error 431
"""
import time
import threading
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)
headers_logger = logging.getLogger('headers_debug')

class HeaderSizeDebugMiddleware(MiddlewareMixin):
    """
    Middleware para detectar y reportar headers grandes que causan error 431
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        self.lock = threading.Lock()
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Analizar el tamaño de headers en requests entrantes
        """
        with self.lock:
            self.request_count += 1
            current_request = self.request_count
        
        if not hasattr(request, 'META'):
            return None
            
        # Calcular tamaño total de headers
        total_header_size = 0
        large_headers = []
        cookie_size = 0
        
        for key, value in request.META.items():
            if key.startswith('HTTP_') or key in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                header_size = len(str(key)) + len(str(value))
                total_header_size += header_size
                
                # Detectar headers individuales grandes
                if header_size > 1000:  # Headers > 1KB son sospechosos
                    large_headers.append({
                        'name': key,
                        'size': header_size,
                        'value_preview': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                    })
                
                # Analizar cookies específicamente
                if key == 'HTTP_COOKIE':
                    cookie_size = header_size
        
        # Log información de debugging
        headers_logger.info(
            f"Request #{current_request} {request.method} {request.path} - "
            f"Total headers: {total_header_size} bytes, Cookies: {cookie_size} bytes"
        )
        
        # Advertir sobre headers grandes
        if total_header_size > 4096:  # 4KB es el límite de advertencia
            headers_logger.warning(
                f"🚨 Large headers detected in request #{current_request}! "
                f"Total size: {total_header_size} bytes"
            )
            
            for header in large_headers:
                headers_logger.warning(
                    f"   📏 Large header: {header['name']} ({header['size']} bytes): "
                    f"{header['value_preview']}"
                )
        
        # Advertencia específica para cookies grandes
        if cookie_size > 2000:  # Cookies > 2KB son problemáticas
            headers_logger.warning(
                f"🍪 Large cookie header in request #{current_request}: {cookie_size} bytes"
            )
            # Mostrar preview de las cookies
            cookie_content = request.META.get('HTTP_COOKIE', '')
            headers_logger.debug(f"Cookie content preview: {cookie_content[:200]}...")
        
        # Si es extremadamente grande, prevenir el request y devolver error útil
        if total_header_size > 16384:  # 16KB es definitivamente demasiado
            headers_logger.error(
                f"🚨 Headers too large in request #{current_request}: {total_header_size} bytes. "
                f"Rejecting request to prevent server overload."
            )
            
            return JsonResponse({
                'error': 'Request headers too large',
                'error_code': 'HEADERS_TOO_LARGE',
                'details': {
                    'total_size_bytes': total_header_size,
                    'max_allowed_bytes': 16384,
                    'request_number': current_request,
                    'large_headers': [
                        {
                            'name': h['name'],
                            'size': h['size']
                        } for h in large_headers
                    ],
                    'cookie_size_bytes': cookie_size
                },
                'message': 'Los headers de la solicitud son demasiado grandes.',
                'solutions': [
                    '🧹 Limpia las cookies del navegador (F12 > Application > Storage > Clear Storage)',
                    '💾 Limpia localStorage y sessionStorage',
                    '🕵️ Usa una ventana de incógnito para probar',
                    '🔄 Reinicia completamente el navegador',
                    '🚫 Verifica que no se estén enviando tokens muy grandes'
                ],
                'debugging_info': {
                    'top_large_headers': large_headers[:3],  # Mostrar solo los 3 más grandes
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')[:100],
                    'referer': request.META.get('HTTP_REFERER', 'None')[:100]
                }
            }, status=431)
        
        return None
    
    def process_response(self, request, response):
        """
        Agregar headers de debugging a la respuesta
        """
        if hasattr(request, 'META') and getattr(settings, 'DEBUG', False):
            # Calcular tamaño de headers del request
            total_size = sum(
                len(str(k)) + len(str(v)) 
                for k, v in request.META.items() 
                if k.startswith('HTTP_') or k in ['CONTENT_TYPE', 'CONTENT_LENGTH']
            )
            
            # Agregar headers informativos (solo en DEBUG)
            response['X-Request-Header-Size'] = str(total_size)
            
            # Si hay cookies grandes, avisar en el header
            cookie_size = len(request.META.get('HTTP_COOKIE', ''))
            if cookie_size > 1000:
                response['X-Large-Cookies-Warning'] = f'{cookie_size}-bytes'
            
            # Agregar consejos si los headers están creciendo
            if total_size > 2000:
                response['X-Header-Advice'] = 'Consider-Clearing-Browser-Data'
        
        return response


class DevelopmentOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware para optimizar el rendimiento en desarrollo
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        self.lock = threading.Lock()
        super().__init__(get_response)
    
    def __call__(self, request):
        start_time = time.time()
        
        # Incrementar contador de requests
        with self.lock:
            self.request_count += 1
            current_count = self.request_count
        
        try:
            response = self.get_response(request)
            
            # Agregar headers seguros que no causan problemas
            if hasattr(response, 'headers') and getattr(settings, 'DEBUG', False):
                # Headers seguros y útiles para debugging
                response['X-Request-ID'] = str(current_count)
                response['X-Response-Time'] = f"{(time.time() - start_time):.3f}s"
                
                # Header para ayudar con CORS en desarrollo
                if request.method == 'OPTIONS':
                    response['X-Preflight-Response'] = 'OK'
            
            # Log para requests lentos
            duration = time.time() - start_time
            if duration > 5.0:
                logger.warning(
                    f"⏰ Slow request #{current_count}: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
            elif duration > 2.0:
                logger.info(
                    f"⏱️ Request #{current_count}: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"💥 Error in request #{current_count}: {str(e)}")
            
            # Respuesta de error más informativa
            error_response = JsonResponse({
                'error': 'Internal server error',
                'error_code': 'INTERNAL_SERVER_ERROR',
                'request_id': current_count,
                'message': 'Error interno del servidor. Ver logs para más detalles.',
                'debugging_info': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)[:200],  # Limitar mensaje de error
                    'request_path': request.path,
                    'request_method': request.method
                } if getattr(settings, 'DEBUG', False) else None
            }, status=500)
            
            return error_response
    
    def process_request(self, request):
        """
        Pre-procesar requests para optimización y prevención de problemas
        """
        # Limitar el tamaño de requests para evitar timeouts
        if hasattr(request, 'META'):
            content_length = request.META.get('CONTENT_LENGTH')
            if content_length:
                try:
                    content_length = int(content_length)
                    if content_length > 10 * 1024 * 1024:  # 10MB
                        return JsonResponse({
                            'error': 'Request too large',
                            'error_code': 'REQUEST_TOO_LARGE',
                            'details': {
                                'content_length_bytes': content_length,
                                'max_size_bytes': 10 * 1024 * 1024,
                                'max_size_readable': '10MB'
                            },
                            'message': 'El tamaño de la solicitud excede el límite permitido',
                            'solutions': [
                                'Reduce el tamaño de los datos enviados',
                                'Divide la operación en múltiples requests más pequeños',
                                'Verifica que no se estén enviando archivos demasiado grandes'
                            ]
                        }, status=413)
                except (ValueError, TypeError):
                    # Content-Length inválido, continuar normalmente
                    pass
        
        return None


class CORSDebugMiddleware(MiddlewareMixin):
    """
    Middleware adicional para debuggear problemas específicos de CORS
    que pueden contribuir al error 431
    """
    
    def process_request(self, request):
        """
        Log información útil sobre requests CORS
        """
        if getattr(settings, 'DEBUG', False):
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                headers_logger.debug(f"🌐 CORS request from origin: {origin}")
            
            # Log preflight requests
            if request.method == 'OPTIONS':
                headers_logger.debug(
                    f"✈️ CORS preflight request to {request.path} from {origin}"
                )
                
                # Log qué headers está solicitando el preflight
                requested_headers = request.META.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS')
                if requested_headers:
                    headers_logger.debug(f"📋 Requested headers: {requested_headers}")
        
        return None
    
    def process_response(self, request, response):
        """
        Log información sobre respuestas CORS
        """
        if getattr(settings, 'DEBUG', False) and request.method == 'OPTIONS':
            # Log qué headers CORS se están enviando en la respuesta
            cors_headers = {
                k: v for k, v in response.items() 
                if k.lower().startswith('access-control-')
            }
            if cors_headers:
                headers_logger.debug(f"📤 CORS response headers: {cors_headers}")
        
        return response