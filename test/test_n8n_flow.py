#!/usr/bin/env python3
"""
Script de prueba para el flujo N8N de onboarding de tenants
"""
import requests
import json
import sys
import os
import uuid
import time

# Configuración
BASE_URL = "http://localhost:8080"  # Cambiar según tu configuración
API_BASE = f"{BASE_URL}/api/auth/n8n"

# Generar datos únicos para cada ejecución
test_uuid = str(uuid.uuid4())[:8]
current_time = int(time.time())

# Datos de prueba
TEST_USER = {
    "email": "admin@testcompany.com",
    "password": "admin123"
}

TEST_TENANT = {
    "name": f"Empresa de Prueba {test_uuid}",
    "domain": f"prueba-{test_uuid}.com",
    "email_address": f"admin-{test_uuid}@prueba-{test_uuid}.com",
    "whatsapp_number": f"+5199912{current_time % 10000:04d}"
}

TEST_WHATSAPP_MESSAGE = {
    "to": "+51999654321",
    "body": "Hola! Este es un mensaje de prueba desde el sistema N8N."
}

TEST_EMAIL = {
    "to": "test@example.com",
    "subject": "Prueba de email desde N8N",
    "body": "Este es un email de prueba enviado desde el sistema de N8N."
}


class N8NTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.tenant_id = None
    
    def login(self):
        """Autenticarse y obtener token JWT"""
        print("🔐 Autenticando usuario...")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login/",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and 'tokens' in data:
                self.token = data['tokens']['access']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                user_info = data['user']['email'] if 'email' in data['user'] else data['user'].get('username', 'Usuario')
                print(f"✅ Login exitoso. Usuario: {user_info}")
                return True
            else:
                print(f"❌ Error en formato de respuesta: {data}")
                return False
        else:
            print(f"❌ Error en login: {response.status_code} - {response.text}")
            return False
    
    def create_tenant(self):
        """Crear un nuevo tenant"""
        print("🏢 Creando tenant...")
        
        response = self.session.post(
            f"{API_BASE}/tenants/",
            json=TEST_TENANT
        )
        
        if response.status_code == 201:
            data = response.json()
            self.tenant_id = data['tenant_id']
            print(f"✅ Tenant creado: {data['tenant_id']}")
            print(f"   Nombre: {data['data']['name']}")
            print(f"   Dominio: {data['data']['domain']}")
            print(f"   Estado: {data['data']['verification_status']}")
            return True
        else:
            print(f"❌ Error creando tenant: {response.status_code} - {response.text}")
            return False
    
    def get_tenant_details(self):
        """Obtener detalles del tenant"""
        if not self.tenant_id:
            print("❌ No hay tenant_id disponible")
            return False
            
        print("📋 Obteniendo detalles del tenant...")
        
        response = self.session.get(
            f"{API_BASE}/tenants/{self.tenant_id}/"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detalles del tenant:")
            print(f"   ID: {data['tenant_id']}")
            print(f"   Nombre: {data['name']}")
            print(f"   Estado: {data['verification_status']}")
            print(f"   Activo: {data['is_active']}")
            return True
        else:
            print(f"❌ Error obteniendo detalles: {response.status_code} - {response.text}")
            return False
    
    def setup_whatsapp(self):
        """Configurar WhatsApp para el tenant"""
        if not self.tenant_id:
            print("❌ No hay tenant_id disponible")
            return False
            
        print("📱 Configurando WhatsApp...")
        
        response = self.session.post(
            f"{API_BASE}/tenants/{self.tenant_id}/setup-whatsapp/",
            json={"whatsapp_number": TEST_TENANT["whatsapp_number"]}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ WhatsApp configurado: {data['message']}")
            return True
        else:
            print(f"❌ Error configurando WhatsApp: {response.status_code} - {response.text}")
            return False
    
    def send_whatsapp_message(self):
        """Enviar mensaje de WhatsApp"""
        if not self.tenant_id:
            print("❌ No hay tenant_id disponible")
            return False
            
        print("💬 Enviando mensaje de WhatsApp...")
        
        response = self.session.post(
            f"{API_BASE}/tenants/{self.tenant_id}/whatsapp/send/",
            json=TEST_WHATSAPP_MESSAGE
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Mensaje enviado (simulado)")
            print(f"   Log ID: {data.get('log_id')}")
            return True
        else:
            print(f"❌ Error enviando WhatsApp: {response.status_code} - {response.text}")
            return False
    
    def send_email(self):
        """Enviar email"""
        if not self.tenant_id:
            print("❌ No hay tenant_id disponible")
            return False
            
        print("📧 Enviando email...")
        
        response = self.session.post(
            f"{API_BASE}/tenants/{self.tenant_id}/email/send/",
            json=TEST_EMAIL
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email enviado (simulado)")
            print(f"   Log ID: {data.get('log_id')}")
            return True
        else:
            print(f"❌ Error enviando email: {response.status_code} - {response.text}")
            return False
    
    def get_usage_report(self):
        """Obtener reporte de uso"""
        if not self.tenant_id:
            print("❌ No hay tenant_id disponible")
            return False
            
        print("📊 Obteniendo reporte de uso...")
        
        response = self.session.get(
            f"{API_BASE}/tenants/{self.tenant_id}/usage/"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reporte de uso:")
            print(f"   Tenant: {data['tenant_name']}")
            print(f"   Total requests: {data['total_requests']}")
            
            for channel, stats in data['usage_summary'].items():
                print(f"   {channel.upper()}: {stats['total']} total, {stats['success']} éxito, {stats['failed']} fallos")
            
            return True
        else:
            print(f"❌ Error obteniendo reporte: {response.status_code} - {response.text}")
            return False
    
    def get_usage_logs(self):
        """Obtener logs de uso"""
        if not self.tenant_id:
            print("❌ No hay tenant_id disponible")
            return False
            
        print("📜 Obteniendo logs de uso...")
        
        response = self.session.get(
            f"{API_BASE}/tenants/{self.tenant_id}/logs/"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logs encontrados: {len(data['results'])}")
            
            for log in data['results'][:3]:  # Mostrar solo los primeros 3
                print(f"   {log['timestamp']}: {log['channel']} - {log['action']} ({log['status']})")
            
            return True
        else:
            print(f"❌ Error obteniendo logs: {response.status_code} - {response.text}")
            return False
    
    def test_webhook_verification(self):
        """Probar verificación de webhook"""
        print("🔗 Probando verificación de webhook...")
        
        # Probar verificación de webhook de WhatsApp
        response = requests.get(
            f"{API_BASE}/webhook/whatsapp/",
            params={
                'hub.mode': 'subscribe',
                'hub.verify_token': 'mi_webhook_token_secreto',
                'hub.challenge': 'test_challenge'
            }
        )
        
        if response.status_code == 200 and 'test_challenge' in response.text:
            print("✅ Verificación de webhook exitosa")
            return True
        else:
            print(f"❌ Error en verificación de webhook: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Iniciando pruebas del flujo N8N...")
        print("=" * 50)
        
        tests = [
            self.login,
            self.create_tenant,
            self.get_tenant_details,
            self.setup_whatsapp,
            self.send_whatsapp_message,
            self.send_email,
            self.get_usage_report,
            self.get_usage_logs,
            self.test_webhook_verification
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
                print("-" * 30)
            except Exception as e:
                print(f"❌ Error inesperado en {test.__name__}: {str(e)}")
                failed += 1
                print("-" * 30)
        
        print("=" * 50)
        print(f"🎯 Resultados: {passed} exitosas, {failed} fallidas")
        
        if failed == 0:
            print("🎉 ¡Todas las pruebas pasaron!")
            return True
        else:
            print("⚠️  Algunas pruebas fallaron. Revisar la configuración.")
            return False


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Uso: python test_n8n_flow.py [--help]")
            print("Prueba el flujo completo de N8N para onboarding de tenants")
            return
    
    tester = N8NTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
