"""
Vistas relacionadas con autenticación JWT
"""
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from django.db import transaction
from drf_spectacular.utils import extend_schema

from ..models import User
from ..serializers import (
    CustomTokenObtainPairSerializer, RegisterSerializer, 
    ProfileSerializer, UserSerializer, ChangePasswordSerializer
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
        request=RegisterSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    user = serializer.save()
                    
                    # Generar tokens
                    refresh = RefreshToken.for_user(user)
                    
                    return Response({
                        'status': 'success',
                        'message': 'Usuario registrado exitosamente',
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'access': str(refresh.access_token),
                            'refresh': str(refresh)
                        }
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': 'Error al registrar usuario',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'error',
            'message': 'Datos inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view with error handling"""
    
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return Response({
                'status': 'success',
                'message': 'Token renovado exitosamente',
                'access': response.data.get('access')
            })
        except (InvalidToken, TokenError) as e:
            return Response({
                'status': 'error',
                'message': 'Token inválido o expirado',
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


class TokenValidationView(APIView):
    """Vista para validar tokens JWT"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Token válido',
            'user': UserSerializer(request.user).data
        })


class ProfileView(APIView):
    """Vista para obtener y actualizar perfil de usuario"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses={200: ProfileSerializer})
    def get(self, request):
        """Obtener perfil del usuario autenticado"""
        serializer = ProfileSerializer(request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    @extend_schema(
        request=ProfileSerializer,
        responses={200: ProfileSerializer}
    )
    def put(self, request):
        """Actualizar perfil del usuario autenticado"""
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Perfil actualizado exitosamente',
                'data': serializer.data
            })
        
        return Response({
            'status': 'error',
            'message': 'Error al actualizar perfil',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Vista para cambiar contraseña"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: 'Password changed successfully'}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Verificar contraseña actual
            if not user.check_password(serializer.validated_data['current_password']):
                return Response({
                    'status': 'error',
                    'message': 'Contraseña actual incorrecta'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Cambiar contraseña
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'status': 'success',
                'message': 'Contraseña cambiada exitosamente'
            })
        
        return Response({
            'status': 'error',
            'message': 'Datos inválidos',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """Vista para cerrar sesión y invalidar tokens"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Cerrar sesión",
        description="Invalida el refresh token del usuario"
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({
                'status': 'success',
                'message': 'Sesión cerrada exitosamente'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Error al cerrar sesión'
            }, status=status.HTTP_400_BAD_REQUEST)


# Aliases for compatibility with URL configuration
LoginView = CustomTokenObtainPairView
TokenRefreshView = CustomTokenRefreshView
LogoutView = LogoutAPIView
