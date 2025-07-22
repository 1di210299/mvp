"""
Middleware personalizado para manejar hosts dinámicos de ngrok
"""
import re
from django.conf import settings
from django.core.exceptions import DisallowedHost


class NgrokHostMiddleware:
    """
    Middleware para permitir automáticamente hosts de ngrok
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.ngrok_pattern = re.compile(r'^[a-z0-9]+\.ngrok-free\.app$')
    
    def __call__(self, request):
        # Verificar si es un host ngrok y agregarlo a ALLOWED_HOSTS
        host = request.get_host().split(':')[0]  # Remove port if present
        
        if self.ngrok_pattern.match(host) and host not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append(host)
            print(f"🔧 Added ngrok host to ALLOWED_HOSTS: {host}")
        
        response = self.get_response(request)
        return response
