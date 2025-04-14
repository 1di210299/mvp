import os
import qrcode
from io import BytesIO
import base64
from typing import Dict, Any, Optional
from datetime import datetime
import random
import string
from app.payments.ai_verification import AIPaymentVerifier

class YapePayment:
    """
    Handles Yape payment method
    """
    
    def __init__(self):
        self.yape_phone = os.getenv("YAPE_PHONE_NUMBER")
        self.yape_owner = os.getenv("YAPE_OWNER_NAME", "Tienda Online")
        self.security_code_length = 6
        if not self.yape_phone:
            raise ValueError("Yape phone number is not configured")
        
        try:
            self.ai_verifier = AIPaymentVerifier()
            self.ai_verification_available = True
        except ValueError:
            self.ai_verification_available = False
    
    def generate_reference_code(self, order_id: int) -> str:
        """
        Generates a unique reference code for the customer to include in payment description
        """
        # Generate a random 6-character alphanumeric code
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD{order_id}{random_part}"
    
    def generate_security_code(self) -> str:
        """
        Generates a security code that must appear in the payment screenshot
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=self.security_code_length))
    
    def create_payment_data(self, order_id: int, amount: float) -> dict:
        """
        Creates payment data for Yape
        
        Args:
            order_id: Order ID
            amount: Amount to charge
            
        Returns:
            dict: Payment details including QR and instructions
        """
        reference_code = self.generate_reference_code(order_id)
        security_code = self.generate_security_code()
        
        # Generate Yape payment QR code
        qr_data = f"yape://{self.yape_phone}?amount={amount}&reference={reference_code}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image and convert to base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered)
        qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Return payment details
        return {
            "payment_type": "yape",
            "reference_code": reference_code,
            "security_code": security_code,
            "yape_phone": self.yape_phone,
            "yape_owner": self.yape_owner,
            "amount": amount,
            "qr_code": qr_base64,
            "instructions": f"Escanea el código QR con tu app de Yape o envía {amount} soles al número {self.yape_phone} a nombre de {self.yape_owner}. IMPORTANTE: Incluye el código de referencia {reference_code} en la descripción del pago. Escribe el código de seguridad {security_code} en los detalles del pago. Después, envía una captura de pantalla del pago realizado."
        }
    
    def verify_payment_with_image(self, reference_code: str, image_data: str, 
                                 expected_amount: float) -> Dict[str, Any]:
        """
        Verify a payment using the payment screenshot
        
        Args:
            reference_code: The reference code for the payment
            image_data: Base64 encoded screenshot data
            expected_amount: The expected payment amount
            
        Returns:
            dict: Verification result
        """
        if not self.ai_verification_available:
            return {
                "verified": False,
                "message": "AI verification is not available",
                "requires_manual_verification": True
            }
        
        is_valid, verification_details = self.ai_verifier.verify_payment_image(
            image_data, 
            reference_code, 
            expected_amount
        )
        
        return {
            "verified": is_valid,
            "message": "Payment automatically verified" if is_valid else "Payment verification failed",
            "requires_manual_verification": not is_valid,
            "verification_details": verification_details
        }
