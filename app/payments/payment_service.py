from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.models import Order, PaymentMethod, OrderStatus, PaymentStatus
from app.payments.culqi import CulqiGateway
from app.payments.yape import YapePayment

class PaymentService:
    """
    Service to handle payment operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.culqi = CulqiGateway()
        self.yape = YapePayment()
    
    def create_payment_link(self, order_id: int) -> Dict[str, Any]:
        """
        Creates a payment link based on the selected payment method
        
        Args:
            order_id: The order ID
            
        Returns:
            dict: Payment link details
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        customer = order.customer
        
        if not order.payment_method:
            raise ValueError("Payment method not set for this order")
        
        result = {}
        
        if order.payment_method == PaymentMethod.CULQI:
            # Create Culqi payment link
            if not customer.email:
                raise ValueError("Customer email is required for Culqi payments")
                
            culqi_response = self.culqi.create_payment_link(
                order_id=order.id,
                amount=order.total_amount,
                customer_email=customer.email,
                description=f"Pedido #{order.id}"
            )
            
            order.payment_link = culqi_response.get('payment_link', '')
            order.payment_id = culqi_response.get('id', '')
            order.status = OrderStatus.PAYMENT_LINK_SENT
            order.payment_status = PaymentStatus.INITIATED
            order.payment_details = culqi_response
            result = {
                "payment_type": "culqi",
                "payment_link": order.payment_link,
                "payment_id": order.payment_id
            }
            
        elif order.payment_method == PaymentMethod.YAPE:
            # Create Yape payment data
            yape_data = self.yape.create_payment_data(
                order_id=order.id,
                amount=order.total_amount
            )
            
            order.payment_status = PaymentStatus.INITIATED
            order.status = OrderStatus.PAYMENT_LINK_SENT
            order.payment_details = yape_data
            order.payment_id = yape_data.get('reference_code')
            result = yape_data
            
        # Update order in database
        self.db.commit()
        
        return result
    
    def process_payment_confirmation(self, payment_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment confirmation from webhook or manual verification
        
        Args:
            payment_id: The payment ID
            payment_data: Payment confirmation data
            
        Returns:
            dict: Result of the payment processing
        """
        # Find the order by payment_id
        order = self.db.query(Order).filter(Order.payment_id == payment_id).first()
        
        if not order:
            raise ValueError(f"Order with payment ID {payment_id} not found")
            
        # Update the order status
        order.payment_status = PaymentStatus.COMPLETED
        order.status = OrderStatus.PAID
        order.payment_date = datetime.utcnow()
        order.payment_details = {**order.payment_details, "confirmation": payment_data} if order.payment_details else {"confirmation": payment_data}
        
        self.db.commit()
        
        return {
            "order_id": order.id,
            "status": "success",
            "message": "Payment completed successfully"
        }
    
    def register_yape_manual_payment(self, reference_code: str, verified: bool = True) -> Dict[str, Any]:
        """
        Register a manual Yape payment verification
        
        Args:
            reference_code: The Yape reference code
            verified: Whether the payment was verified
            
        Returns:
            dict: Result of the payment processing
        """
        order = self.db.query(Order).filter(Order.payment_id == reference_code).first()
        
        if not order:
            raise ValueError(f"Order with reference code {reference_code} not found")
        
        if verified:
            order.payment_status = PaymentStatus.COMPLETED
            order.status = OrderStatus.PAID
            order.payment_date = datetime.utcnow()
            
            if order.payment_details:
                order.payment_details["manually_verified"] = True
                order.payment_details["verification_date"] = datetime.utcnow().isoformat()
            else:
                order.payment_details = {
                    "manually_verified": True,
                    "verification_date": datetime.utcnow().isoformat()
                }
            
            self.db.commit()
            
            return {
                "order_id": order.id,
                "status": "success",
                "message": "Yape payment manually verified"
            }
        else:
            return {
                "order_id": order.id,
                "status": "error",
                "message": "Payment verification failed"
            }
    
    def verify_yape_payment_with_image(self, order_id: int, image_data: str) -> Dict[str, Any]:
        """
        Verifies a Yape payment using an image
        
        Args:
            order_id: The order ID
            image_data: Base64 encoded image data
            
        Returns:
            dict: Verification result
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order.payment_method != PaymentMethod.YAPE:
            raise ValueError("This order is not configured for Yape payment")
        
        if not order.payment_details or not order.payment_id:
            raise ValueError("Order payment details are incomplete")
        
        reference_code = order.payment_id
        expected_amount = order.total_amount
        
        # Verify the payment using the image
        verification_result = self.yape.verify_payment_with_image(
            reference_code, 
            image_data, 
            expected_amount
        )
        
        # Update order with verification details
        if verification_result.get("verified", False):
            order.payment_status = PaymentStatus.COMPLETED
            order.status = OrderStatus.PAID
            order.payment_date = datetime.utcnow()
        
        # Add verification attempt to payment details
        if order.payment_details:
            order.payment_details["verification_attempts"] = order.payment_details.get("verification_attempts", []) + [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": verification_result,
                    "method": "image_ai"
                }
            ]
        else:
            order.payment_details = {
                "verification_attempts": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "result": verification_result,
                        "method": "image_ai"
                    }
                ]
            }
        
        self.db.commit()
        
        return {
            "order_id": order.id,
            "verification_result": verification_result,
            "status": "success" if verification_result.get("verified", False) else "pending",
            "message": "Payment verified" if verification_result.get("verified", False) else "Payment requires manual verification"
        }
