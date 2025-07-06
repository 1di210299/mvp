from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'inventory-items', views.InventoryItemViewSet)
router.register(r'transactions', views.TransactionViewSet)

# CRM ViewSets
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'leads', views.LeadViewSet, basename='lead')
router.register(r'opportunities', views.OpportunityViewSet, basename='opportunity')
router.register(r'contacts', views.ContactViewSet, basename='contact')
router.register(r'activities', views.ActivityViewSet, basename='activity')

urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
    
    # Vistas adicionales de inventario
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('products/<int:product_id>/stock/', views.ProductStockView.as_view(), name='product-stock'),
    path('low-stock/', views.LowStockView.as_view(), name='low-stock'),
    path('stock-movements/', views.StockMovementsView.as_view(), name='stock-movements'),
    
    # CRM Dashboard
    path('crm/dashboard/', views.CRMDashboardView.as_view(), name='crm-dashboard'),
]