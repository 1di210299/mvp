"""
URLs principales del módulo inventory - Punto de entrada
Este archivo se carga automáticamente cuando Django hace include('inventory.urls')
"""

from django.urls import path, include
from .. import views

print("🔥 INVENTORY URLs principales cargando desde __init__.py")

urlpatterns = [
    # 🔧 RUTAS ESPECÍFICAS (antes del router para evitar conflictos)
    path('products/intelligence/', views.ProductIntelligenceView.as_view(), name='product-intelligence'),
    path('products/smart-filters/', views.ProductSmartFiltersView.as_view(), name='product-smart-filters'),
    path('products/actions/', views.ProductActionView.as_view(), name='product-actions'),
    
    # 🎯 VISTAS INDIVIDUALES DE INVENTORY
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard-fixed/', views.InventoryDashboardView.as_view(), name='inventory-dashboard-fixed'),
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('low-stock/', views.LowStockView.as_view(), name='low-stock'),
    path('stock-movements/', views.StockMovementsView.as_view(), name='stock-movements'),
    path('filter-options/', views.FilterOptionsView.as_view(), name='filter-options'),
    
    # 📊 MÓDULOS ESPECIALIZADOS (organizados por funcionalidad)
    path('dashboards/', include('inventory.urls.dashboard_urls')),
    path('whatsapp/', include('inventory.urls.whatsapp_urls')),
    path('email-tracking/', include('inventory.urls.email_tracking_urls')),
    path('gmail-oauth/', include('inventory.urls.gmail_webhook_urls')),
    path('pdf-analysis/', include('inventory.urls.pdf_automation_urls')),
    
    # 🤖 N8N INTEGRATION APIs
    path('api/', include('inventory.urls.n8n_api_urls')),
    
    # 🔗 INTEGRACIÓN N8N (APIs simplificadas)
    path('api/', include('inventory.urls.n8n_urls')),
    
    # 🧪 OAUTH2 TESTING
    path('oauth-test/', include('inventory.urls.oauth2_test_urls')),
    
    # 🎯 ONBOARDING DE TENANTS
    path('tenant/', include('inventory.urls.tenant_onboarding_urls')),
    
    # 🚀 API PRINCIPAL (ViewSets del router) - AL FINAL
    path('', include('inventory.urls.api_urls')),
]

print("✅ INVENTORY URLs principales cargadas exitosamente desde __init__.py")
