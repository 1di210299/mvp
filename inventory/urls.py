from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_stub as views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'inventory-items', views.InventoryItemViewSet)
router.register(r'transactions', views.TransactionViewSet)

urlpatterns = [
    # Custom endpoints
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.FileUploadView.as_view(), name='upload'),
    path('products/<int:product_id>/stock/', views.ProductStockView.as_view(), name='product_stock'),
    path('low-stock/', views.LowStockView.as_view(), name='low_stock'),
    path('stock-movements/', views.StockMovementsView.as_view(), name='stock_movements'),
    
    # ViewSets
    path('', include(router.urls)),
]
