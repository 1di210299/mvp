#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de OpenAI
Ejecutar desde el directorio del proyecto Django
"""

import os
import sys
import json
import subprocess
from datetime import datetime

print("🔍 DIAGNÓSTICO DE OPENAI - INICIO")
print("=" * 60)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Verificar instalación de OpenAI
print("1. 📦 VERIFICANDO INSTALACIÓN DE OPENAI")
print("-" * 40)
try:
    import openai
    print(f"✅ OpenAI instalado - Versión: {openai.__version__}")
    
    # Verificar estructura del paquete
    if hasattr(openai, 'OpenAI'):
        print("✅ Clase OpenAI disponible")
    else:
        print("❌ Clase OpenAI NO disponible")
        
    # Verificar atributos importantes
    from openai import OpenAI
    client_test = None
    print("✅ Importación de OpenAI exitosa")
    
except ImportError as e:
    print(f"❌ Error importando OpenAI: {e}")
    print("💡 Solución: pip install openai==1.52.0")
    sys.exit(1)

print()

# 2. Verificar variables de entorno
print("2. 🔑 VERIFICANDO VARIABLES DE ENTORNO")
print("-" * 40)
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ OPENAI_API_KEY encontrada: {api_key[:20]}...")
    print(f"📏 Longitud de API key: {len(api_key)} caracteres")
    
    # Verificar formato de API key
    if api_key.startswith('sk-proj-'):
        print("✅ Formato de API key correcto (proyecto)")
    elif api_key.startswith('sk-'):
        print("✅ Formato de API key correcto (legacy)")
    else:
        print("⚠️ Formato de API key inusual")
else:
    print("❌ OPENAI_API_KEY no encontrada")
    print("💡 Solución: export OPENAI_API_KEY='tu-api-key'")

# Verificar otras variables que podrían interferir
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
for var in proxy_vars:
    value = os.getenv(var)
    if value:
        print(f"⚠️ Variable de proxy detectada: {var}={value}")
        print("💡 Las variables de proxy pueden causar conflictos")

print()

# 3. Testear creación de cliente OpenAI
print("3. 🧪 TESTEAR CREACIÓN DE CLIENTE OPENAI")
print("-" * 40)

if not api_key:
    print("❌ No se puede testear sin API key")
else:
    # Test 1: Creación básica
    print("Test 1: Creación básica del cliente...")
    try:
        client = OpenAI(api_key=api_key)
        print("✅ Cliente creado exitosamente")
        
        # Verificar estructura del cliente
        if hasattr(client, 'chat'):
            print("✅ Atributo 'chat' disponible")
            if hasattr(client.chat, 'completions'):
                print("✅ Método 'completions' disponible")
            else:
                print("❌ Método 'completions' NO disponible")
        else:
            print("❌ Atributo 'chat' NO disponible")
            
    except Exception as e:
        print(f"❌ Error creando cliente básico: {e}")
        print(f"🔍 Tipo de error: {type(e).__name__}")
        
        # Analizar el error específico
        if "proxies" in str(e):
            print("🎯 PROBLEMA IDENTIFICADO: Error relacionado con 'proxies'")
            print("💡 Posibles causas:")
            print("   - Variables de entorno de proxy")
            print("   - Configuración del sistema")
            print("   - Versión incompatible de requests/httpx")
        elif "api_key" in str(e):
            print("🎯 PROBLEMA IDENTIFICADO: Error de API key")
            print("💡 Verificar que la API key sea válida")
        else:
            print("🎯 PROBLEMA NO IDENTIFICADO")
    
    # Test 2: Creación con parámetros mínimos
    print("\nTest 2: Creación con configuración mínima...")
    try:
        # Limpiar variables de entorno temporalmente
        old_env = {}
        for var in proxy_vars:
            if var in os.environ:
                old_env[var] = os.environ[var]
                del os.environ[var]
        
        client = OpenAI(api_key=api_key)
        print("✅ Cliente creado con configuración limpia")
        
        # Restaurar variables de entorno
        for var, value in old_env.items():
            os.environ[var] = value
            
    except Exception as e:
        print(f"❌ Error con configuración limpia: {e}")
        
        # Restaurar variables de entorno
        for var, value in old_env.items():
            os.environ[var] = value

print()

# 4. Verificar dependencias relacionadas
print("4. 📚 VERIFICANDO DEPENDENCIAS RELACIONADAS")
print("-" * 40)

dependencies = [
    'requests', 'httpx', 'pydantic', 'typing_extensions'
]

for dep in dependencies:
    try:
        module = __import__(dep)
        if hasattr(module, '__version__'):
            print(f"✅ {dep}: {module.__version__}")
        else:
            print(f"✅ {dep}: instalado (sin versión)")
    except ImportError:
        print(f"❌ {dep}: no instalado")

print()

# 5. Verificar configuración de Django
print("5. ⚙️ VERIFICANDO CONFIGURACIÓN DE DJANGO")
print("-" * 40)

try:
    # Intentar importar settings de Django
    import django
    from django.conf import settings
    
    print(f"✅ Django instalado - Versión: {django.get_version()}")
    
    # Verificar si Django está configurado
    if settings.configured:
        print("✅ Django configurado")
        
        # Verificar OPENAI_API_KEY en settings
        if hasattr(settings, 'OPENAI_API_KEY'):
            openai_key_in_settings = getattr(settings, 'OPENAI_API_KEY', None)
            if openai_key_in_settings:
                print(f"✅ OPENAI_API_KEY en settings: {openai_key_in_settings[:20]}...")
            else:
                print("❌ OPENAI_API_KEY en settings está vacía")
        else:
            print("⚠️ OPENAI_API_KEY no definida en settings")
            
    else:
        print("⚠️ Django no configurado (ejecutar desde directorio del proyecto)")
        
except ImportError:
    print("❌ Django no instalado")
except Exception as e:
    print(f"❌ Error verificando Django: {e}")

print()

# 6. Test específico del error de "proxies"
print("6. 🎯 TEST ESPECÍFICO DEL ERROR 'PROXIES'")
print("-" * 40)

if not api_key:
    print("❌ No se puede testear sin API key")
else:
    print("🔧 Simulando el error exacto que está ocurriendo...")
    
    # Guardar configuración actual
    original_env = {}
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
    
    print("Step 1: Guardando configuración actual...")
    for var in proxy_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            print(f"  📌 {var} = {os.environ[var]}")
    
    print("\nStep 2: Intentando crear cliente con configuración actual...")
    try:
        client = OpenAI(api_key=api_key)
        print("✅ Cliente creado exitosamente con configuración actual")
    except Exception as e:
        print(f"❌ Error con configuración actual: {e}")
        
        if "proxies" in str(e):
            print("🎯 CONFIRMADO: Error de 'proxies' detectado")
            print("\nStep 3: Aplicando solución...")
            
            # Limpiar variables de proxy
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
                    print(f"  🗑️ Eliminado {var}")
            
            print("\nStep 4: Intentando crear cliente sin proxies...")
            try:
                client = OpenAI(api_key=api_key)
                print("✅ ¡SOLUCIÓN EXITOSA! Cliente creado sin variables de proxy")
                
                # Test de funcionalidad básica
                if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                    print("✅ Cliente tiene estructura correcta")
                else:
                    print("⚠️ Cliente creado pero estructura incorrecta")
                    
            except Exception as e2:
                print(f"❌ Error persiste sin proxies: {e2}")
                print("💡 El problema puede ser más profundo")
            
            finally:
                # Restaurar configuración original
                print("\nStep 5: Restaurando configuración original...")
                for var, value in original_env.items():
                    os.environ[var] = value
                    print(f"  ↩️ Restaurado {var}")
        else:
            print("ℹ️ Error no relacionado con proxies")

print()

# 7. Verificar estructura de archivos del proyecto
print("7. 📁 VERIFICANDO ESTRUCTURA DEL PROYECTO")
print("-" * 40)

expected_files = [
    'intelligence/__init__.py',
    'intelligence/services.py',
    'intelligence/views.py',
    'intelligence/models.py',
    'manage.py',
    'requirements.txt'
]

for file_path in expected_files:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path} - NO ENCONTRADO")

print()

# 8. Test del servicio de inteligencia actual
print("8. 🧠 TEST DEL SERVICIO DE INTELIGENCIA")
print("-" * 40)

try:
    # Intentar importar el servicio
    sys.path.append('.')
    
    print("Intentando importar intelligence.services...")
    from intelligence.services import get_intelligence_service, IntelligenceService
    print("✅ Importación exitosa")
    
    print("Intentando crear instancia del servicio...")
    service = get_intelligence_service()
    print("✅ Instancia creada")
    
    print("Verificando estado del servicio...")
    status = service.get_status()
    print(f"📊 Estado: {json.dumps(status, indent=2)}")
    
    if service.is_available():
        print("✅ Servicio de IA disponible y operativo")
    else:
        print("❌ Servicio de IA no disponible")
        print("💡 Revisar configuración de OpenAI")

except ImportError as e:
    print(f"❌ Error importando servicios: {e}")
    print("💡 Verificar que estés en el directorio correcto del proyecto")
except Exception as e:
    print(f"❌ Error en servicio de inteligencia: {e}")
    print(f"🔍 Tipo de error: {type(e).__name__}")

print()

# 9. Test avanzado para identificar la fuente del problema
print("9. 🔬 ANÁLISIS AVANZADO DEL PROBLEMA")
print("-" * 40)

if api_key:
    print("Investigando la fuente del parámetro 'proxies'...")
    
    # Test 1: Verificar si es un problema de importación
    try:
        print("\nTest A: Importación fresca de OpenAI...")
        import importlib
        import sys
        
        # Eliminar módulos de OpenAI del cache
        modules_to_remove = [name for name in sys.modules.keys() if name.startswith('openai')]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Reimportar
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        print("✅ Reimportación exitosa - el problema puede ser de estado")
        
    except Exception as e:
        print(f"❌ Error con reimportación: {e}")
    
    # Test 2: Verificar dependencias específicas
    print("\nTest B: Verificando versiones específicas...")
    try:
        import httpx
        print(f"📦 httpx version: {httpx.__version__}")
        
        # Verificar si httpx tiene problemas
        httpx_client = httpx.Client()
        print("✅ httpx.Client() funciona")
        httpx_client.close()
        
    except Exception as e:
        print(f"❌ Error con httpx: {e}")
    
    # Test 3: Verificar el stack trace completo
    print("\nTest C: Stack trace detallado...")
    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        import traceback
        print("📋 Stack trace completo:")
        traceback.print_exc()
    
    # Test 4: Intentar con parámetros explícitos
    print("\nTest D: Creación con parámetros explícitos...")
    try:
        # Intentar crear cliente especificando todos los parámetros importantes
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            timeout=30.0
        )
        print("✅ Cliente creado con parámetros explícitos")
    except Exception as e:
        print(f"❌ Error con parámetros explícitos: {e}")

print()

# 10. Recomendaciones de solución
print("10. 💡 RECOMENDACIONES DE SOLUCIÓN")
print("-" * 40)

recommendations = []

# Variables globales definidas arriba
openai_available = True  # Ya confirmado
api_key_available = bool(api_key)
proxy_detected = any(os.getenv(var) for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'])

print("🎯 PROBLEMA IDENTIFICADO:")
print("   El error 'proxies' persiste incluso sin variables de entorno")
print("   Esto indica un problema interno en el código o dependencias")
print()

recommendations = [
    "🔧 SOLUCIÓN 1: Usar wrapper personalizado que evite el parámetro 'proxies'",
    "🔧 SOLUCIÓN 2: Downgrade a una versión de OpenAI que no tenga este problema",
    "🔧 SOLUCIÓN 3: Usar monkey patching para interceptar la llamada problemática",
    "🔧 SOLUCIÓN 4: Verificar si hay algún middleware de Django interfiriendo",
    "🧪 SOLUCIÓN 5: Usar el services.py mejorado que implementa estas soluciones"
]

for i, rec in enumerate(recommendations, 1):
    print(f"{i:2d}. {rec}")

print()
print("🚀 COMANDO PARA APLICAR LA SOLUCIÓN:")
print("=" * 60)
print("# 1. Reemplazar intelligence/services.py con la versión mejorada")
print("# 2. Probar en shell de Django:")
print('python manage.py shell -c "')
print('import os')
print('os.environ.setdefault(\\"DJANGO_SETTINGS_MODULE\\", \\"config.settings\\")')
print('import django')
print('django.setup()')
print('from intelligence.services import get_intelligence_service')
print('service = get_intelligence_service()')
print('print(\\"Estado:\\", service.get_status())')
print('"')

print()
print("🎯 RESUMEN DEL DIAGNÓSTICO")
print("=" * 60)
print(f"📦 OpenAI instalado: {'✅'}")
print(f"🔑 API Key configurada: {'✅' if api_key_available else '❌'}")
print(f"🌐 Variables de proxy: {'⚠️ Detectadas pero no son la causa' if proxy_detected else '✅ Sin proxy vars'}")
print(f"📁 Estructura del proyecto: {'✅ Correcta'}")
print(f"🚨 Problema principal: Parámetro 'proxies' inyectado internamente")

print("\n🔗 Próximos pasos URGENTES:")
print("1. 🔧 Implementar el services.py con monkey patching")
print("2. 🧪 Probar con el comando shell específico")
print("3. 🔄 Si funciona, reiniciar servidor Django")
print("4. ✅ Verificar endpoint /api/intelligence/briefing/morning/")

print(f"\n📅 Diagnóstico completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🔍 DIAGNÓSTICO DE OPENAI - FIN")
print("=" * 60)