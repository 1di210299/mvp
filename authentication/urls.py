from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importar desde el package views reorganizado
from .views import (
    # Authentication
    RegisterView, LoginView, ProfileView, ChangePasswordView, 
    TokenRefreshView, LogoutView,
    # Company Management
    CompanyViewSet, UserViewSet, CompanyWhatsAppConfigView, WhatsAppTestView,
    # Settings
    UserSettingsView, SystemInfoView,
)
from .views.tenant_auth import TenantAuthView, TenantConfigView
from .views.communication_config import (
    tenant_communication_configs, tenant_communication_config_detail,
    tenant_bulk_config_setup, tenant_ai_config, tenant_config_summary,
    tenant_default_setup
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    # JWT Authentication - using reorganized views
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Tenant Authentication for N8N
    # Tenant authentication
    path('tenant-auth/', TenantAuthView.as_view(), name='tenant_auth'),
    path('tenant-config/', TenantConfigView.as_view(), name='tenant_config'),
    
    # Tenant Communication Configuration
    path('tenants/<uuid:tenant_id>/communication-configs/', tenant_communication_configs, name='tenant_communication_configs'),
    path('tenants/<uuid:tenant_id>/communication-configs/<str:event_type>/', tenant_communication_config_detail, name='tenant_communication_config_detail'),
    path('tenants/<uuid:tenant_id>/communication-configs/bulk-setup/', tenant_bulk_config_setup, name='tenant_bulk_config_setup'),
    path('tenants/<uuid:tenant_id>/ai-config/', tenant_ai_config, name='tenant_ai_config'),
    path('tenants/<uuid:tenant_id>/config-summary/', tenant_config_summary, name='tenant_config_summary'),
    path('tenants/<uuid:tenant_id>/default-setup/', tenant_default_setup, name='tenant_default_setup'),
    
    # Settings endpoints
    path('settings/', UserSettingsView.as_view(), name='user_settings'),
    path('system-info/', SystemInfoView.as_view(), name='system_info'),
    
    # Company WhatsApp configuration endpoints
    path('company/whatsapp/config/', CompanyWhatsAppConfigView.as_view(), name='company-whatsapp-config'),
    path('company/whatsapp/test/', WhatsAppTestView.as_view(), name='company-whatsapp-test'),
    
    # N8N Integration endpoints
    path('n8n/', include('authentication.urls_n8n', namespace='n8n')),
    
    # ViewSets
    path('', include(router.urls)),
]
