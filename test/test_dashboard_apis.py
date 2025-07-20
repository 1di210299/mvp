#!/usr/bin/env python3
"""
Script para probar las APIs del Dashboard
"""
import requests
import json
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://localhost:8080"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"

# Credenciales de prueba (ajustar según tu configuración)
TEST_EMAIL = "admin@testcompany.com"
TEST_PASSWORD = "admin123"

class DashboardAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def login(self):
        """Autenticarse en el sistema"""
        print("🔐 Iniciando sesión...")
        
        response = self.session.post(LOGIN_URL, json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            # Extraer el token del objeto tokens
            tokens = data.get('tokens', {})
            self.token = tokens.get('access')
            
            if self.token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print("✅ Login exitoso")
                return True
            else:
                print("❌ Error: No se encontró el token de acceso")
                print(f"Respuesta: {data}")
                return False
        else:
            print(f"❌ Error en login: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
    
    def test_dashboard_overview(self):
        """Probar endpoint de resumen general"""
        print("\n📊 Probando Dashboard Overview...")
        
        url = f"{BASE_URL}/api/inventory/dashboards/dashboard/overview/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Dashboard Overview OK")
            print(f"   📋 Purchase Orders: {data['metrics']['total_purchase_orders']}")
            print(f"   🏢 Suppliers: {data['metrics']['total_suppliers']}")
            print(f"   📧 Emails Tracked: {data['metrics']['total_emails_tracked']}")
            print(f"   📈 Active Campaigns: {data['metrics']['active_campaigns']}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
    
    def test_purchase_orders_dashboard(self):
        """Probar Purchase Orders Dashboard"""
        print("\n📋 Probando Purchase Orders Dashboard...")
        
        # Test overview
        url = f"{BASE_URL}/api/inventory/dashboards/purchase-orders-dashboard/overview/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PO Dashboard Overview OK")
            print(f"   📦 Total Orders: {data['metrics']['total_orders']}")
            print(f"   ⏳ Pending: {data['metrics']['pending_orders']}")
            print(f"   ✅ Confirmed: {data['metrics']['confirmed_orders']}")
            print(f"   💰 Total Value: ${data['metrics']['total_value']:.2f}")
        else:
            print(f"❌ Error en PO Overview: {response.status_code}")
            return False
        
        # Test orders list
        url = f"{BASE_URL}/api/inventory/dashboards/purchase-orders-dashboard/orders_list/"
        print(f"🔍 Probando URL: {url}")
        response = self.session.get(url, params={'page': 1, 'page_size': 5})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PO Orders List OK - {len(data['orders'])} orders")
            print(f"   📄 Page: {data['pagination']['page']}/{data['pagination']['total_pages']}")
        else:
            print(f"❌ Error en PO Orders List: {response.status_code}")
            print(f"   🔗 URL intentada: {url}")
            print(f"   📋 Headers enviados: {dict(self.session.headers)}")
            print(f"   📄 Respuesta completa: {response.text[:500]}...")
            return False
        
        # Test suppliers list
        url = f"{BASE_URL}/api/inventory/dashboards/purchase-orders-dashboard/suppliers_list/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Suppliers List OK - {len(data['suppliers'])} suppliers")
        else:
            print(f"❌ Error en Suppliers List: {response.status_code}")
            return False
        
        return True
    
    def test_email_tracking_dashboard(self):
        """Probar Email Tracking Dashboard"""
        print("\n📧 Probando Email Tracking Dashboard...")
        
        # Test overview
        url = f"{BASE_URL}/api/inventory/dashboards/email-tracking-dashboard/overview/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Email Tracking Overview OK")
            print(f"   📨 Total Sent: {data['metrics']['total_sent']}")
            print(f"   👀 Open Rate: {data['metrics']['open_rate']}%")
            print(f"   🖱️ Click Rate: {data['metrics']['click_rate']}%")
            print(f"   💬 Reply Rate: {data['metrics']['reply_rate']}%")
            print(f"   🎯 Engagement Score: {data['metrics']['engagement_score']}")
        else:
            print(f"❌ Error en Email Tracking Overview: {response.status_code}")
            return False
        
        # Test daily performance
        url = f"{BASE_URL}/api/inventory/dashboards/email-tracking-dashboard/daily_performance/"
        print(f"🔍 Probando URL: {url}")
        response = self.session.get(url, params={'days': 7})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Daily Performance OK - {len(data['daily_performance'])} days")
        else:
            print(f"❌ Error en Daily Performance: {response.status_code}")
            print(f"   🔗 URL intentada: {url}")
            print(f"   📋 Headers enviados: {dict(self.session.headers)}")
            print(f"   📄 Respuesta completa: {response.text[:500]}...")
            return False
        
        # Test emails list
        url = f"{BASE_URL}/api/inventory/dashboards/email-tracking-dashboard/emails_list/"
        response = self.session.get(url, params={'page': 1, 'page_size': 5})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Emails List OK - {len(data['emails'])} emails")
        else:
            print(f"❌ Error en Emails List: {response.status_code}")
            return False
        
        # Test campaigns list
        url = f"{BASE_URL}/api/inventory/dashboards/email-tracking-dashboard/campaigns_list/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Campaigns List OK - {len(data['campaigns'])} campaigns")
        else:
            print(f"❌ Error en Campaigns List: {response.status_code}")
            return False
        
        return True
    
    def test_activity_chart(self):
        """Probar datos para gráfico de actividad"""
        print("\n📈 Probando Activity Chart...")
        
        url = f"{BASE_URL}/api/inventory/dashboards/dashboard/activity_chart/"
        print(f"🔍 Probando URL: {url}")
        response = self.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Activity Chart OK")
            print(f"   📅 Days: {len(data['data'])}")
            print(f"   🏷️ Labels: {data['labels']}")
        else:
            print(f"❌ Error en Activity Chart: {response.status_code}")
            print(f"   🔗 URL intentada: {url}")
            print(f"   📋 Headers enviados: {dict(self.session.headers)}")
            print(f"   📄 Respuesta completa: {response.text[:500]}...")
            return False
        
        return True
    
    def test_filters(self):
        """Probar filtros en los dashboards"""
        print("\n🔍 Probando filtros...")
        
        # Filtros de fecha
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/api/inventory/dashboards/purchase-orders-dashboard/overview/"
        response = self.session.get(url, params={
            'date_from': date_from,
            'date_to': date_to,
            'status': 'pending'
        })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Filtros PO OK")
            print(f"   🗓️ Periodo: {data['filters_applied']['date_from']} - {data['filters_applied']['date_to']}")
            print(f"   📊 Status: {data['filters_applied']['status']}")
        else:
            print(f"❌ Error en filtros PO: {response.status_code}")
            return False
        
        # Filtros email tracking
        url = f"{BASE_URL}/api/inventory/dashboards/email-tracking-dashboard/overview/"
        response = self.session.get(url, params={
            'date_from': date_from,
            'date_to': date_to,
            'status': 'opened'
        })
        
        if response.status_code == 200:
            print("✅ Filtros Email Tracking OK")
        else:
            print(f"❌ Error en filtros Email Tracking: {response.status_code}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Iniciando pruebas de Dashboard APIs...")
        print("=" * 50)
        
        if not self.login():
            print("❌ No se pudo autenticar. Verificar credenciales.")
            return False
        
        tests = [
            self.test_dashboard_overview,
            self.test_purchase_orders_dashboard,
            self.test_email_tracking_dashboard,
            self.test_activity_chart,
            self.test_filters,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Error en {test.__name__}: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 RESULTADOS: {passed} ✅ | {failed} ❌")
        
        if failed == 0:
            print("🎉 ¡Todas las APIs funcionan correctamente!")
        else:
            print("⚠️ Algunos endpoints necesitan revisión.")
        
        return failed == 0


if __name__ == "__main__":
    print("🧪 Dashboard API Test Suite")
    print("Asegúrate de que el servidor Django esté corriendo en localhost:8080")
    print()
    
    # Permitir configurar credenciales
    import sys
    if len(sys.argv) >= 3:
        TEST_EMAIL = sys.argv[1]
        TEST_PASSWORD = sys.argv[2]
        print(f"🔧 Usando credenciales: {TEST_EMAIL}")
    else:
        print(f"🔧 Usando credenciales por defecto: {TEST_EMAIL}")
        print("   Uso: python test_dashboard_apis.py <email> <password>")
    
    print()
    
    tester = DashboardAPITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
