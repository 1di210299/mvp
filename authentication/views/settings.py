"""
Vistas relacionadas con configuraciones del usuario y sistema
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ..serializers import ProfileSerializer, ChangePasswordSerializer


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
