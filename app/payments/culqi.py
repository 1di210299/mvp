import os
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime

class CulqiGateway:
    """
    Culqi payment gateway integration
    """
    BASE_URL = "https://api.culqi.com/v2"
    
    def __init__(self):
        self.public_key = os.getenv("CULQI_PUBLIC_KEY")
        self.private_key = os.getenv("CULQI_PRIVATE_KEY")
        if not self.public_key or not self.private_key:
            raise ValueError("Culqi API keys are missing")
            
    def create_payment_link(self, order_id: int, amount: float, 
                           customer_email: str, description: str) -> dict:
        """
        Creates a payment link for an order
        
        Args:
            order_id: The order ID
            amount: Amount to charge (in PEN cents - multiply by 100)
            customer_email: Customer's email
            description: Order description
            
        Returns:
            dict: Response with payment link details
        """
        url = f"{self.BASE_URL}/orders"
        headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": int(amount * 100),  # Convert to cents
            "currency_code": "PEN",
            "description": description,
            "order_number": f"order-{order_id}",
            "client_details": {
                "email": customer_email
            },
            "expiration_date": int((datetime.now().timestamp() + 24*60*60) * 1000),  # 24 hours from now
            "confirm": False
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            raise Exception(f"Error creating Culqi link: {response.text}")
            
        return response.json()
    
    def verify_payment(self, payment_id: str) -> dict:
        """
        Verify a payment status
        
        Args:
            payment_id: The payment ID from Culqi
            
        Returns:
            dict: Payment details response
        """
        url = f"{self.BASE_URL}/charges/{payment_id}"
        headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error verifying payment: {response.text}")
            
        return response.json()
