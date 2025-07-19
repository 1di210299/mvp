from django.urls import path, include

# URLs simplificadas solo para email tracking
urlpatterns = [
    # 📧 EMAIL TRACKING SERVICE - URLs principales
    path('email-tracking/', include('inventory.urls.email_tracking_urls')),
    
    # 🔗 GMAIL WEBHOOKS & OAUTH - URLs para webhooks
    path('gmail-oauth/', include('inventory.urls.gmail_webhook_urls')),
]
