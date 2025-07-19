"""
URLs para Gmail OAuth2 y Webhooks
"""
from django.urls import path
from inventory.views.gmail_webhook_views import (
    GmailOAuthView,
    gmail_oauth_callback,
    GmailWebhookView,
    GmailWebhookStatusView,
    test_gmail_webhook
)

urlpatterns = [
    # OAuth2 endpoints
    path('auth/', GmailOAuthView.as_view(), name='gmail-oauth'),
    path('auth/callback/', gmail_oauth_callback, name='gmail-oauth-callback'),
    
    # Webhook endpoints
    path('webhook/', GmailWebhookView.as_view(), name='gmail-webhook'),
    path('webhook/status/', GmailWebhookStatusView.as_view(), name='gmail-webhook-status'),
    
    # Testing endpoint
    path('test-webhook/', test_gmail_webhook, name='test-gmail-webhook'),
]
