"""
URLs para las APIs de órdenes de compra
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.views.purchase_order_views import (
    PurchaseOrderViewSet,
    PurchaseOrderTrackingViewSet,
    PurchaseOrderEmailLogViewSet
)

# Crear router para las APIs de órdenes de compra
purchase_order_router = DefaultRouter()
purchase_order_router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')
purchase_order_router.register(r'purchase-order-tracking', PurchaseOrderTrackingViewSet, basename='purchaseordertracking')
purchase_order_router.register(r'purchase-order-emails', PurchaseOrderEmailLogViewSet, basename='purchaseorderemaillog')

# URLs específicas para órdenes de compra
purchase_order_urls = [
    path('api/', include(purchase_order_router.urls)),
]

# Exportar las URLs para el módulo principal
urlpatterns = purchase_order_urls
