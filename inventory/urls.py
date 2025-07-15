from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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

urlpatterns = [
    # 🔧 FIX: Rutas específicas ANTES del router para evitar conflictos
    # Nuevos endpoints de inteligencia de productos
    path('products/intelligence/', views.ProductIntelligenceView.as_view(), name='product-intelligence'),
    path('products/smart-filters/', views.ProductSmartFiltersView.as_view(), name='product-smart-filters'),
    path('products/actions/', views.ProductActionView.as_view(), name='product-actions'),
    
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