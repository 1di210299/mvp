#!/usr/bin/env python
"""
Script específico para analizar el registry del router
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

print("🔍 ANÁLISIS DEL REGISTRY DEL ROUTER")
print("=" * 50)

# Importar el router desde la nueva ubicación
import inventory.urls.api_urls
router = inventory.urls.api_urls.router

print(f"📊 Router tiene {len(router.urls)} URLs generadas")

# Usar el atributo correcto para el registry
if hasattr(router, 'registry'):
    registry = router.registry
    print(f"✅ Registry tiene {len(registry)} ViewSets registrados")
    
    print("\n🔍 ViewSets registrados:")
    for i, item in enumerate(registry):
        print(f"   {i+1:2d}. Estructura: {item}")
        print(f"        Tipo: {type(item)}")
        print(f"        Longitud: {len(item) if hasattr(item, '__len__') else 'N/A'}")
        
        # Intentar extraer información dependiendo de la estructura
        try:
            if len(item) == 3:
                prefix, viewset_class, basename = item
                if 'purchase' in prefix.lower():
                    print(f"        ✅ {prefix} -> {viewset_class.__name__} (basename: {basename})")
                else:
                    print(f"        📝 {prefix} -> {viewset_class.__name__} (basename: {basename})")
            elif len(item) == 2:
                prefix, (viewset_class, basename) = item
                if 'purchase' in prefix.lower():
                    print(f"        ✅ {prefix} -> {viewset_class.__name__} (basename: {basename})")
                else:
                    print(f"        📝 {prefix} -> {viewset_class.__name__} (basename: {basename})")
        except Exception as e:
            print(f"        ❌ Error parseando: {e}")
            
    # Buscar específicamente nuestro ViewSet
    print("\n🎯 Buscando 'purchase-orders-ai-test':")
    found = False
    for item in registry:
        try:
            if len(item) == 3:
                prefix = item[0]
            elif len(item) == 2:
                prefix = item[0]
            else:
                continue
                
            if prefix == 'purchase-orders-ai-test':
                print(f"   ✅ ENCONTRADO: {prefix}")
                found = True
                break
        except:
            continue
    
    if not found:
        print("   ❌ NO encontrado en el registry")
        
else:
    print("❌ El router no tiene atributo 'registry'")
    print(f"   Atributos disponibles: {[attr for attr in dir(router) if not attr.startswith('_')]}")

# Verificar si el ViewSet está en el archivo api_urls.py
print("\n🔍 VERIFICANDO CÓDIGO EN API_URLS.PY:")
with open('/Users/juandiegogutierrezcortez/mvp/inventory/urls/api_urls.py', 'r') as f:
    content = f.read()
    
if 'purchase-orders-ai-test' in content:
    print("✅ El texto 'purchase-orders-ai-test' está en api_urls.py")
    
    # Extraer la línea específica
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'purchase-orders-ai-test' in line:
            print(f"   Línea {i+1}: {line.strip()}")
else:
    print("❌ El texto 'purchase-orders-ai-test' NO está en api_urls.py")

print("\n" + "=" * 50)
print("🏁 ANÁLISIS COMPLETADO")
