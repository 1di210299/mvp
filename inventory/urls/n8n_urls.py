"""
URLs específicas para integración con n8n
"""
from django.urls import path
from inventory.views.n8n_api_views import (
    create_order,
    order_callback,
    tenant_config
)

app_name = 'n8n_api'

urlpatterns = [
    # Endpoint para crear órdenes (desde n8n o frontend)
    path('orders/', create_order, name='create_order'),
    
    # Endpoint para callbacks de n8n (sin autenticación)
    path('orders/callback/', order_callback, name='order_callback'),
    
    # Endpoint para configuración del tenant
    path('tenant/config/', tenant_config, name='tenant_config'),
]
