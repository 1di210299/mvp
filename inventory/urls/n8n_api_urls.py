"""
URLs para APIs REST con n8n
"""
from django.urls import path, include
from inventory.views.n8n_api_views import (
    create_order,
    order_callback,
    tenant_config
)

urlpatterns = [
    # API para crear órdenes (desde frontend o externa)
    path('orders/', create_order, name='create_order'),
    
    # Callback para recibir updates de n8n
    path('orders/callback/', order_callback, name='order_callback'),
    
    # Configuración del tenant
    path('tenant/config/', tenant_config, name='tenant_config'),
    
    # Onboarding de tenants
    path('tenant/', include('inventory.urls.tenant_onboarding_urls')),
]
