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
    # Incluir todas las rutas del router
    path('', include(router.urls)),
    
    # Vistas adicionales de inventario
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('low-stock/', views.LowStockView.as_view(), name='low-stock'),
    path('stock-movements/', views.StockMovementsView.as_view(), name='stock-movements'),
]