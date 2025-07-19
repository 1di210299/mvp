#!/usr/bin/env python3
"""
Test para diagnosticar el error 405 en /api/inventory/products/actions/
"""
import requests
import json

# Configuración
BASE_URL = "http://localhost:8080/api"
LOGIN_URL = f"{BASE_URL}/auth/login/"
PRODUCTS_ACTIONS_URL = f"{BASE_URL}/inventory/products/actions/"

def test_endpoint_405():
    print("🧪 Diagnóstico del error 405 en ProductActionView")
    print("=" * 60)
    
    # Paso 1: Login para obtener token
    print("1. 🔐 Obteniendo token de autenticación...")
    login_data = {
        "email": "admin@sanmartin.com.pe",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(LOGIN_URL, json=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json()['tokens']['access']
            print("   ✅ Token obtenido exitosamente")
        else:
            print(f"   ❌ Error en login: {login_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error conectando a login: {e}")
        return
    
    # Paso 2: Verificar endpoint con diferentes métodos
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n2. 🔍 Probando diferentes métodos HTTP...")
    
    # Test GET (no debería estar permitido)
    try:
        get_response = requests.get(PRODUCTS_ACTIONS_URL, headers=headers)
        print(f"   GET: {get_response.status_code} - {get_response.text[:100]}")
    except Exception as e:
        print(f"   GET: Error - {e}")
    
    # Test OPTIONS (para ver métodos permitidos)
    try:
        options_response = requests.options(PRODUCTS_ACTIONS_URL, headers=headers)
        print(f"   OPTIONS: {options_response.status_code}")
        if 'Allow' in options_response.headers:
            print(f"   Métodos permitidos: {options_response.headers['Allow']}")
    except Exception as e:
        print(f"   OPTIONS: Error - {e}")
    
    # Test POST (el que debería funcionar)
    test_data = {
        "product_id": 136,  # ID del producto del error original
        "action": "generate_purchase_order",
        "data": {}
    }
    
    print(f"\n3. 📤 Probando POST con datos: {test_data}")
    
    try:
        post_response = requests.post(PRODUCTS_ACTIONS_URL, json=test_data, headers=headers)
        print(f"   POST status: {post_response.status_code}")
        print(f"   Response headers: {dict(post_response.headers)}")
        print(f"   Response body: {post_response.text[:500]}")
        
        if post_response.status_code == 405:
            print("\n🔍 DIAGNÓSTICO DEL ERROR 405:")
            print("   - El endpoint existe pero no acepta POST")
            print("   - Posibles causas:")
            print("     1. Error en la definición de la clase")
            print("     2. Problema de importaciones")
            print("     3. Error en la configuración de URLs")
            print("     4. Problema en la herencia de APIView")
            
    except Exception as e:
        print(f"   POST: Error de conexión - {e}")
    
    # Paso 4: Verificar endpoint de productos normal
    print("\n4. ✅ Verificando endpoint de productos (control)...")
    products_url = f"{BASE_URL}/inventory/products/"
    
    try:
        products_response = requests.get(products_url, headers=headers)
        print(f"   GET products: {products_response.status_code}")
        if products_response.status_code == 200:
            products_data = products_response.json()
            print(f"   ✅ Productos disponibles: {len(products_data.get('results', []))}")
        else:
            print(f"   ❌ Error: {products_response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Diagnóstico completado")

if __name__ == "__main__":
    test_endpoint_405() 