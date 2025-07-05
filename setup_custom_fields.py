#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para crear migraciones de campos personalizados
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    """Ejecutar comandos de Django"""
    print("🔧 Creando migraciones para campos personalizados...")
    
    try:
        # Verificar modelos
        print("1. Verificando modelos...")
        execute_from_command_line(['manage.py', 'check'])
        print("   ✅ Modelos OK")
        
        # Crear migraciones
        print("2. Creando migraciones...")
        execute_from_command_line(['manage.py', 'makemigrations', 'inventory'])
        print("   ✅ Migraciones creadas")
        
        # Aplicar migraciones
        print("3. Aplicando migraciones...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("   ✅ Migraciones aplicadas")
        
        print("\n🎉 ¡Campos personalizados listos!")
        print("Ahora puedes ejecutar: python demo_custom_fields.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
