#!/usr/bin/env python3
"""
Test básico para diagnosticar problemas
"""
import os
import sys

print("🔍 DIAGNÓSTICO DEL SISTEMA")
print("=" * 40)

# 1. Verificar Python
print(f"✅ Python: {sys.version}")
print(f"✅ Path: {sys.executable}")

# 2. Verificar ruta del proyecto
current_dir = os.getcwd()
print(f"✅ Directorio actual: {current_dir}")

# 3. Verificar que Django está disponible
try:
    import django
    print(f"✅ Django: {django.get_version()}")
except ImportError as e:
    print(f"❌ Django no disponible: {e}")
    sys.exit(1)

# 4. Configurar Django
sys.path.append('/Users/juandiegogutierrezcortez/mvp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')

try:
    django.setup()
    print("✅ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

# 5. Verificar settings
try:
    from django.conf import settings
    print(f"✅ Settings cargados: {settings.SECRET_KEY[:10]}...")
    
    # Verificar configuraciones específicas para Gmail
    config_items = [
        'GMAIL_CLIENT_ID',
        'GMAIL_CLIENT_SECRET',
        'GMAIL_REDIRECT_URI',
        'GOOGLE_CLOUD_PROJECT_ID',
        'PUBSUB_TOPIC_NAME',
        'PUBSUB_SUBSCRIPTION_NAME',
        'PUBSUB_WEBHOOK_URL'
    ]
    
    print("\n📋 CONFIGURACIONES:")
    for item in config_items:
        value = getattr(settings, item, '')
        configured = bool(value)
        status = "✅" if configured else "❌"
        print(f"  {status} {item}: {'Configurado' if configured else 'NO CONFIGURADO'}")
        
except Exception as e:
    print(f"❌ Error cargando settings: {e}")
    sys.exit(1)

# 6. Verificar importación de servicios
try:
    from inventory.services.gmail_oauth_service import gmail_oauth_service
    print("✅ gmail_oauth_service importado")
    
    from inventory.services.pubsub_service import pubsub_service  
    print("✅ pubsub_service importado")
    
    from inventory.services.email_tracking_service import EmailTrackingService
    print("✅ EmailTrackingService importado")
    
except Exception as e:
    print(f"❌ Error importando servicios: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 7. Test básico de servicios
print("\n🧪 TESTS BÁSICOS:")

try:
    # Test Gmail OAuth Service
    is_available = gmail_oauth_service.is_available()
    print(f"  📧 Gmail OAuth disponible: {'✅' if is_available else '❌'}")
    
    # Test Pub/Sub Service
    pubsub_available = pubsub_service.is_available()
    print(f"  📡 Pub/Sub disponible: {'✅' if pubsub_available else '❌'}")
    
    # Test Email Tracking Service
    email_service = EmailTrackingService(company_id=1)
    print(f"  📨 EmailTrackingService: ✅")
    
except Exception as e:
    print(f"❌ Error en tests básicos: {e}")
    import traceback
    traceback.print_exc()

print("\n✨ DIAGNÓSTICO COMPLETADO")
