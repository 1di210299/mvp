"""
Vistas relacionadas con autenticación JWT
"""
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from django.db import transaction
from drf_spectacular.utils import extend_schema

from ..models import User
from ..serializers import (
    CustomTokenObtainPairSerializer, RegisterSerializer, 
    ProfileSerializer, UserSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that accepts email and password"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            return Response({
                'status': 'success',
                'message': 'Login exitoso',
                'user': serializer.validated_data['user'],
                'tokens': {
                    'access': serializer.validated_data['access'],
                    'refresh': serializer.validated_data['refresh']
                }
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Email o contraseña incorrectos',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """Vista para registro de nuevos usuarios y empresas"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    @extend_schema(
        summary="Registrar nueva empresa y usuario administrador",
        description="Crea una nueva empresa junto con el primer usuario administrador"
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                
                # Generar tokens JWT
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'status': 'success',
                    'message': 'Registro exitoso',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    """Vista personalizada para renovación de tokens con información del usuario"""
    
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            # Agregar información del usuario en la respuesta
            if response.status_code == 200:
                # Obtener el token de acceso renovado
                access_token = response.data.get('access')
                
                # Decodificar el token para obtener el user_id
                from rest_framework_simplejwt.tokens import UntypedToken
                from rest_framework_simplejwt.state import token_backend
                from django.contrib.auth import get_user_model
                
                try:
                    # Validar y decodificar el token
                    validated_token = UntypedToken(access_token)
                    user_id = validated_token.get('user_id')
                    
                    # Obtener el usuario
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                    
                    # Agregar datos del usuario a la respuesta
                    response.data.update({
                        'status': 'success',
                        'message': 'Token renovado exitosamente',
                        'user': ProfileSerializer(user).data,
                        'tokens': {
                            'access': access_token,
                            'refresh': response.data.get('refresh')
                        }
                    })
                    
                except Exception as token_error:
                    # Si hay error obteniendo el usuario, devolver solo el token
                    response.data = {
                        'status': 'success',
                        'message': 'Token renovado exitosamente',
                        'tokens': {
                            'access': access_token,
                            'refresh': response.data.get('refresh')
                        }
                    }
            
            return response
            
        except TokenError as e:
            return Response({
                'status': 'error',
                'message': 'Token de actualización inválido o expirado',
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Error al renovar token',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TokenValidationView(APIView):
    """Vista para validar si un token es válido"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Validar token de acceso",
        description="Verifica si un token JWT es válido y retorna información del usuario"
    )
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 TokenValidationView - Request data: {request.data}")
        logger.info(f"🔍 TokenValidationView - Request headers: {dict(request.headers)}")
        
        token = request.data.get('token')
        
        if not token:
            logger.error("❌ No token provided in request")
            return Response({
                'status': 'error',
                'message': 'Token requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🔍 Token received: {token[:50]}..." if len(token) > 50 else f"🔍 Token received: {token}")
        
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from django.contrib.auth import get_user_model
            
            # Validar el token
            logger.info("🔄 Validating token...")
            validated_token = UntypedToken(token)
            user_id = validated_token.get('user_id')
            logger.info(f"✅ Token validated, user_id: {user_id}")
            
            # Obtener el usuario
            User = get_user_model()
            user = User.objects.get(id=user_id)
            logger.info(f"✅ User found: {user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Token válido',
                'user': ProfileSerializer(user).data,
                'expires_at': validated_token.get('exp')
            })
            
        except TokenError as e:
            logger.error(f"❌ Token error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Token inválido o expirado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"❌ General error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error al validar token',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
