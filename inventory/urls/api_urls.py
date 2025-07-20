"""
URLs para todos los ViewSets principales del API de inventory
"""
from rest_framework.routers import DefaultRouter
from .. import views
from ..views.purchase_order_views import (
    PurchaseOrderViewSet, 
    PurchaseOrderTrackingViewSet, 
    PurchaseOrderEmailLogViewSet
)
from ..views.purchase_order_test_views import PurchaseOrderTestViewSet

print("🚀 Cargando API URLs - ViewSets principales")

# Router principal para todos los ViewSets
router = DefaultRouter()

# 📦 VIEWSETS PRINCIPALES DE INVENTORY
print("📦 Registrando ViewSets principales...")
router.register(r'categories', views.CategoryViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'sales', views.SaleViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'inventory-history', views.InventoryHistoryViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'leads', views.LeadViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'inventory-items', views.InventoryItemViewSet)
router.register(r'opportunities', views.OpportunityViewSet)

# 🚨 VIEWSETS DE ÓRDENES DE COMPRA
print("🚨 Registrando ViewSets de órdenes de compra...")
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-orders')
router.register(r'purchase-order-tracking', PurchaseOrderTrackingViewSet, basename='purchase-order-tracking')
router.register(r'purchase-order-emails', PurchaseOrderEmailLogViewSet, basename='purchase-order-emails')

# 🤖 VIEWSETS DE AI + WHATSAPP TESTING
print("🤖 Registrando ViewSets de AI + WhatsApp testing...")
router.register(r'purchase-orders-ai-test', PurchaseOrderTestViewSet, basename='purchase-orders-ai-test')

print(f"✅ API URLs cargadas - {len(router.registry)} ViewSets registrados")
print(f"📊 URLs generadas: {len(router.urls)}")

# URLs que se exportarán
urlpatterns = router.urls
