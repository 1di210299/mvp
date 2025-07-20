#!/usr/bin/env python
"""
Script para probar específicamente la importación en urls.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

print("🔍 PROBANDO IMPORTACIONES EN URLS.PY")
print("=" * 50)

# Probar cada importación individualmente
print("1️⃣ Probando: from django.urls import path, include")
try:
    from django.urls import path, include
    print("   ✅ Exitoso")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("2️⃣ Probando: from rest_framework.routers import DefaultRouter")
try:
    from rest_framework.routers import DefaultRouter
    print("   ✅ Exitoso")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("3️⃣ Probando: from . import views")
try:
    import inventory.views as views
    print("   ✅ Exitoso")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("4️⃣ Probando: from .views.purchase_order_views import ...")
try:
    from inventory.views.purchase_order_views import (
        PurchaseOrderViewSet, 
        PurchaseOrderTrackingViewSet, 
        PurchaseOrderEmailLogViewSet
    )
    print("   ✅ Exitoso")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("5️⃣ Probando: from .views.dashboard_views import ...")
try:
    from inventory.views.dashboard_views import (
        DashboardAPIViewSet,
        PurchaseOrderDashboardViewSet,
        EmailTrackingDashboardViewSet
    )
    print("   ✅ Exitoso")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("6️⃣ Probando: from .views.purchase_order_test_views import PurchaseOrderTestViewSet")
try:
    from inventory.views.purchase_order_test_views import PurchaseOrderTestViewSet
    print(f"   ✅ Exitoso - Clase: {PurchaseOrderTestViewSet}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n7️⃣ Probando recrear el router tal como está en urls.py...")
try:
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

    # PURCHASE ORDER VIEWSETS
    router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-orders')
    router.register(r'purchase-order-tracking', PurchaseOrderTrackingViewSet, basename='purchase-order-tracking')
    router.register(r'purchase-order-emails', PurchaseOrderEmailLogViewSet, basename='purchase-order-emails')

    print(f"   ✅ Router creado exitosamente hasta aquí - {len(router.registry)} ViewSets")
    
    # AQUÍ EL PROBLEMA
    print("🎯 Probando registrar PurchaseOrderTestViewSet...")
    router.register(r'purchase-orders-ai-test', PurchaseOrderTestViewSet, basename='purchase-orders-ai-test')
    print(f"   ✅ PurchaseOrderTestViewSet registrado - Total: {len(router.registry)} ViewSets")
    
    # Verificar que se registró
    found = False
    for prefix, viewset_class, basename in router.registry:
        if prefix == 'purchase-orders-ai-test':
            found = True
            print(f"   ✅ CONFIRMADO: {prefix} está en el registry")
            break
    
    if not found:
        print("   ❌ EXTRAÑO: No se encontró en el registry después del registro")
    
except Exception as e:
    print(f"   ❌ Error creando router: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🏁 ANÁLISIS COMPLETADO")
