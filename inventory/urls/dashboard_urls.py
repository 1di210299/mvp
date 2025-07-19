"""
URLs para Dashboard APIs REST
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

print("🚀 Dashboard URLs siendo cargado...")

from inventory.views.dashboard_views import (
    DashboardAPIViewSet,
    PurchaseOrderDashboardViewSet,
    EmailTrackingDashboardViewSet
)

print("✅ ViewSets de dashboard importados exitosamente")

# Router para ViewSets
router = DefaultRouter()
router.register(r'dashboard', DashboardAPIViewSet, basename='dashboard-api')
router.register(r'purchase-orders-dashboard', PurchaseOrderDashboardViewSet, basename='purchase-orders-dashboard')
router.register(r'email-tracking-dashboard', EmailTrackingDashboardViewSet, basename='email-tracking-dashboard')

urlpatterns = [
    # API endpoints REST - Directamente el router sin prefijo 'api/'
    path('', include(router.urls)),
]

"""
Endpoints disponibles (bajo /api/inventory/dashboards/):

📊 DASHBOARD GENERAL:
- GET /api/inventory/dashboards/dashboard/overview/
- GET /api/inventory/dashboards/dashboard/activity-chart/

📋 PURCHASE ORDERS DASHBOARD:
- GET /api/inventory/dashboards/purchase-orders-dashboard/overview/
- GET /api/inventory/dashboards/purchase-orders-dashboard/orders-list/
- GET /api/inventory/dashboards/purchase-orders-dashboard/suppliers-list/

📧 EMAIL TRACKING DASHBOARD:
- GET /api/inventory/dashboards/email-tracking-dashboard/overview/
- GET /api/inventory/dashboards/email-tracking-dashboard/daily-performance/
- GET /api/inventory/dashboards/email-tracking-dashboard/emails-list/
- GET /api/inventory/dashboards/email-tracking-dashboard/campaigns-list/
- GET /api/inventory/dashboards/email-tracking-dashboard/top-performing-emails/

Filtros disponibles (query params):
- date_from: YYYY-MM-DD
- date_to: YYYY-MM-DD  
- status: pending, confirmed, completed, cancelled
- supplier: ID del supplier
- campaign: ID de la campaña
- page: número de página
- page_size: tamaño de página
- days: número de días para performance

Ejemplos de uso:
GET /api/inventory/dashboards/purchase-orders-dashboard/overview/?date_from=2024-01-01&status=pending
GET /api/inventory/dashboards/email-tracking-dashboard/daily-performance/?days=7
GET /api/inventory/dashboards/purchase-orders-dashboard/orders-list/?page=1&page_size=20&supplier=123
"""
