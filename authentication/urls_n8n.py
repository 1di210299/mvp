"""
URLs para el flujo N8N de onboarding de tenants
"""
from django.urls import path, include
from . import views_n8n

app_name = 'n8n'

urlpatterns = [
    # Gestión de tenants
    path('tenants/', views_n8n.TenantCreateAPIView.as_view(), name='tenant-create'),
    path('tenants/list/', views_n8n.TenantListAPIView.as_view(), name='tenant-list'),
    path('tenants/<uuid:tenant_id>/', views_n8n.TenantDetailAPIView.as_view(), name='tenant-detail'),
    
    # Onboarding
    path('tenants/<uuid:tenant_id>/verify-domain/', views_n8n.DomainVerificationAPIView.as_view(), name='verify-domain'),
    path('tenants/<uuid:tenant_id>/setup-whatsapp/', views_n8n.WhatsAppSetupAPIView.as_view(), name='setup-whatsapp'),
    
    # Servicios de comunicación
    path('tenants/<uuid:tenant_id>/whatsapp/send/', views_n8n.WhatsAppSendAPIView.as_view(), name='whatsapp-send'),
    path('tenants/<uuid:tenant_id>/email/send/', views_n8n.EmailSendAPIView.as_view(), name='email-send'),
    
    # Webhooks
    path('webhook/whatsapp/', views_n8n.WhatsAppWebhookAPIView.as_view(), name='whatsapp-webhook'),
    
    # Reportes y logs
    path('tenants/<uuid:tenant_id>/usage/', views_n8n.TenantUsageAPIView.as_view(), name='tenant-usage'),
    path('tenants/<uuid:tenant_id>/logs/', views_n8n.UsageLogListAPIView.as_view(), name='usage-logs'),
]
