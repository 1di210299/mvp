#!/usr/bin/env python3
"""
Script para crear un tenant de prueba y obtener su UUID
para testing de N8N
"""
import requests
import json

# Configuración
BASE_URL = "https://c6dd629ae13d.ngrok-free.app"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
CREATE_TENANT_URL = f"{BASE_URL}/api/auth/n8n/tenants/"

# Datos de login (ajusta según tu usuario)
login_data = {
    "email": "admin@testcompany.com",
    "password": "admin123"
}

# Datos del tenant de prueba
tenant_data = {
    "name": "Empresa N8N Test",
    "domain": "n8ntest.com", 
    "email_address": "admin@n8ntest.com",
    "whatsapp_number": "+51999888777"
}

def main():
    try:
        # 1. Login para obtener token
        print("🔐 Obteniendo token de autenticación...")
        response = requests.post(LOGIN_URL, json=login_data)
        
        if response.status_code == 200:
            token = response.json()["access"]
            print(f"✅ Token obtenido")
        else:
            print(f"❌ Error en login: {response.text}")
            return
        
        # 2. Crear tenant
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("🏢 Creando tenant de prueba...")
        response = requests.post(CREATE_TENANT_URL, json=tenant_data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            tenant_id = result["tenant_id"]
            print(f"✅ Tenant creado exitosamente!")
            print(f"📋 Tenant ID: {tenant_id}")
            print(f"📋 Nombre: {result['data']['name']}")
            print(f"📋 Dominio: {result['data']['domain']}")
            print(f"📋 Email: {result['data']['email_address']}")
            
            # 3. Generar URL para N8N
            get_config_url = f"{BASE_URL}/api/auth/n8n/tenants/{tenant_id}/"
            print(f"\n🎯 URL para tu nodo 'Get Config' en N8N:")
            print(f"{get_config_url}")
            
            # 4. Generar JSON para webhook de prueba
            webhook_test_data = {
                "tenantId": tenant_id,
                "name": tenant_data["name"],
                "domain": tenant_data["domain"],
                "email": tenant_data["email_address"]
            }
            
            print(f"\n📨 JSON de prueba para tu webhook:")
            print(json.dumps(webhook_test_data, indent=2))
            
        else:
            print(f"❌ Error creando tenant: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
