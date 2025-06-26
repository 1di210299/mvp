from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import uuid

from database import get_db
from schemas import PaymentCreate, PaymentResponse
from models import Payment as PaymentModel, User as UserModel
from routers.auth import get_current_user

router = APIRouter()

# Precios en soles peruanos
SUBSCRIPTION_PRICES = {
    "monthly": 29.90,
    "yearly": 299.90,
    "one-time": 9.90
}

@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo pago (simulado o real)"""
    
    if payment_data.subscription_type not in SUBSCRIPTION_PRICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de suscripción inválido"
        )
    
    amount = SUBSCRIPTION_PRICES[payment_data.subscription_type]
    
    # Calcular fecha de expiración
    expires_at = None
    if payment_data.subscription_type == "monthly":
        expires_at = datetime.utcnow() + timedelta(days=30)
    elif payment_data.subscription_type == "yearly":
        expires_at = datetime.utcnow() + timedelta(days=365)
    elif payment_data.subscription_type == "one-time":
        expires_at = datetime.utcnow() + timedelta(days=7)  # Acceso por 7 días
    
    # Crear registro de pago
    db_payment = PaymentModel(
        user_id=current_user.id,
        amount=amount,
        currency="PEN",
        status="pending",
        payment_method=payment_data.payment_method,
        transaction_id=str(uuid.uuid4()),
        subscription_type=payment_data.subscription_type,
        expires_at=expires_at
    )
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Si es simulado, completar automáticamente
    if payment_data.payment_method == "simulation":
        db_payment.status = "completed"
        current_user.is_premium = True
        db.commit()
    
    return db_payment

@router.post("/simulate-success/{payment_id}")
async def simulate_payment_success(
    payment_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simular éxito de pago (para desarrollo)"""
    
    payment = db.query(PaymentModel).filter(
        PaymentModel.id == payment_id,
        PaymentModel.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    payment.status = "completed"
    current_user.is_premium = True
    db.commit()
    
    return {"message": "Pago simulado exitosamente - Usuario actualizado a premium"}

@router.post("/webhook/stripe")
async def stripe_webhook():
    """Webhook de Stripe (placeholder para integración futura)"""
    # TODO: Implementar webhook real de Stripe
    return {"message": "Webhook de Stripe recibido"}

@router.post("/webhook/culqi")
async def culqi_webhook():
    """Webhook de Culqi (placeholder para integración futura)"""
    # TODO: Implementar webhook real de Culqi
    return {"message": "Webhook de Culqi recibido"}

@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener historial de pagos del usuario"""
    payments = db.query(PaymentModel).filter(
        PaymentModel.user_id == current_user.id
    ).order_by(PaymentModel.created_at.desc()).all()
    return payments

@router.get("/subscription-status")
async def get_subscription_status(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estado de suscripción del usuario"""
    
    # Obtener el último pago completado
    latest_payment = db.query(PaymentModel).filter(
        PaymentModel.user_id == current_user.id,
        PaymentModel.status == "completed"
    ).order_by(PaymentModel.created_at.desc()).first()
    
    is_active = False
    expires_at = None
    subscription_type = None
    
    if latest_payment and latest_payment.expires_at:
        is_active = datetime.utcnow() < latest_payment.expires_at
        expires_at = latest_payment.expires_at
        subscription_type = latest_payment.subscription_type
        
        # Actualizar estado premium del usuario si ha expirado
        if not is_active and current_user.is_premium:
            current_user.is_premium = False
            db.commit()
    
    return {
        "is_premium": current_user.is_premium,
        "subscription_active": is_active,
        "subscription_type": subscription_type,
        "expires_at": expires_at,
        "available_plans": {
            "monthly": {
                "price": SUBSCRIPTION_PRICES["monthly"],
                "currency": "PEN",
                "description": "Acceso completo por 30 días"
            },
            "yearly": {
                "price": SUBSCRIPTION_PRICES["yearly"],
                "currency": "PEN",
                "description": "Acceso completo por 365 días (descuento del 17%)",
                "discount": "17%"
            },
            "one-time": {
                "price": SUBSCRIPTION_PRICES["one-time"],
                "currency": "PEN",
                "description": "Acceso de prueba por 7 días"
            }
        }
    }