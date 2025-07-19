"""
URLs para EmailTrackingService
"""
from django.urls import path, include
from inventory.views.email_tracking_views import (
    EmailTrackingPixelView,
    EmailClickTrackingView,
    GmailWebhookView,
    EmailTrackingAPIView,
    EmailPatternsAPIView,
    EmailInsightsAPIView,
    EmailCampaignAPIView,
    email_tracking_stats,
    setup_gmail_integration
)

# URLs para tracking de emails (sin autenticación para permitir tracking)
tracking_patterns = [
    # Pixel de tracking para aperturas
    path('pixel/<str:tracking_id>/', EmailTrackingPixelView.as_view(), name='email_tracking_pixel'),
    
    # Tracking de clicks
    path('click/<str:tracking_id>/', EmailClickTrackingView.as_view(), name='email_click_tracking'),
    
    # Webhook de Gmail
    path('webhook/gmail/', GmailWebhookView.as_view(), name='gmail_webhook'),
]

# URLs para API (requieren autenticación)
api_patterns = [
    # Gestión de campañas (ruta directa)
    path('campaigns/', EmailCampaignAPIView.as_view(), name='email_campaigns'),
    
    # Analytics (ruta directa)
    path('analytics/', EmailTrackingAPIView.as_view(), name='email_analytics'),
    
    # Análisis de patrones (ruta directa)
    path('patterns/', EmailPatternsAPIView.as_view(), name='email_patterns'),
    
    # Insights de IA (ruta directa)
    path('insights/', EmailInsightsAPIView.as_view(), name='email_insights'),
    
    # API principal de tracking
    path('api/', EmailTrackingAPIView.as_view(), name='email_tracking_api'),
    
    # Análisis de patrones (ruta API)
    path('api/patterns/', EmailPatternsAPIView.as_view(), name='email_patterns_api'),
    
    # Insights de IA (ruta API)
    path('api/insights/', EmailInsightsAPIView.as_view(), name='email_insights_api'),
    
    # Gestión de campañas (ruta API)
    path('api/campaigns/', EmailCampaignAPIView.as_view(), name='email_campaigns_api'),
    
    # Estadísticas rápidas
    path('api/stats/', email_tracking_stats, name='email_tracking_stats'),
    
    # Configuración de Gmail
    path('api/setup-gmail/', setup_gmail_integration, name='setup_gmail_integration'),
]

# Combinar todos los patrones
urlpatterns = tracking_patterns + api_patterns
