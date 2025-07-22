"""
Autenticación personalizada para tokens de tenant
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions
import jwt
from django.conf import settings


class TenantJWTAuthentication(authentication.BaseAuthentication):
    """
    Autenticación personalizada para tokens JWT de tenant
    """
    
    def authenticate(self, request):
        """
        Autentica usando JWT de tenant
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        try:
            token = auth_header.split(' ')[1]
            
            # Decodificar el token sin verificar usuario (es un token de tenant)
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Verificar que tiene tenant_id
            tenant_id = payload.get('tenant_id')
            if not tenant_id:
                return None
                
            # Crear un usuario ficticio con los datos del tenant
            tenant_user = TenantUser(tenant_id, payload)
            
            return (tenant_user, token)
            
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, KeyError):
            return None


class TenantUser:
    """
    Usuario ficticio que representa un tenant autenticado
    """
    
    def __init__(self, tenant_id, payload):
        self.tenant_id = tenant_id
        self.tenant_name = payload.get('tenant_name', '')
        self.scope = payload.get('scope', '')
        self.is_authenticated = True
        self.is_anonymous = False
        
    @property
    def is_active(self):
        return True
        
    def __str__(self):
        return f"Tenant({self.tenant_id})"
