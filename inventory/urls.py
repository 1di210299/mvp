from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views.purchase_order_views import (
    PurchaseOrderViewSet, 
    PurchaseOrderTrackingViewSet, 
    PurchaseOrderEmailLogViewSet
)
from .views.dashboard_views import (
    DashboardAPIViewSet,
    PurchaseOrderDashboardViewSet,
    EmailTrackingDashboardViewSet
)

print("🔥 URLs.py recargado - Dashboard URLs incluidos v3")

router = DefaultRouter()
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

# 🚨 NUEVAS RUTAS: Sistema de Órdenes de Compra Automáticas
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-orders')
router.register(r'purchase-order-tracking', PurchaseOrderTrackingViewSet, basename='purchase-order-tracking')
router.register(r'purchase-order-emails', PurchaseOrderEmailLogViewSet, basename='purchase-order-emails')

# 📊 DASHBOARD API ViewSets - Movido a dashboard_urls.py separado
# print("🚀 Iniciando registro de Dashboard ViewSets...")
# try:
#     print("📝 Registrando DashboardAPIViewSet...")
#     router.register(r'dashboards/dashboard', DashboardAPIViewSet, basename='dashboard-api')
#     print("📝 Registrando PurchaseOrderDashboardViewSet...")
#     router.register(r'dashboards/purchase-orders-dashboard', PurchaseOrderDashboardViewSet, basename='purchase-orders-dashboard')
#     print("📝 Registrando EmailTrackingDashboardViewSet...")
#     router.register(r'dashboards/email-tracking-dashboard', EmailTrackingDashboardViewSet, basename='email-tracking-dashboard')
#     print("✅ Dashboard ViewSets registrados exitosamente")
#     print(f"🔍 Router URLs ahora: {len(router.urls)} rutas registradas")
# except Exception as e:
#     print(f"❌ Error registrando Dashboard ViewSets: {e}")
#     import traceback
#     traceback.print_exc()

urlpatterns = [
    # 🔧 FIX: Rutas específicas ANTES del router para evitar conflictos
    # Nuevos endpoints de inteligencia de productos
    path('products/intelligence/', views.ProductIntelligenceView.as_view(), name='product-intelligence'),
    path('products/smart-filters/', views.ProductSmartFiltersView.as_view(), name='product-smart-filters'),
    path('products/actions/', views.ProductActionView.as_view(), name='product-actions'),
    
    # 📧 EMAIL TRACKING SERVICE - Nuevas URLs
    path('email-tracking/', include('inventory.urls.email_tracking_urls')),
    
    # 🔗 GMAIL WEBHOOKS & OAUTH - Nuevas URLs
    path('gmail-oauth/', include('inventory.urls.gmail_webhook_urls')),
    
    # 📄 PDF ANALYSIS & AUTOMATION - Nuevas URLs
    path('pdf-analysis/', include('inventory.urls.pdf_automation_urls')),
    
    # 📊 MVP DASHBOARDS - Rutas incluidas directamente en el router principal
    path('dashboards/', include('inventory.urls.dashboard_urls')),
    
    # Vistas adicionales de inventario
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard-fixed/', views.InventoryDashboardView.as_view(), name='inventory-dashboard-fixed'),  # FIX: Nueva vista corregida
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('low-stock/', views.LowStockView.as_view(), name='low-stock'),
    path('stock-movements/', views.StockMovementsView.as_view(), name='stock-movements'),
    path('filter-options/', views.FilterOptionsView.as_view(), name='filter-options'),
    
    # 🔧 Router al FINAL para que no intercepte las rutas específicas
    path('', include(router.urls)),
]