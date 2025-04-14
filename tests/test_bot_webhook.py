#!/usr/bin/env python
import sys
import os
import json
import requests
from typing import Dict, Any

# Añadir la ruta del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Realizar un test directo al webhook usando requests
def test_with_requests():
    """Prueba el webhook directamente usando requests."""
    base_url = "http://localhost:8000"
    webhook_url = f"{base_url}/api/webhooks/twilio"
    
    # Simular datos del formulario que Twilio enviaría
    form_data = {
        "From": "whatsapp:+51999999999",
        "To": "whatsapp:+14155238886",
        "Body": "Hola, quiero comprar algo",
        "AccountSid": os.getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    }
    
    # Realizar la petición POST
    response = requests.post(webhook_url, data=form_data)
    
    # Mostrar la respuesta
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

# Para pruebas con la API directamente
def test_conversation_flow():
    """Prueba un flujo de conversación completo simulando varios mensajes."""
    base_url = "http://localhost:8000"
    webhook_url = f"{base_url}/api/webhooks/twilio"
    phone_number = "whatsapp:+51999999999"
    
    # Lista de mensajes para simular un flujo completo
    messages = [
        "Hola",                                    # Saludo inicial
        "Sí",                                      # Aceptar consentimiento
        "Me llamo Juan Pérez, DNI 12345678",       # Proporcionar datos
        "Quiero ver los productos",                # Ver menú
        "A01",                                     # Añadir producto
        "B02",                                     # Añadir otro producto
        "Ver carrito",                             # Ver el carrito
        "Sí, confirmar"                            # Confirmar pedido
    ]
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    
    # Enviar cada mensaje y mostrar la respuesta
    for message in messages:
        form_data = {
            "From": phone_number,
            "To": "whatsapp:+14155238886",
            "Body": message,
            "AccountSid": account_sid
        }
        
        print(f"\n--- Enviando: '{message}' ---")
        response = requests.post(webhook_url, data=form_data)
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
        
        # Pausa para revisar la respuesta
        input("Presiona Enter para continuar al siguiente mensaje...")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prueba el bot de WhatsApp")
    parser.add_argument("--flow", action="store_true", help="Ejecutar un flujo completo de conversación")
    parser.add_argument("--message", type=str, help="Enviar un mensaje específico")
    
    args = parser.parse_args()
    
    if args.flow:
        test_conversation_flow()
    elif args.message:
        # Configurar la prueba para un mensaje específico
        base_url = "http://localhost:8000"
        webhook_url = f"{base_url}/api/webhooks/twilio"
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        
        form_data = {
            "From": "whatsapp:+51999999999",
            "To": "whatsapp:+14155238886",
            "Body": args.message,
            "AccountSid": account_sid
        }
        
        response = requests.post(webhook_url, data=form_data)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
    else:
        # Prueba simple
        test_with_requests()