#!/usr/bin/env python3
"""
Script que simula el flujo completo de producción:
1. Tu backend autentica como tenant
2. Tu backend obtiene JWT  
3. Tu backend llama al webhook de N8N con el JWT incluido
"""
import requests
import json

# Configuración
BASE_URL = "https://c6dd629ae13d.ngrok-free.app"
N8N_WEBHOOK = "https://juandi210299.app.n8n.cloud/webhook-test/webhook/tenants"

# Credenciales de usuario para crear tenant
USER_LOGIN = {
    "email": "admin@testcompany.com",
    "password": "admin123"
}

def step1_get_user_token():
    """Paso 1: Obtener JWT de usuario para crear tenant"""
    print("🔐 Paso 1: Obteniendo token de usuario...")
    
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=USER_LOGIN)
    
    if response.status_code == 200:
        token = response.json()["tokens"]["access"]
        print("✅ Token de usuario obtenido")
        return token
    else:
        print(f"❌ Error en login: {response.text}")
        return None

def step2_create_tenant(user_token):
    """Paso 2: Crear tenant para obtener client_id y client_secret"""
    print("🏢 Paso 2: Creando tenant...")
    
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    tenant_data = {
        "name": "Empresa N8N Prod Test",
        "domain": "n8nprodtest.com",
        "email_address": "admin@n8nprodtest.com",
        "whatsapp_number": "+51999777888"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/n8n/tenants/", json=tenant_data, headers=headers)
    
    if response.status_code == 201:
        result = response.json()
        tenant_id = result["tenant_id"]
        print(f"✅ Tenant creado: {tenant_id}")
        
        # Activar el tenant para que pueda autenticarse
        activate_response = requests.patch(
            f"{BASE_URL}/api/auth/n8n/tenants/{tenant_id}/",
            json={"is_active": True},
            headers=headers
        )
        
        if activate_response.status_code == 200:
            print("✅ Tenant activado")
        
        return tenant_id
    else:
        print(f"❌ Error creando tenant: {response.text}")
        return None

def step3_get_tenant_config(tenant_id, user_token):
    """Paso 3: Obtener client_secret del tenant"""
    print("🔑 Paso 3: Obteniendo configuración del tenant...")
    
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/api/auth/n8n/tenants/{tenant_id}/", headers=headers)
    
    if response.status_code == 200:
        tenant_data = response.json()
        client_secret = tenant_data.get("client_secret")
        if client_secret:
            print(f"✅ Client secret obtenido: {client_secret[:20]}...")
            return client_secret
        else:
            print("❌ Tenant no tiene client_secret")
            return None
    else:
        print(f"❌ Error obteniendo config: {response.text}")
        return None

def step4_authenticate_as_tenant(tenant_id, client_secret):
    """Paso 4: Autenticarse como tenant para obtener JWT"""
    print("🎯 Paso 4: Autenticando como tenant...")
    
    auth_data = {
        "client_id": tenant_id,
        "client_secret": client_secret
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/tenant-auth/", json=auth_data)
    
    if response.status_code == 200:
        result = response.json()
        access_token = result["access_token"]
        print(f"✅ JWT de tenant obtenido: {access_token[:50]}...")
        print(f"📋 Expira en: {result['expires_in']} segundos")
        return access_token
    else:
        print(f"❌ Error autenticando tenant: {response.text}")
        return None

def step5_call_n8n_webhook(tenant_id, tenant_jwt):
    """Paso 5: Llamar webhook de N8N con JWT incluido"""
    print("🚀 Paso 5: Llamando webhook de N8N...")
    
    webhook_payload = {
        "action": "process_order",
        "orderId": "12345",
        "tenantId": tenant_id,
        "tenantJwt": tenant_jwt,  # ← JWT incluido para N8N
        "customerPhone": "+51999123456",
        "messageBody": "¡Tu pedido #12345 está siendo procesado!",
        "orderDetails": {
            "total": 150.00,
            "items": ["Producto A", "Producto B"],
            "delivery_date": "2025-07-22"
        }
    }
    
    response = requests.post(N8N_WEBHOOK, json=webhook_payload)
    
    if response.status_code == 200:
        print("✅ Webhook N8N llamado exitosamente")
        print(f"📨 Response: {response.text}")
        return True
    else:
        print(f"❌ Error llamando N8N: {response.status_code} - {response.text}")
        return False

def main():
    """Flujo completo de producción"""
    print("🚀 SIMULACIÓN DE FLUJO DE PRODUCCIÓN COMPLETO")
    print("=" * 60)
    
    # Paso 1: Token de usuario
    user_token = step1_get_user_token()
    if not user_token:
        return
    
    print()
    
    # Paso 2: Crear tenant
    tenant_id = step2_create_tenant(user_token)
    if not tenant_id:
        return
    
    print()
    
    # Paso 3: Obtener client_secret
    client_secret = step3_get_tenant_config(tenant_id, user_token)
    if not client_secret:
        return
    
    print()
    
    # Paso 4: Autenticar como tenant
    tenant_jwt = step4_authenticate_as_tenant(tenant_id, client_secret)
    if not tenant_jwt:
        return
    
    print()
    
    # Paso 5: Llamar N8N con JWT
    success = step5_call_n8n_webhook(tenant_id, tenant_jwt)
    
    print()
    print("=" * 60)
    if success:
        print("🎉 ¡FLUJO COMPLETO EXITOSO!")
        print("\n📋 Resumen de credenciales para N8N:")
        print(f"   • Tenant ID: {tenant_id}")
        print(f"   • Client Secret: {client_secret[:20]}...")
        print(f"   • JWT Token: {tenant_jwt[:50]}...")
        
        print("\n🎯 En N8N, tu nodo 'Get Config' debe usar:")
        print(f"   Authorization: Bearer {{{{ $node['Webhook'].json['body']['tenantJwt'] }}}}")
        print(f"   URL: {BASE_URL}/api/auth/n8n/tenants/{tenant_id}/")
        
    else:
        print("❌ FLUJO FALLÓ")

if __name__ == "__main__":
    main()
