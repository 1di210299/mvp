from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import authenticate
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Company, User
from .serializers import (
    CompanySerializer, UserSerializer, UserCreateSerializer,
    RegisterSerializer, ProfileSerializer, ChangePasswordSerializer,
    CustomTokenObtainPairSerializer
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


class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de empresas"""
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    queryset = Company.objects.all()  # Add this line
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return Company.objects.all()
        return Company.objects.filter(id=user.company.id)
    
    @extend_schema(
        summary="Obtener estadísticas de la empresa",
        description="Retorna estadísticas básicas de la empresa como usuarios activos, productos, etc."
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        company = self.get_object()
        stats = {
            'total_users': company.users.filter(is_active=True).count(),
            'total_products': company.products.filter(is_active=True).count(),
            'total_locations': company.locations.filter(is_active=True).count(),
            'total_suppliers': company.suppliers.filter(is_active=True).count(),
            'subscription_type': company.subscription_type,
            'max_users': company.max_users,
        }
        return Response(stats)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()  # Add this line
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return User.objects.all()
        elif user.role == 'admin':
            return User.objects.filter(company=user.company)
        else:
            return User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        # Solo admin y superadmin pueden crear usuarios
        user = self.request.user
        if user.role not in ['admin', 'superadmin']:
            raise permissions.PermissionDenied("No tienes permisos para crear usuarios")
        
        # Si no es superadmin, asignar a su empresa
        if user.role != 'superadmin':
            serializer.save(company=user.company)
        else:
            serializer.save()
    
    @extend_schema(
        summary="Activar/desactivar usuario",
        description="Cambia el estado activo del usuario"
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({
            'status': 'success',
            'is_active': user.is_active
        })


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


class ProfileView(APIView):
    """Vista para gestión del perfil del usuario"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener perfil del usuario",
        description="Retorna la información del perfil del usuario autenticado"
    )
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Actualizar perfil del usuario",
        description="Actualiza la información del perfil del usuario autenticado"
    )
    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Perfil actualizado exitosamente',
                'data': serializer.data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Vista para cambio de contraseña"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Cambiar contraseña del usuario",
        description="Permite al usuario cambiar su contraseña actual"
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'status': 'success',
                'message': 'Contraseña cambiada exitosamente'
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ===== SETTINGS ENDPOINTS =====

class UserSettingsView(APIView):
    """Vista para gestión de configuraciones de usuario"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener configuraciones del usuario",
        description="Retorna todas las configuraciones personales del usuario"
    )
    def get(self, request):
        user = request.user
        
        settings_data = {
            'user_settings': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone or '',
                'language': getattr(user, 'language', 'es'),
                'timezone': getattr(user, 'timezone', 'America/Lima'),
            },
            'notification_settings': {
                'email_notifications': user.email_notifications,
                'sms_notifications': getattr(user, 'sms_notifications', False),
                'low_stock_alerts': getattr(user, 'low_stock_alerts', True),
                'daily_reports': getattr(user, 'daily_reports', True),
                'weekly_reports': getattr(user, 'weekly_reports', False),
            },
            'security_settings': {
                'two_factor_enabled': getattr(user, 'two_factor_enabled', False),
                'password_expiry': getattr(user, 'password_expiry', '90'),
                'session_timeout': getattr(user, 'session_timeout', '30'),
            },
            'system_settings': {
                'currency': getattr(user.company, 'currency', 'PEN') if user.company else 'PEN',
                'date_format': getattr(user.company, 'date_format', 'DD/MM/YYYY') if user.company else 'DD/MM/YYYY',
                'low_stock_threshold': getattr(user.company, 'low_stock_threshold', 10) if user.company else 10,
                'auto_reorder': getattr(user.company, 'auto_reorder', False) if user.company else False,
            }
        }
        
        return Response(settings_data)
    
    @extend_schema(
        summary="Actualizar configuraciones del usuario",
        description="Actualiza las configuraciones personales del usuario"
    )
    def patch(self, request):
        user = request.user
        data = request.data
        
        try:
            # Actualizar configuraciones de usuario
            if 'user_settings' in data:
                user_settings = data['user_settings']
                if 'first_name' in user_settings:
                    user.first_name = user_settings['first_name']
                if 'last_name' in user_settings:
                    user.last_name = user_settings['last_name']
                if 'email' in user_settings:
                    user.email = user_settings['email']
                if 'phone' in user_settings:
                    user.phone = user_settings['phone']
                
                # Guardar preferencias en dashboard_preferences como JSON
                preferences = user.dashboard_preferences or {}
                if 'language' in user_settings:
                    preferences['language'] = user_settings['language']
                if 'timezone' in user_settings:
                    preferences['timezone'] = user_settings['timezone']
                user.dashboard_preferences = preferences
            
            # Actualizar configuraciones de notificaciones
            if 'notification_settings' in data:
                notification_settings = data['notification_settings']
                if 'email_notifications' in notification_settings:
                    user.email_notifications = notification_settings['email_notifications']
                
                # Guardar otras configuraciones en dashboard_preferences
                preferences = user.dashboard_preferences or {}
                notification_prefs = preferences.get('notifications', {})
                
                for key in ['sms_notifications', 'low_stock_alerts', 'daily_reports', 'weekly_reports']:
                    if key in notification_settings:
                        notification_prefs[key] = notification_settings[key]
                
                preferences['notifications'] = notification_prefs
                user.dashboard_preferences = preferences
            
            # Actualizar configuraciones de seguridad
            if 'security_settings' in data:
                security_settings = data['security_settings']
                preferences = user.dashboard_preferences or {}
                security_prefs = preferences.get('security', {})
                
                for key in ['two_factor_enabled', 'password_expiry', 'session_timeout']:
                    if key in security_settings:
                        security_prefs[key] = security_settings[key]
                
                preferences['security'] = security_prefs
                user.dashboard_preferences = preferences
            
            # Actualizar configuraciones del sistema (a nivel de empresa)
            if 'system_settings' in data and user.company:
                system_settings = data['system_settings']
                company = user.company
                
                # Solo admins pueden cambiar configuraciones de empresa
                if user.role in ['admin', 'superadmin']:
                    # Usar dashboard_preferences para configuraciones de empresa también
                    company_prefs = {}
                    for key in ['currency', 'date_format', 'low_stock_threshold', 'auto_reorder']:
                        if key in system_settings:
                            company_prefs[key] = system_settings[key]
                    
                    # Aquí podríamos agregar campos a Company model, pero por ahora usamos JSON
                    # Por simplicidad, guardamos en las preferencias del usuario admin
                    preferences = user.dashboard_preferences or {}
                    preferences['company_settings'] = company_prefs
                    user.dashboard_preferences = preferences
            
            user.save()
            
            return Response({
                'status': 'success',
                'message': 'Configuraciones actualizadas exitosamente'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Error al actualizar configuraciones: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class SystemInfoView(APIView):
    """Vista para obtener información del sistema"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Obtener información del sistema",
        description="Retorna información técnica del sistema para la página de configuraciones"
    )
    def get(self, request):
        import django
        import sys
        import platform
        from django.conf import settings
        
        system_info = {
            'application': {
                'name': 'DataLens',
                'version': '1.0.0',
                'environment': 'Desarrollo' if settings.DEBUG else 'Producción',
            },
            'technical': {
                'django_version': django.get_version(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': platform.system(),
                'database': 'SQLite 3.x',  # Puedes hacer esto dinámico
                'storage': '2.3 GB / 10 GB',  # Puedes calcular esto dinámicamente
            },
            'company': {
                'name': request.user.company.name if request.user.company else 'Sin empresa',
                'subscription': request.user.company.subscription_type if request.user.company else 'basic',
                'users': request.user.company.users.filter(is_active=True).count() if request.user.company else 0,
                'max_users': request.user.company.max_users if request.user.company else 0,
            }
        }
        
        return Response(system_info)


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
        token = request.data.get('token')
        
        if not token:
            return Response({
                'status': 'error',
                'message': 'Token requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            from django.contrib.auth import get_user_model
            
            # Validar el token
            validated_token = UntypedToken(token)
            user_id = validated_token.get('user_id')
            
            # Obtener el usuario
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            return Response({
                'status': 'success',
                'message': 'Token válido',
                'user': ProfileSerializer(user).data,
                'expires_at': validated_token.get('exp')
            })
            
        except TokenError:
            return Response({
                'status': 'error',
                'message': 'Token inválido o expirado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Error al validar token',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
