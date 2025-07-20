#!/usr/bin/env python
"""
🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA AI + WHATSAPP
Script para detectar problemas de configuración, imports y URLs
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

def print_separator(title):
    print(f"\n{'='*80}")
    print(f"🔍 {title}")
    print(f"{'='*80}")

def check_file_structure():
    """Verificar estructura de archivos en inventory/"""
    print_separator("ESTRUCTURA DE ARCHIVOS EN INVENTORY/")
    
    inventory_path = Path("/Users/juandiegogutierrezcortez/mvp/inventory")
    
    print(f"📁 Directorio base: {inventory_path}")
    print(f"📁 Existe: {inventory_path.exists()}")
    
    # Verificar archivos clave
    key_files = [
        "urls.py",
        "views/__init__.py", 
        "views/purchase_order_test_views.py",
        "services/purchase_order_ai_service.py",
        "views/whatsapp_webhook.py"
    ]
    
    for file_path in key_files:
        full_path = inventory_path / file_path
        print(f"📄 {file_path}: {'✅ Existe' if full_path.exists() else '❌ NO existe'}")
    
    # Listar todos los archivos en views/
    views_dir = inventory_path / "views"
    if views_dir.exists():
        print(f"\n📁 Contenido de views/:")
        for item in sorted(views_dir.iterdir()):
            if item.is_file() and item.suffix == '.py':
                print(f"   📄 {item.name}")

def check_imports():
    """Verificar que todos los imports funcionen"""
    print_separator("VERIFICACIÓN DE IMPORTS")
    
    imports_to_test = [
        ("inventory.views.purchase_order_test_views", "PurchaseOrderTestViewSet"),
        ("inventory.services.purchase_order_ai_service", "purchase_order_ai_service"),
        ("inventory.views.whatsapp_webhook", "WhatsAppWebhookView"),
        ("inventory.models", "PurchaseOrder"),
        ("inventory.serializers", "PurchaseOrderSerializer")
    ]
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            obj = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}: {obj}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: ERROR - {e}")

def check_url_registration():
    """Verificar registro de URLs"""
    print_separator("VERIFICACIÓN DE URLS")
    
    try:
        from django.urls import get_resolver
        from django.core.management import call_command
        
        # Obtener todas las URLs
        resolver = get_resolver()
        
        print("🔍 Buscando URLs relacionadas con 'purchase' y 'ai'...")
        
        def print_urls(urllist, prefix=""):
            for url in urllist:
                pattern = str(url.pattern)
                if hasattr(url, 'url_patterns'):
                    # Es un include, recursivo
                    print_urls(url.url_patterns, prefix + pattern)
                else:
                    full_pattern = prefix + pattern
                    if 'purchase' in full_pattern.lower() or 'ai' in full_pattern.lower():
                        callback = getattr(url, 'callback', None)
                        name = getattr(url, 'name', 'No name')
                        print(f"📌 {full_pattern} -> {callback} (name: {name})")
        
        print_urls(resolver.url_patterns)
        
    except Exception as e:
        print(f"❌ Error obteniendo URLs: {e}")

def check_router_registration():
    """Verificar registro en el router de DRF"""
    print_separator("VERIFICACIÓN DEL ROUTER DRF")
    
    try:
        from inventory.urls import router
        
        print(f"🔍 Router: {router}")
        print(f"🔍 Tipo: {type(router)}")
        
        # Verificar URLs registradas en el router
        print("\n📋 ViewSets registrados en el router:")
        for prefix, viewset, basename in router.registry:
            print(f"   📌 '{prefix}' -> {viewset} (basename: {basename})")
            if 'ai' in prefix.lower() or 'test' in prefix.lower():
                print(f"      🎯 ¡ENCONTRADO AI/TEST VIEWSET!")
        
        # Verificar URLs generadas por el router
        print(f"\n🔗 URLs generadas por el router:")
        urls = router.get_urls()
        for url in urls:
            pattern = str(url.pattern)
            if 'ai' in pattern.lower() or 'test' in pattern.lower():
                print(f"   🎯 {pattern} -> {url.callback}")
        
    except Exception as e:
        print(f"❌ Error verificando router: {e}")
        import traceback
        traceback.print_exc()

def check_viewset_methods():
    """Verificar métodos del ViewSet AI"""
    print_separator("VERIFICACIÓN DEL VIEWSET AI")
    
    try:
        from inventory.views.purchase_order_test_views import PurchaseOrderTestViewSet
        
        viewset = PurchaseOrderTestViewSet()
        
        print(f"✅ ViewSet creado: {viewset}")
        print(f"🔍 Tipo: {type(viewset)}")
        
        # Verificar métodos personalizados
        custom_methods = []
        for attr_name in dir(viewset):
            attr = getattr(viewset, attr_name)
            if hasattr(attr, 'detail') or hasattr(attr, 'url_path'):
                custom_methods.append(attr_name)
        
        print(f"\n📋 Métodos personalizados encontrados:")
        for method in custom_methods:
            print(f"   🎯 {method}")
        
        # Verificar métodos específicos
        expected_methods = ['test_complete_flow', 'simulate_delivery_photo', 'test_summary']
        for method_name in expected_methods:
            if hasattr(viewset, method_name):
                method = getattr(viewset, method_name)
                print(f"   ✅ {method_name}: {method}")
            else:
                print(f"   ❌ {method_name}: NO encontrado")
                
    except Exception as e:
        print(f"❌ Error verificando ViewSet: {e}")
        import traceback
        traceback.print_exc()

def check_django_urls_command():
    """Usar comando Django para mostrar URLs"""
    print_separator("COMANDO DJANGO SHOW_URLS")
    
    try:
        from io import StringIO
        from django.core.management import call_command
        
        # Capturar salida del comando
        out = StringIO()
        call_command('show_urls', stdout=out)
        urls_output = out.getvalue()
        
        # Filtrar URLs relevantes
        print("🔍 URLs que contienen 'purchase' o 'ai':")
        for line in urls_output.split('\n'):
            if 'purchase' in line.lower() or 'ai' in line.lower():
                print(f"   📌 {line}")
                
        # Buscar específicamente el ViewSet AI
        print(f"\n🔍 Buscando 'purchase-orders-ai-test':")
        ai_test_found = False
        for line in urls_output.split('\n'):
            if 'purchase-orders-ai-test' in line:
                print(f"   🎯 {line}")
                ai_test_found = True
        
        if not ai_test_found:
            print("   ❌ NO se encontró 'purchase-orders-ai-test'")
            
    except Exception as e:
        print(f"❌ Error ejecutando show_urls: {e}")

def check_ai_service():
    """Verificar servicio de AI"""
    print_separator("VERIFICACIÓN DEL SERVICIO AI")
    
    try:
        from inventory.services.purchase_order_ai_service import purchase_order_ai_service
        
        print(f"✅ Servicio AI importado: {purchase_order_ai_service}")
        print(f"🔍 Tipo: {type(purchase_order_ai_service)}")
        
        # Verificar métodos del servicio
        methods = ['analyze_whatsapp_message', 'analyze_delivery_photo', 'generate_follow_up_message']
        for method_name in methods:
            if hasattr(purchase_order_ai_service, method_name):
                print(f"   ✅ {method_name}: Disponible")
            else:
                print(f"   ❌ {method_name}: NO disponible")
                
    except Exception as e:
        print(f"❌ Error verificando servicio AI: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Función principal de diagnóstico"""
    print("🚀 INICIANDO DIAGNÓSTICO COMPLETO DEL SISTEMA AI + WHATSAPP")
    print(f"📅 Fecha: {os.popen('date').read().strip()}")
    print(f"🐍 Python: {sys.version}")
    print(f"🔧 Django: {django.get_version()}")
    
    try:
        check_file_structure()
        check_imports()
        check_ai_service()
        check_viewset_methods()
        check_router_registration()
        check_url_registration()
        check_django_urls_command()
        
        print_separator("DIAGNÓSTICO COMPLETADO")
        print("✅ Revisa los resultados arriba para identificar problemas")
        
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
