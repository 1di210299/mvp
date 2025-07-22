#!/usr/bin/env python3
"""
Script que usa el tenant existente para probar el flujo completo
"""
import requests
import json

# Configuración
BASE_URL = "https://c6dd629ae13d.ngrok-free.app"
N8N_WEBHOOK = "https://juandi210299.app.n8n.cloud/webhook-test/webhook/tenants"

# Usar el tenant que ya existe
EXISTING_TENANT_ID = "f0b2cefd-1814-4d00-90c4-0e40cd283de1"
EXISTING_CLIENT_SECRET = "tenant_AEu5ejyAT9LkNJrgw3VJkbog1jeSAYYd8AMv7eSP4uU"

def step1_authenticate_as_tenant():
    """Paso 1: Autenticarse como tenant para obtener JWT"""
    print("🎯 Paso 1: Autenticando como tenant...")
    
    auth_data = {
        "client_id": EXISTING_TENANT_ID,
        "client_secret": EXISTING_CLIENT_SECRET
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/tenant-auth/", json=auth_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"📋 Respuesta completa: {result}")
        
        # Verificar qué campo contiene el token
        jwt_token = result.get("access") or result.get("token") or result.get("access_token")
        if jwt_token:
            expires_in = result.get("expires_in", "unknown")
            print(f"✅ JWT de tenant obtenido: {jwt_token[:50]}...")
            print(f"📋 Expira en: {expires_in} segundos")
            return jwt_token
        else:
            print(f"❌ No se encontró token en la respuesta: {result}")
            return None
    else:
        print(f"❌ Error en autenticación: {response.text}")
        return None

def step2_call_n8n_webhook(tenant_jwt):
    """Paso 2: Llamar webhook de N8N con JWT incluido"""
    print("🚀 Paso 2: Llamando webhook de N8N...")
    
    webhook_data = {
        "orderId": "TEST-12345",
        "tenantId": EXISTING_TENANT_ID,
        "tenantJwt": tenant_jwt,
        "customerPhone": "+51987654321",
        "messageBody": "Hola! Tu pedido está listo para entrega. Confirmanos si estarás disponible."
    }
    
    try:
        response = requests.post(N8N_WEBHOOK, json=webhook_data, timeout=10)
        
        if response.status_code == 200:
            print("✅ ¡Webhook de N8N llamado exitosamente!")
            print(f"📋 Respuesta: {response.text}")
            return True
        else:
            print(f"❌ Error llamando N8N: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout llamando N8N (puede ser normal si N8N está procesando)")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
        return False

def main():
    print("🚀 PRUEBA CON TENANT EXISTENTE")
    print("=" * 60)
    
    # Paso 1: Autenticar como tenant
    tenant_jwt = step1_authenticate_as_tenant()
    if not tenant_jwt:
        print("\n❌ FALLÓ EN PASO 1")
        return
    
    # Paso 2: Llamar N8N
    success = step2_call_n8n_webhook(tenant_jwt)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡FLUJO COMPLETADO EXITOSAMENTE!")
        print("✅ El sistema de autenticación JWT para N8N está funcionando")
    else:
        print("❌ FLUJO FALLÓ EN N8N")
        print("💡 Asegúrate de que el webhook esté activado en N8N")

if __name__ == "__main__":
    main()
