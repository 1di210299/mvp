"""
Middleware personalizado para optimizar el servidor de desarrollo
"""
import time
import threading
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

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
            
            # NO agregar headers problemáticos en desarrollo
            # Solo agregar headers seguros
            if hasattr(response, 'headers'):
                # Headers seguros que no causan problemas con WSGI
                response['X-Request-ID'] = str(current_count)
                response['X-Response-Time'] = f"{(time.time() - start_time):.3f}s"
            
            # Log para requests lentos
            duration = time.time() - start_time
            if duration > 5.0:
                logger.warning(
                    f"Slow request #{current_count}: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
            elif duration > 2.0:
                logger.info(
                    f"Request #{current_count}: {request.method} {request.path} "
                    f"took {duration:.2f}s"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in request #{current_count}: {str(e)}")
            return JsonResponse({
                'error': 'Internal server error',
                'request_id': current_count,
                'message': 'Error interno del servidor. Ver logs para más detalles.'
            }, status=500)
    
    def process_request(self, request):
        """
        Pre-procesar requests para optimización
        """
        # Limitar el tamaño de requests para evitar timeouts
        if hasattr(request, 'META'):
            content_length = request.META.get('CONTENT_LENGTH')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
                return JsonResponse({
                    'error': 'Request too large',
                    'max_size': '10MB',
                    'message': 'El tamaño de la solicitud excede el límite permitido'
                }, status=413)
        
        return None