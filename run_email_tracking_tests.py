#!/usr/bin/env python
"""
Script para ejecutar los tests de Email Tracking con configuración correcta de Django
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
    django.setup()
    
    # Ejecutar tests específicos
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Importar tests después de configurar Django
    from test_email_tracking_backend import EmailTrackingEndToEndTest, EmailTrackingTestRunner
    
    print("🚀 EJECUTANDO TESTS DE EMAIL TRACKING CON IA")
    print("=" * 80)
    
    # Ejecutar con nuestro runner personalizado
    runner = EmailTrackingTestRunner()
    result = runner.run_all_tests()
    
    # Exit code basado en el resultado
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
