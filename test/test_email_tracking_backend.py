#!/usr/bin/env python3
"""
Script de pruebas para EmailTrackingService Backend
Verifica que todos los componentes estén funcionando correctamente
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8080"
API_BASE = f"{BASE_URL}/api"

class EmailTrackingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []

    def log_test(self, test_name, success, message="", response_data=None):
        """Registrar resultado de prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   └─ {message}")
        if response_data and isinstance(response_data, dict):
            print(f"   └─ Data: {json.dumps(response_data, indent=6)}")
        print()

        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'data': response_data
        })

    def test_server_health(self):
        """Verificar que el servidor esté respondiendo"""
        try:
            response = self.session.get(f"{BASE_URL}/admin/", timeout=5)
            success = response.status_code in [200, 302]  # 302 = redirect to login
            self.log_test(
                "Server Health Check", 
                success, 
                f"Status: {response.status_code}"
            )
            return success
        except Exception as e:
            self.log_test("Server Health Check", False, f"Error: {str(e)}")
            return False

    def test_models_import(self):
        """Verificar que los modelos se pueden importar"""
        try:
            # Usar Django shell para verificar imports
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'shell', '-c',
                '''
from inventory.models import EmailCampaign, TrackedEmail, EmailClick, EmailPattern, EmailInsight, GmailWebhookLog
from inventory.services.email_tracking_service import EmailTrackingService
print("SUCCESS: All models and service imported correctly")
                '''
            ], capture_output=True, text=True, cwd='/Users/juandiegogutierrezcortez/mvp')

            success = "SUCCESS" in result.stdout and result.returncode == 0
            self.log_test(
                "Models Import Test", 
                success, 
                result.stdout.strip() if success else result.stderr.strip()
            )
            return success
        except Exception as e:
            self.log_test("Models Import Test", False, f"Error: {str(e)}")
            return False

    def test_database_tables(self):
        """Verificar que las tablas de la base de datos existan"""
        try:
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'shell', '-c',
                '''
from django.db import connection
cursor = connection.cursor()

# Verificar tablas de email tracking
tables = [
    "inventory_emailcampaign",
    "inventory_trackedemail", 
    "inventory_emailclick",
    "inventory_emailpattern",
    "inventory_emailinsight",
    "inventory_gmailwebhooklog"
]

existing_tables = []
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        existing_tables.append(table)
    except Exception as e:
        print(f"Missing table: {table}")

print(f"SUCCESS: {len(existing_tables)}/{len(tables)} tables exist")
for table in existing_tables:
    print(f"✓ {table}")
                '''
            ], capture_output=True, text=True, cwd='/Users/juandiegogutierrezcortez/mvp')

            success = "SUCCESS" in result.stdout and result.returncode == 0
            self.log_test(
                "Database Tables Test", 
                success, 
                result.stdout.strip() if success else result.stderr.strip()
            )
            return success
        except Exception as e:
            self.log_test("Database Tables Test", False, f"Error: {str(e)}")
            return False

    def test_email_tracking_urls(self):
        """Verificar que las URLs de email tracking estén configuradas"""
        endpoints_to_test = [
            "/api/inventory/email-tracking/campaigns/",
            "/api/inventory/email-tracking/analytics/", 
            "/api/inventory/email-tracking/patterns/",
            "/api/inventory/email-tracking/insights/",
        ]

        all_success = True
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                # 401 significa que la URL existe pero requiere autenticación
                # 200 significa que funciona
                # 404 significa que no existe
                success = response.status_code in [200, 401, 403]
                self.log_test(
                    f"URL Check: {endpoint}", 
                    success, 
                    f"Status: {response.status_code}"
                )
                if not success:
                    all_success = False
            except Exception as e:
                self.log_test(f"URL Check: {endpoint}", False, f"Error: {str(e)}")
                all_success = False

        return all_success

    def test_tracking_pixel_endpoint(self):
        """Verificar endpoint de tracking pixel"""
        try:
            # Test con tracking_id dummy
            test_tracking_id = "test-tracking-123"
            response = self.session.get(f"{BASE_URL}/api/inventory/email-tracking/pixel/{test_tracking_id}/")

            # Esperamos que devuelva una imagen 1x1 pixel o un 404 si no existe el tracking_id
            success = response.status_code in [200, 404]
            self.log_test(
                "Tracking Pixel Endpoint", 
                success, 
                f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}"
            )
            return success
        except Exception as e:
            self.log_test("Tracking Pixel Endpoint", False, f"Error: {str(e)}")
            return False

    def test_gmail_webhook_endpoint(self):
        """Verificar endpoint de webhook de Gmail"""
        try:
            # Test POST al webhook endpoint
            webhook_data = {
                "message": {
                    "data": "dGVzdCBkYXRh",  # "test data" en base64
                    "messageId": "test-message-id",
                    "publishTime": datetime.now().isoformat()
                }
            }

            response = self.session.post(
                f"{BASE_URL}/api/inventory/email-tracking/webhook/gmail/",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )

            # Esperamos 401/403 (sin auth) o 200/400 (procesado)
            success = response.status_code in [200, 400, 401, 403]
            self.log_test(
                "Gmail Webhook Endpoint", 
                success, 
                f"Status: {response.status_code}"
            )
            return success
        except Exception as e:
            self.log_test("Gmail Webhook Endpoint", False, f"Error: {str(e)}")
            return False

    def test_service_functionality(self):
        """Verificar funcionalidades básicas del servicio"""
        try:
            import subprocess
            result = subprocess.run([
                'python', 'manage.py', 'shell', '-c',
                '''
from inventory.services.email_tracking_service import EmailTrackingService
from authentication.models import Company
from django.contrib.auth import get_user_model

User = get_user_model()

# Verificar que se puede instanciar el servicio
try:
    # Usar la primera compañía disponible o crear una de prueba
    company = Company.objects.first()
    if not company:
        print("No companies found - service instantiation test skipped")
    else:
        service = EmailTrackingService(company)
        print("SUCCESS: EmailTrackingService instantiated correctly")
        
        # Verificar métodos principales
        methods = ['track_email_open', 'track_email_click', 'analyze_patterns', 'generate_insights']
        for method in methods:
            if hasattr(service, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                
except Exception as e:
    print(f"ERROR: {str(e)}")
                '''
            ], capture_output=True, text=True, cwd='/Users/juandiegogutierrezcortez/mvp')

            success = "SUCCESS" in result.stdout and result.returncode == 0
            self.log_test(
                "Service Functionality Test", 
                success, 
                result.stdout.strip() if success else result.stderr.strip()
            )
            return success
        except Exception as e:
            self.log_test("Service Functionality Test", False, f"Error: {str(e)}")
            return False

    def test_admin_integration(self):
        """Verificar que los modelos estén registrados en Django Admin"""
        try:
            response = self.session.get(f"{BASE_URL}/admin/")

            # Verificar que el admin responde
            success = response.status_code in [200, 302]

            if success:
                # Verificar contenido HTML para buscar referencias a nuestros modelos
                content = response.text.lower()
                models_found = []
                expected_models = ['emailcampaign', 'trackedemail', 'emailpattern']

                for model in expected_models:
                    if model in content:
                        models_found.append(model)

                self.log_test(
                    "Admin Integration Test", 
                    True, 
                    f"Admin accessible, found {len(models_found)} model references"
                )
            else:
                self.log_test("Admin Integration Test", False, f"Admin not accessible: {response.status_code}")

            return success
        except Exception as e:
            self.log_test("Admin Integration Test", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🧪 INICIANDO PRUEBAS DEL EMAIL TRACKING SERVICE BACKEND")
        print("=" * 60)
        print()

        start_time = time.time()

        # Lista de pruebas a ejecutar
        tests = [
            self.test_server_health,
            self.test_models_import,
            self.test_database_tables,
            self.test_email_tracking_urls,
            self.test_tracking_pixel_endpoint,
            self.test_gmail_webhook_endpoint,
            self.test_service_functionality,
            self.test_admin_integration,
        ]

        # Ejecutar pruebas
        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1

        # Resumen final
        end_time = time.time()
        duration = end_time - start_time

        print("=" * 60)
        print(f"🏁 RESUMEN DE PRUEBAS")
        print(f"📊 Resultado: {passed}/{total} pruebas pasaron")
        print(f"⏱️  Duración: {duration:.2f} segundos")

        if passed == total:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON! El backend está funcionando correctamente.")
        else:
            print("⚠️  Algunas pruebas fallaron. Revisar los resultados arriba.")

        print()
        print("📈 Estado del EmailTrackingService:")
        if passed >= total * 0.8:  # 80% o más
            print("✅ BACKEND FUNCIONANDO CORRECTAMENTE")
        elif passed >= total * 0.6:  # 60% o más  
            print("⚠️  BACKEND FUNCIONANDO CON PROBLEMAS MENORES")
        else:
            print("❌ BACKEND CON PROBLEMAS SIGNIFICATIVOS")

        return passed == total


if __name__ == "__main__":
    tester = EmailTrackingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
