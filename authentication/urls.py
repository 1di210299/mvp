from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Importar desde el package viewsets organizado
from .viewsets import (
    # Authentication
    CustomTokenObtainPairView, RegisterView, CustomTokenRefreshView, TokenValidationView,
    # Model ViewSets
    CompanyViewSet, UserViewSet,
    # Profile
    ProfileView, ChangePasswordView,
    # Settings
    UserSettingsView, SystemInfoView,
    # Company Settings
    CompanyWhatsAppConfigView, WhatsAppTestView
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    # JWT Authentication - using custom login view
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),  # Cambiado a vista personalizada
    path('validate-token/', TokenValidationView.as_view(), name='token_validate'),  # NUEVO
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Settings endpoints
    path('settings/', UserSettingsView.as_view(), name='user_settings'),
    path('system-info/', SystemInfoView.as_view(), name='system_info'),
    
    # Company WhatsApp configuration endpoints
    path('company/whatsapp/config/', CompanyWhatsAppConfigView.as_view(), name='company-whatsapp-config'),
    path('company/whatsapp/test/', WhatsAppTestView.as_view(), name='company-whatsapp-test'),
    
    # ViewSets
    path('', include(router.urls)),
]
