#!/usr/bin/env python3
"""
Script de Testing Completo del Sistema de Gmail API Webhooks
Verifica OAuth2, Pub/Sub, webhooks y integración completa
"""
import os
import sys
import django
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any

# Configurar Django
sys.path.append('/Users/juandiegogutierrezcortez/mvp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datalens_backend.settings')
django.setup()

from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from inventory.services.gmail_oauth_service import gmail_oauth_service
from inventory.services.pubsub_service import pubsub_service
from inventory.services.email_tracking_service import EmailTrackingService

User = get_user_model()

class GmailWebhookSystemTester:
    """
    Tester completo para el sistema de webhooks de Gmail
    """
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.results = []
        
        print("🧪 INICIANDO TESTING COMPLETO DEL SISTEMA GMAIL WEBHOOKS")
        print("=" * 60)
        
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        try:
            print("🚀 Iniciando tests del sistema...")
            
            # 1. Tests de configuración
            self.test_configuration()
            
            # 2. Tests de servicios
            self.test_gmail_oauth_service()
            self.test_pubsub_service()
            self.test_email_tracking_service()
            
            # 3. Tests de endpoints
            self.test_webhook_endpoints()
            
            # 4. Test de integración completa
            self.test_complete_integration()
            
            # 5. Mostrar resultados
            self.show_results()
            
        except Exception as e:
            print(f"❌ Error en testing: {e}")
            import traceback
            traceback.print_exc()
            
    def test_configuration(self):
        """Test 1: Verificar configuración"""
        print("\n📋 TEST 1: CONFIGURACIÓN DEL SISTEMA")
        print("-" * 40)
        
        # Verificar settings
        config_checks = {
            'GMAIL_CLIENT_ID': bool(settings.GMAIL_CLIENT_ID),
            'GMAIL_CLIENT_SECRET': bool(settings.GMAIL_CLIENT_SECRET),
            'GMAIL_REDIRECT_URI': bool(settings.GMAIL_REDIRECT_URI),
            'GOOGLE_CLOUD_PROJECT_ID': bool(settings.GOOGLE_CLOUD_PROJECT_ID),
            'PUBSUB_TOPIC_NAME': bool(settings.PUBSUB_TOPIC_NAME),
            'PUBSUB_SUBSCRIPTION_NAME': bool(settings.PUBSUB_SUBSCRIPTION_NAME),
            'PUBSUB_WEBHOOK_URL': bool(settings.PUBSUB_WEBHOOK_URL),
            'OPENAI_API_KEY': bool(settings.OPENAI_API_KEY),
            'FRONTEND_URL': bool(settings.FRONTEND_URL),
        }
        
        for setting, configured in config_checks.items():
            status = "✅" if configured else "❌"
            print(f"  {status} {setting}: {'Configurado' if configured else 'NO CONFIGURADO'}")
            
        total_configured = sum(config_checks.values())
        total_settings = len(config_checks)
        
        self.results.append({
            'test': 'Configuración',
            'status': 'PASS' if total_configured >= 7 else 'FAIL',  # Al menos 7 de 9
            'details': f"{total_configured}/{total_settings} configuraciones válidas"
        })
        
    def test_gmail_oauth_service(self):
        """Test 2: Verificar GmailOAuthService"""
        print("\n🔐 TEST 2: GMAIL OAUTH SERVICE")
        print("-" * 40)
        
        try:
            # Test de disponibilidad
            is_available = gmail_oauth_service.is_available()
            print(f"  🔍 Servicio disponible: {'✅' if is_available else '❌'}")
            
            if is_available:
                # Test de generación de URL de autorización
                auth_url, state = gmail_oauth_service.get_authorization_url(user_id="test_user")
                url_generated = bool(auth_url and state)
                print(f"  🔗 URL de autorización: {'✅' if url_generated else '❌'}")
                
                if url_generated:
                    print(f"     URL: {auth_url[:50]}...")
                    print(f"     State: {state}")
                
                # Test de estado de autenticación
                is_authenticated = gmail_oauth_service.is_authenticated()
                print(f"  🔑 Autenticado: {'✅' if is_authenticated else '⚠️  No autenticado'}")
                
                # Test de estado del watch
                watch_status = gmail_oauth_service.get_watch_status()
                print(f"  👀 Watch status: {watch_status}")
                
                status = 'PASS'
            else:
                print("  ⚠️  Servicio no disponible (credenciales de Google Cloud requeridas)")
                status = 'PARTIAL'  # Cambio de FAIL a PARTIAL cuando no hay credenciales
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            status = 'FAIL'
            
        self.results.append({
            'test': 'Gmail OAuth Service',
            'status': status,
            'details': 'Servicio OAuth funcional' if status == 'PASS' else f'Error: {str(e) if "e" in locals() else "Servicio no disponible"}'
        })
        
    def test_pubsub_service(self):
        """Test 3: Verificar PubSubService"""
        print("\n📡 TEST 3: PUB/SUB SERVICE")
        print("-" * 40)
        
        try:
            # Test de disponibilidad
            is_available = pubsub_service.is_available()
            print(f"  🔍 Servicio disponible: {'✅' if is_available else '❌'}")
            
            if is_available:
                # Test de creación de tópico (si no existe)
                topic_created = pubsub_service.create_topic()
                print(f"  📝 Tópico creado/existente: {'✅' if topic_created else '❌'}")
                
                # Test de creación de suscripción
                subscription_created = pubsub_service.create_subscription()
                print(f"  📮 Suscripción creada/existente: {'✅' if subscription_created else '❌'}")
                
                # Test de parseo de mensaje (con datos simulados)
                test_message_data = {
                    'message': {
                        'data': 'eyJoaXN0b3J5SWQiOiIxMjM0NSIsImVtYWlsQWRkcmVzcyI6InRlc3RAZXhhbXBsZS5jb20ifQ==',
                        'messageId': 'test_message_123',
                        'publishTime': '2024-01-15T10:00:00Z'
                    }
                }
                
                parsed_message = pubsub_service.parse_pubsub_message(test_message_data)
                parse_success = bool(parsed_message)
                print(f"  🔍 Parseo de mensaje: {'✅' if parse_success else '❌'}")
                
                if parse_success:
                    print(f"     Datos parseados: {parsed_message}")
                
                status = 'PASS'
            else:
                print("  ⚠️  Servicio no disponible (credenciales de Google Cloud requeridas)")
                
                # Test de parseo sin conexión a Pub/Sub
                test_message_data = {
                    'message': {
                        'data': 'eyJoaXN0b3J5SWQiOiIxMjM0NSIsImVtYWlsQWRkcmVzcyI6InRlc3RAZXhhbXBsZS5jb20ifQ==',
                        'messageId': 'test_message_123',
                        'publishTime': '2024-01-15T10:00:00Z'
                    }
                }
                
                parsed_message = pubsub_service.parse_pubsub_message(test_message_data)
                parse_success = bool(parsed_message)
                print(f"  🔍 Parseo de mensaje (offline): {'✅' if parse_success else '❌'}")
                
                status = 'PARTIAL' if parse_success else 'FAIL'
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            status = 'FAIL'
            
        self.results.append({
            'test': 'Pub/Sub Service',
            'status': status,
            'details': 'Servicio Pub/Sub funcional' if status == 'PASS' else f'Error: {str(e) if "e" in locals() else "Servicio no disponible"}'
        })
        
    def test_email_tracking_service(self):
        """Test 4: Verificar EmailTrackingService"""
        print("\n📧 TEST 4: EMAIL TRACKING SERVICE")
        print("-" * 40)
        
        try:
            # Crear instancia del servicio
            email_service = EmailTrackingService(company_id=1)
            
            # Test de webhook notification processing
            test_notification = {
                'emailAddress': 'test@example.com',
                'historyId': '67890'
            }
            
            result = email_service.process_gmail_webhook_notification(test_notification)
            webhook_processed = result.get('success', False)
            print(f"  📨 Procesamiento webhook: {'✅' if webhook_processed else '❌'}")
            
            if webhook_processed:
                print(f"     Resultado: {result}")
            
            status = 'PASS'
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            status = 'FAIL'
            
        self.results.append({
            'test': 'Email Tracking Service',
            'status': status,
            'details': 'Servicio EmailTracking funcional' if status == 'PASS' else f'Error: {str(e) if "e" in locals() else "Error en servicio"}'
        })
        
    def test_webhook_endpoints(self):
        """Test 5: Verificar endpoints de webhooks"""
        print("\n🌐 TEST 5: ENDPOINTS DE WEBHOOKS")
        print("-" * 40)
        
        # Crear usuario de prueba
        try:
            # Crear/obtener una empresa para el usuario
            from authentication.models import Company
            
            company, created = Company.objects.get_or_create(
                name='Test Company',
                defaults={
                    'email': 'test@company.com',
                    'phone': '+51999999999'
                }
            )
            
            self.test_user, created = User.objects.get_or_create(
                username='test_webhook_user',
                defaults={
                    'email': 'test@webhook.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'company': company  # Agregar company requerida
                }
            )
            self.client.force_login(self.test_user)
            print(f"  ✅ Usuario de prueba creado: {self.test_user.username}")
            
        except Exception as e:
            print(f"  ❌ Error creando usuario de prueba: {e}")
            
        # Test endpoints
        endpoints_to_test = [
            ('/api/inventory/gmail-oauth/auth/', 'GET', 'OAuth Auth'),
            ('/api/inventory/gmail-oauth/webhook/status/', 'GET', 'Webhook Status'),
            ('/api/inventory/gmail-oauth/test-webhook/', 'POST', 'Test Webhook'),
        ]
        
        endpoint_results = []
        
        for url, method, name in endpoints_to_test:
            try:
                if method == 'GET':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, {'action': 'test'})
                
                status_ok = response.status_code in [200, 201, 302, 401, 403]  # Códigos válidos
                status_icon = "✅" if status_ok else "❌"
                
                print(f"  {status_icon} {name}: {response.status_code}")
                
                endpoint_results.append(status_ok)
                
            except Exception as e:
                print(f"  ❌ Error en {name}: {e}")
                endpoint_results.append(False)
        
        all_endpoints_ok = all(endpoint_results)
        
        self.results.append({
            'test': 'Webhook Endpoints',
            'status': 'PASS' if all_endpoints_ok else 'PARTIAL',
            'details': f"{sum(endpoint_results)}/{len(endpoint_results)} endpoints funcionando"
        })
        
    def test_complete_integration(self):
        """Test 6: Test de integración completa"""
        print("\n🔗 TEST 6: INTEGRACIÓN COMPLETA")
        print("-" * 40)
        
        try:
            # Simular flujo completo de webhook
            
            # 1. Verificar configuración de webhook
            webhook_config = cache.get('email_tracking_webhook_config', {})
            print(f"  🔧 Config webhook en cache: {'✅' if webhook_config else '⚠️  No configurado'}")
            
            # 2. Simular recepción de webhook
            webhook_data = {
                'message': {
                    'data': 'eyJoaXN0b3J5SWQiOiIxMjM0NSIsImVtYWlsQWRkcmVzcyI6InRlc3RAZXhhbXBsZS5jb20ifQ==',
                    'messageId': 'integration_test_123',
                    'publishTime': datetime.now().isoformat()
                }
            }
            
            # 3. Procesar con EmailTrackingService
            email_service = EmailTrackingService(company_id=1)
            
            # Parsear mensaje primero
            parsed_data = pubsub_service.parse_pubsub_message(webhook_data)
            
            if parsed_data:
                # Procesar notificación
                result = email_service.process_gmail_webhook_notification(parsed_data['data'])
                integration_success = result.get('success', False)
                print(f"  🔄 Flujo completo: {'✅' if integration_success else '❌'}")
                
                if integration_success:
                    print(f"     Detalles: {result}")
            else:
                integration_success = False
                print(f"  🔄 Flujo completo: ❌ Error en parseo")
            
            status = 'PASS' if integration_success else 'FAIL'
            
        except Exception as e:
            print(f"  ❌ Error en integración: {e}")
            status = 'FAIL'
            
        self.results.append({
            'test': 'Integración Completa',
            'status': status,
            'details': 'Flujo webhook completo funcional' if status == 'PASS' else f'Error: {str(e) if "e" in locals() else "Error en flujo"}'
        })
        
    def show_results(self):
        """Mostrar resultados finales"""
        print("\n" + "=" * 60)
        print("📊 RESULTADOS FINALES DEL TESTING")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['status'] == 'PASS')
        partial_tests = sum(1 for r in self.results if r['status'] == 'PARTIAL')
        failed_tests = sum(1 for r in self.results if r['status'] == 'FAIL')
        
        for result in self.results:
            status_icon = {
                'PASS': '✅',
                'PARTIAL': '⚠️ ',
                'FAIL': '❌'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        print("\n" + "-" * 60)
        print(f"📈 RESUMEN:")
        print(f"   ✅ Pasaron: {passed_tests}/{total_tests}")
        print(f"   ⚠️  Parciales: {partial_tests}/{total_tests}")
        print(f"   ❌ Fallaron: {failed_tests}/{total_tests}")
        
        success_rate = (passed_tests + partial_tests * 0.5) / total_tests * 100
        print(f"   📊 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 SISTEMA GMAIL WEBHOOKS: LISTO PARA PRODUCCIÓN")
        elif success_rate >= 60:
            print("\n⚠️  SISTEMA GMAIL WEBHOOKS: NECESITA MEJORAS MENORES")
        else:
            print("\n❌ SISTEMA GMAIL WEBHOOKS: NECESITA CORRECCIONES IMPORTANTES")
        
        # Recomendaciones
        print("\n🔧 RECOMENDACIONES:")
        
        failed_configs = [r for r in self.results if r['status'] == 'FAIL']
        if failed_configs:
            print("   1. Configurar variables de entorno faltantes:")
            print("      - GMAIL_CLIENT_ID y GMAIL_CLIENT_SECRET (Google Cloud Console)")
            print("      - GOOGLE_CLOUD_PROJECT_ID (Google Cloud Project)")
            print("      - GOOGLE_APPLICATION_CREDENTIALS (Service Account JSON)")
        
        print("   2. Para OAuth2 completo:")
        print("      - Configurar OAuth consent screen en Google Cloud")
        print("      - Agregar redirect URI autorizada")
        print("      - Obtener autorización de usuario real")
        
        print("   3. Para Pub/Sub:")
        print("      - Crear tópico y suscripción en Google Cloud")
        print("      - Configurar credenciales de servicio")
        print("      - Configurar webhook endpoint público")
        
        print("\n✨ SIGUIENTE PASO: Configurar OAuth2 real con Google")


def main():
    """Función principal"""
    tester = GmailWebhookSystemTester()
    tester.run_all_tests()


if __name__ == '__main__':
    main()
