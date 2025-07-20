#!/usr/bin/env python
"""
Script de debugging para analizar el problema de URLs
"""
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

print("=" * 60)
print("🔍 ANÁLISIS COMPLETO DEL PROBLEMA DE URLs")
print("=" * 60)

# 1. Verificar que el ViewSet se pueda importar
print("\n1️⃣ VERIFICANDO IMPORTACIÓN DEL VIEWSET:")
try:
    from inventory.views.purchase_order_test_views import PurchaseOrderTestViewSet
    print("✅ PurchaseOrderTestViewSet importado exitosamente")
    print(f"   📍 Clase: {PurchaseOrderTestViewSet}")
    print(f"   📍 Módulo: {PurchaseOrderTestViewSet.__module__}")
except Exception as e:
    print(f"❌ Error importando ViewSet: {e}")
    import traceback
    traceback.print_exc()

# 2. Verificar el router de inventory
print("\n2️⃣ VERIFICANDO ROUTER DE INVENTORY:")
try:
    import inventory.urls
    router = inventory.urls.router
    print(f"✅ Router cargado con {len(router.urls)} URLs")
    print(f"✅ Registry tiene {len(router._registry)} ViewSets registrados")
    
    print("\n🔍 ViewSets registrados en el router:")
    for prefix, (viewset, basename) in router._registry.items():
        if 'purchase' in prefix.lower():
            print(f"   ✅ {prefix} -> {viewset.__name__} (basename: {basename})")
        else:
            print(f"   📝 {prefix} -> {viewset.__name__} (basename: {basename})")
            
except Exception as e:
    print(f"❌ Error cargando inventory.urls: {e}")
    import traceback
    traceback.print_exc()

# 3. Verificar las URLs principales de Django
print("\n3️⃣ VERIFICANDO URLs PRINCIPALES:")
try:
    from django.urls import get_resolver
    from django.conf import urls
    
    resolver = get_resolver()
    print(f"✅ Resolver principal cargado")
    
    # Buscar rutas de API inventory
    print("\n🔍 Buscando rutas de api/inventory/:")
    found_inventory = False
    
    def find_urls(urlpatterns, prefix=""):
        for pattern in urlpatterns:
            pattern_str = str(pattern.pattern)
            full_pattern = prefix + pattern_str
            
            if hasattr(pattern, 'url_patterns'):
                # Es un include(), buscar recursivamente
                if 'inventory' in pattern_str:
                    print(f"   🔗 ENCONTRADO INCLUDE: {full_pattern}")
                    find_urls(pattern.url_patterns, full_pattern)
            else:
                # Es una URL directa
                if 'purchase-orders-ai-test' in full_pattern:
                    print(f"   ✅ ENCONTRADA: {full_pattern}")
                    return True
        return False
    
    found = find_urls(resolver.url_patterns)
    if not found:
        print("   ❌ NO se encontró purchase-orders-ai-test")
        
except Exception as e:
    print(f"❌ Error verificando URLs principales: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar estado del servidor
print("\n4️⃣ VERIFICANDO CONFIGURACIÓN DEL SERVIDOR:")
try:
    from django.core.management import execute_from_command_line
    from django.conf import settings
    
    print(f"✅ Settings: {settings.SETTINGS_MODULE}")
    print(f"✅ Debug: {settings.DEBUG}")
    print(f"✅ Apps instaladas: {len(settings.INSTALLED_APPS)}")
    
    if 'inventory' in settings.INSTALLED_APPS:
        print("✅ App 'inventory' está en INSTALLED_APPS")
    else:
        print("❌ App 'inventory' NO está en INSTALLED_APPS")
        
except Exception as e:
    print(f"❌ Error verificando configuración: {e}")

print("\n" + "=" * 60)
print("🏁 ANÁLISIS COMPLETADO")
print("=" * 60)
