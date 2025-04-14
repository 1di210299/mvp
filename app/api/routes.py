from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.db import repositories
from app.db.models import Customer, Product, Order, ConversationStatus, OrderStatus
from pydantic import BaseModel, Field

router = APIRouter()

# === Modelos Pydantic ===

class CustomerCreate(BaseModel):
    phone_number: str
    name: Optional[str] = None
    dni: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    phone_number: str
    name: Optional[str] = None
    dni: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_blocked: bool
    
    class Config:
        orm_mode = True

class OrderItemCreate(BaseModel):
    product_id: int
    product_code: str
    quantity: int
    unit_price: float

class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    customer_id: int
    status: OrderStatus
    total_amount: float
    payment_link: Optional[str] = None
    
    class Config:
        orm_mode = True

class ProductResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    price: float
    inventory: int
    is_active: bool
    
    class Config:
        orm_mode = True

class BlacklistRequest(BaseModel):
    phone_number: str
    reason: Optional[str] = None

# === Endpoints de Clientes ===

@router.post("/customers/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer_endpoint(customer: CustomerCreate, db: Session = Depends(get_db)):
    """Crea un nuevo cliente."""
    # Verificar si ya existe
    db_customer = repositories.get_customer_by_phone(db, customer.phone_number)
    if db_customer:
        return db_customer
    # Verificar lista negra
    if repositories.is_phone_blacklisted(db, customer.phone_number):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El número de teléfono está bloqueado."
        )
    # Crear nuevo cliente
    return repositories.create_customer(
        db=db, 
        phone_number=customer.phone_number,
        name=customer.name,
        dni=customer.dni
    )

@router.get("/customers/{phone_number}", response_model=CustomerResponse)
def get_customer_endpoint(phone_number: str, db: Session = Depends(get_db)):
    """Obtiene un cliente por su número de teléfono."""
    customer = repositories.get_customer_by_phone(db, phone_number)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return customer

@router.post("/blacklist/", status_code=status.HTTP_201_CREATED)
def add_to_blacklist_endpoint(request: BlacklistRequest, db: Session = Depends(get_db)):
    """Añade un número a la lista negra."""
    # Verificar si ya existe
    if repositories.is_phone_blacklisted(db, request.phone_number):
        return {"status": "success", "message": "El número ya estaba en la lista negra"}
    
    # Añadir a la lista negra
    repositories.add_to_blacklist(db, request.phone_number, request.reason)
    
    # Bloquear al cliente si existe
    customer = repositories.get_customer_by_phone(db, request.phone_number)
    if customer:
        repositories.block_customer(db, customer.id, request.reason)
    
    return {"status": "success", "message": "Número añadido a la lista negra"}

@router.get("/blacklist/check/{phone_number}")
def check_blacklist_endpoint(phone_number: str, db: Session = Depends(get_db)):
    """Verifica si un número está en la lista negra."""
    is_blacklisted = repositories.is_phone_blacklisted(db, phone_number)
    return {"is_blacklisted": is_blacklisted}

# === Endpoints de Productos ===

@router.get("/products/", response_model=List[ProductResponse])
def get_all_products_endpoint(db: Session = Depends(get_db)):
    """Obtiene todos los productos activos."""
    return repositories.get_all_active_products(db)

@router.get("/products/{code}", response_model=ProductResponse)
def get_product_endpoint(code: str, db: Session = Depends(get_db)):
    """Obtiene un producto por su código."""
    product = repositories.get_product_by_code(db, code)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product

# === Endpoints de Órdenes ===

@router.post("/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(order: OrderCreate, db: Session = Depends(get_db)):
    """Crea una nueva orden."""
    # Verificar si el cliente existe
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Verificar si el cliente está bloqueado
    if customer.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El cliente está bloqueado"
        )
    
    # Validar y preparar items
    items_data = []
    for item in order.items:
        product = repositories.get_product_by_code(db, item.product_code)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con código {item.product_code} no encontrado"
            )
        
        # Validar inventario
        if product.inventory < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No hay suficiente inventario para {product.name}"
            )
        
        # Validar precio (opcional, para evitar manipulación)
        if abs(product.price - item.unit_price) > 0.01:  # Permitir pequeña variación por decimales
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El precio de {product.name} es incorrecto"
            )
        
        items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "unit_price": product.price
        })
    
    # Crear la orden
    return repositories.create_order(db, customer.id, items_data)