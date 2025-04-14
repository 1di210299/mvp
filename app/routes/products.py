# filepath: /Users/juandiegogutierrezcortez/mvp/app/routes/products.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import logging

from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Dict[str, Any]])
async def get_products(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de productos disponibles
    """
    # Implementación básica - en un sistema real, obtendrías datos de la BD
    products = [
        {
            "id": 1,
            "code": "P001",
            "name": "Producto 1",
            "price": 25.99,
            "description": "Descripción del producto 1",
            "stock": 10
        },
        {
            "id": 2,
            "code": "P002",
            "name": "Producto 2",
            "price": 15.50,
            "description": "Descripción del producto 2",
            "stock": 5
        }
    ]
    
    return products

@router.get("/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene información detallada de un producto
    """
    # Implementación básica - en un sistema real, obtendrías datos de la BD
    products = {
        1: {
            "id": 1,
            "code": "P001",
            "name": "Producto 1",
            "price": 25.99,
            "description": "Descripción detallada del producto 1",
            "stock": 10,
            "images": ["https://example.com/image1.jpg"]
        },
        2: {
            "id": 2,
            "code": "P002",
            "name": "Producto 2",
            "price": 15.50,
            "description": "Descripción detallada del producto 2",
            "stock": 5,
            "images": ["https://example.com/image2.jpg"]
        }
    }
    
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return products[product_id]