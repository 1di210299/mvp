import os
import base64
from typing import Dict, Any, Optional, Tuple
import openai
from PIL import Image
import io
import re

class AIPaymentVerifier:
    """
    Uses OpenAI's vision capabilities to verify payment screenshots
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")
        
        openai.api_key = self.api_key
        self.company_name = os.getenv("COMPANY_NAME", "Mi Tienda")
    
    def verify_payment_image(self, image_data: str, reference_code: str, 
                            expected_amount: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies a payment using OpenAI vision to extract info from screenshots
        
        Args:
            image_data: Base64 encoded image
            reference_code: Expected reference code in the payment
            expected_amount: Expected payment amount
            
        Returns:
            Tuple containing:
                - Boolean indicating if payment is valid
                - Dictionary with extracted information and verification details
        """
        try:
            # Prepare the image data for the API
            if image_data.startswith("data:image"):
                # Extract the base64 part if it's a data URL
                image_data = image_data.split(",")[1]
            
            # Call OpenAI API with the image
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a payment verification assistant. Analyze the payment screenshot and extract these details: 1) Payment amount, 2) Recipient name/company, 3) Any reference code or transaction ID, 4) Date and time, 5) Payment status (successful, pending, failed). Specifically check if the payment was made to {self.company_name} and if reference code {reference_code} appears in the image."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Verify this payment screenshot and extract all relevant information:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Extract the analysis from the response
            analysis = response.choices[0].message.content
            
            # Parse the analysis to extract key information
            extracted_info = self._parse_analysis(analysis)
            
            # Verify if the payment is valid based on extracted info
            is_valid = self._validate_payment(
                extracted_info, 
                reference_code, 
                expected_amount
            )
            
            return is_valid, {
                "extracted_info": extracted_info,
                "raw_analysis": analysis,
                "verification_result": "verified" if is_valid else "failed",
                "verification_method": "ai"
            }
            
        except Exception as e:
            return False, {
                "error": str(e),
                "verification_result": "error",
                "verification_method": "ai"
            }
    
    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        """
        Parse the text analysis to extract structured information
        """
        result = {
            "amount": None,
            "recipient": None,
            "reference_code": None,
            "date": None,
            "status": None,
            "security_code": None
        }
        
        # Extract amount
        amount_match = re.search(r"(?:amount|monto|suma)(?:[:\s]+)(?:S\/\.|\$|PEN|USD)?[^\d]*([\d.,]+)", 
                                analysis, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '.')
            try:
                result["amount"] = float(amount_str)
            except ValueError:
                pass
        
        # Extract recipient
        recipient_match = re.search(r"(?:recipient|destinatario|beneficiario|company|empresa)(?:[:\s]+)([^\n\r.]+)", 
                                  analysis, re.IGNORECASE)
        if recipient_match:
            result["recipient"] = recipient_match.group(1).strip()
        
        # Extract reference code
        ref_match = re.search(r"(?:reference|referencia|código|code|ID)(?:[:\s]+)([A-Z0-9]+)", 
                            analysis, re.IGNORECASE)
        if ref_match:
            result["reference_code"] = ref_match.group(1).strip()
        
        # Extract security code if present
        security_match = re.search(r"(?:security code|código de seguridad|verificación)(?:[:\s]+)([A-Z0-9]+)", 
                                 analysis, re.IGNORECASE)
        if security_match:
            result["security_code"] = security_match.group(1).strip()
        
        # Extract status
        if re.search(r"(?:successful|exitoso|completado|approved|aprobado)", analysis, re.IGNORECASE):
            result["status"] = "successful"
        elif re.search(r"(?:pending|pendiente|en proceso)", analysis, re.IGNORECASE):
            result["status"] = "pending"
        elif re.search(r"(?:failed|fallido|rechazado|declined)", analysis, re.IGNORECASE):
            result["status"] = "failed"
        
        return result
    
    def _validate_payment(self, extracted_info: Dict[str, Any], 
                         expected_reference: str, expected_amount: float) -> bool:
        """
        Validate if the extracted payment information matches expected values
        """
        # Check if payment was successful
        if extracted_info.get("status") != "successful":
            return False
        
        # Check if the company name appears in the recipient field
        recipient = extracted_info.get("recipient", "")
        if not recipient or self.company_name.lower() not in recipient.lower():
            return False
        
        # Check reference code
        reference = extracted_info.get("reference_code")
        if not reference or expected_reference not in reference:
            return False
        
        # Check amount with some tolerance for parsing errors
        amount = extracted_info.get("amount")
        if not amount or abs(amount - expected_amount) > 0.1:  # Allow 0.1 tolerance
            return False
        
        return True
