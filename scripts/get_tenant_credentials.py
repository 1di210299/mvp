#!/usr/bin/env python3
"""
Script para obtener el client_secret actual del tenant existente
"""
import requests
import json

# Configuración
BASE_URL = "https://c6dd629ae13d.ngrok-free.app"
TENANT_ID = "f0b2cefd-1814-4d00-90c4-0e40cd283de1"

# Credenciales de usuario
USER_LOGIN = {
    "email": "admin@testcompany.com", 
    "password": "admin123"
}

def get_user_token():
    """Obtener JWT de usuario"""
    print("🔐 Obteniendo token de usuario...")
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=USER_LOGIN)
    
    if response.status_code == 200:
        token = response.json()["tokens"]["access"]
        print("✅ Token obtenido")
        return token
    else:
        print(f"❌ Error: {response.text}")
        return None

def get_tenant_details(user_token):
    """Obtener detalles del tenant"""
    print(f"🏢 Obteniendo detalles del tenant {TENANT_ID}...")
    
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/api/auth/n8n/tenants/{TENANT_ID}/", headers=headers)
    
    if response.status_code == 200:
        tenant_data = response.json()
        print("✅ Tenant encontrado:")
        print(f"📋 ID: {tenant_data.get('id')}")
        print(f"📋 Nombre: {tenant_data.get('name')}")
        print(f"📋 Client Secret: {tenant_data.get('client_secret', 'NO ENCONTRADO')}")
        print(f"📋 Activo: {tenant_data.get('is_active')}")
        return tenant_data
    else:
        print(f"❌ Error: {response.text}")
        return None

def main():
    print("🔍 OBTENIENDO DATOS DEL TENANT EXISTENTE")
    print("=" * 60)
    
    # Paso 1: Obtener token de usuario
    user_token = get_user_token()
    if not user_token:
        return
        
    # Paso 2: Obtener detalles del tenant
    tenant_data = get_tenant_details(user_token)
    
    if tenant_data:
        print("\n🎯 DATOS PARA USAR EN PRUEBAS:")
        print(f"TENANT_ID = \"{tenant_data.get('id')}\"")
        print(f"CLIENT_SECRET = \"{tenant_data.get('client_secret')}\"")

if __name__ == "__main__":
    main()
