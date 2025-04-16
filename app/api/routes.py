from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.db import repositories
from app.db.models import Customer, Product, Order, ConversationStatus, OrderStatus, BlacklistEntry
from pydantic import BaseModel, Field

router = APIRouter()

# Import and register the webhooks router
from app.api import webhooks
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Import the diagnostico router for debugging
try:
    from app.api import diagnostico
    router.include_router(diagnostico.router, prefix="/debug", tags=["diagnostico"])
except ImportError:
    pass

# Try to import and register the unblock router if it exists
try:
    from app.api import unblock
    router.include_router(unblock.router, prefix="/security", tags=["security"])
except ImportError:
    pass

# Try to register other routers if they exist
try:
    from app.api import items
    router.include_router(items.router, prefix="/items", tags=["items"])
except ImportError:
    pass

try:
    from app.api import users
    router.include_router(users.router, prefix="/users", tags=["users"])
except ImportError:
    pass

@router.get("/")
async def api_root():
    """
    API root endpoint
    """
    return {
        "status": "online",
        "endpoints": [
            "/api/unblock - Endpoints for unblocking phone numbers",
            "/api/webhooks - Endpoints for webhook integrations",
            "/api/whatsapp - WhatsApp integration endpoints"
        ]
    }

@router.get("/whatsapp/unblock-instructions/{phone_number}", response_model=Dict[str, Any])
async def get_unblock_instructions(
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Get instructions for unblocking a phone number
    """
    # Normalize phone number
    if not phone_number.startswith("whatsapp:"):
        normalized_phone = f"whatsapp:{phone_number}"
    else:
        normalized_phone = phone_number
    
    # Check if phone is blacklisted
    blacklist_entry = db.query(BlacklistEntry).filter(
        BlacklistEntry.phone_number == normalized_phone,
        BlacklistEntry.is_active == True
    ).first()
    
    if not blacklist_entry:
        return {
            "success": True,
            "is_blocked": False,
            "message": "Este número no está bloqueado."
        }
    
    # Provide unblock instructions
    return {
        "success": True,
        "is_blocked": True,
        "message": "Tu número está bloqueado por motivos de seguridad.",
        "instructions": [
            "Para solicitar el desbloqueo, envía un mensaje con la palabra 'SOLICITUD DESBLOQUEO' seguido de una breve explicación.",
            "Si ya tienes un código de verificación, envía 'VERIFICAR' seguido del código.",
            "También puedes usar la herramienta de línea de comandos: python scripts/unblock_number.py request TU_NUMERO"
        ]
    }

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
    inventory: int = Field(alias="stock")  # Mapea stock a inventory para compatibilidad
    is_active: bool
    image_url: Optional[str] = None
    
    class Config:
        orm_mode = True
        populate_by_name = True

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