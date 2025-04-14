from fastapi import APIRouter, Depends, HTTPException, Request, Response, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.payments.payment_service import PaymentService

router = APIRouter()

@router.post("/webhooks/culqi", status_code=200)
async def culqi_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for Culqi payment confirmations
    """
    # Get the raw request body
    payload = await request.json()
    
    # Validate the webhook signature (in a real implementation)
    # This would involve checking headers and validating the signature
    
    # Extract data from the webhook payload
    event_type = payload.get("type")
    
    if event_type != "order.paid":
        # Only process successful payments
        return {"status": "ignored", "message": "Event type not relevant"}
    
    data = payload.get("data", {})
    payment_id = data.get("id")
    
    if not payment_id:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    
    # Process the payment confirmation
    payment_service = PaymentService(db)
    try:
        result = payment_service.process_payment_confirmation(payment_id, data)
        return {"status": "success", "message": "Payment processed", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/webhooks/yape/verify", status_code=200)
async def verify_yape_payment(
    reference_code: str = Body(..., embed=True),
    verified: bool = Body(True, embed=True),
    db: Session = Depends(get_db)
):
    """
    Endpoint for manual verification of Yape payments
    """
    payment_service = PaymentService(db)
    try:
        result = payment_service.register_yape_manual_payment(reference_code, verified)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhooks/yape/verify-image", status_code=200)
async def verify_yape_payment_with_image(
    order_id: int = Body(...),
    image_data: str = Body(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint for verifying Yape payments using a screenshot image
    """
    payment_service = PaymentService(db)
    
    try:
        # Verify the payment using the provided image
        result = payment_service.verify_yape_payment_with_image(order_id, image_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
