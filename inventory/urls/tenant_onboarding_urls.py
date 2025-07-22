"""
URLs para onboarding y configuración de tenants
"""
from django.urls import path
from inventory.views.tenant_onboarding_views import (
    setup_new_tenant,
    gmail_oauth_start,
    gmail_oauth_callback,
    tenant_status,
    test_integrations
)

app_name = 'tenant_onboarding'

urlpatterns = [
    # Setup completo de nuevo tenant (admin only)
    path('setup/', setup_new_tenant, name='setup_new_tenant'),
    
    # OAuth2 de Gmail
    path('gmail-oauth/start/', gmail_oauth_start, name='gmail_oauth_start'),
    path('gmail-oauth/callback/', gmail_oauth_callback, name='gmail_oauth_callback'),
    
    # Status y validación
    path('status/', tenant_status, name='tenant_status'),
    
    # Pruebas de integración
    path('test/', test_integrations, name='test_integrations'),
]
