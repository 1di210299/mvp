"""
URLs para webhooks de WhatsApp
"""
from django.urls import path
from inventory.views import webhook_views
from inventory.views.whatsapp_webhook import WhatsAppWebhookView, twilio_whatsapp_webhook

app_name = 'whatsapp'

urlpatterns = [
    # Webhook principal unificado (Meta WhatsApp Business)
    path('webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    
    # Webhook específico para Twilio (legacy support)
    path('webhook/twilio/', twilio_whatsapp_webhook, name='twilio_webhook'),
    
    # Legacy webhooks (mantener compatibilidad)
    path('webhook/meta/', webhook_views.meta_whatsapp_webhook, name='meta-webhook-legacy'),
    path('webhook/twilio-legacy/', webhook_views.twilio_whatsapp_webhook, name='twilio-webhook-legacy'),
    
    # API para enviar órdenes de compra por WhatsApp
    path('send-order/', webhook_views.send_purchase_order_whatsapp, name='send-order'),
    
    # API para obtener estado de mensajes WhatsApp
    path('status/<str:message_id>/', webhook_views.whatsapp_message_status, name='message-status'),
]
