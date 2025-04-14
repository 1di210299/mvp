# filepath: /Users/juandiegogutierrezcortez/mvp/app/routes/orders.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import logging
from datetime import datetime

from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Dict[str, Any]])
async def get_orders(
    phone_number: str = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de órdenes
    """
    # Implementación básica - en un sistema real, obtendrías datos de la BD
    orders = [
        {
            "id": 1,
            "phone_number": "whatsapp:+51987654321",
            "status": "pending",
            "total": 41.49,
            "items": [
                {"product_id": 1, "quantity": 1, "price": 25.99},
                {"product_id": 2, "quantity": 1, "price": 15.50}
            ],
            "created_at": datetime.now().isoformat()
        }
    ]
    
    # Filtrar por número de teléfono si se proporciona
    if phone_number:
        orders = [order for order in orders if order["phone_number"] == phone_number]
    
    return orders

@router.post("/create", response_model=Dict[str, Any])
async def create_order(
    phone_number: str = Body(...),
    items: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva orden
    """
    try:
        # Implementación básica - en un sistema real, guardarías en la BD
        # Calcular el total
        total = sum(item["price"] * item["quantity"] for item in items)
        
        new_order = {
            "id": 2,  # En un sistema real, se generaría automáticamente
            "phone_number": phone_number,
            "status": "pending",
            "total": total,
            "items": items,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "order": new_order,
            "message": "Orden creada correctamente"
        }
    
    except Exception as e:
        logger.error(f"Error creando orden: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))