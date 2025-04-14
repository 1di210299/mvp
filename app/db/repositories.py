from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union

from app.db.models import (
    Customer, 
    Order, 
    OrderItem, 
    Product, 
    Conversation, 
    Message, 
    BlacklistEntry,
    OrderStatus,
    ConversationStatus
)

# === Customer Repository ===

def get_customer_by_phone(db: Session, phone_number: str) -> Optional[Customer]:
    """Obtiene un cliente por su número de teléfono."""
    return db.query(Customer).filter(Customer.phone_number == phone_number).first()

def create_customer(db: Session, phone_number: str, name: str = None, dni: str = None) -> Customer:
    """Crea un nuevo cliente."""
    customer = Customer(
        phone_number=phone_number,
        name=name,
        dni=dni
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def update_customer(db: Session, customer_id: int, data: Dict[str, Any]) -> Customer:
    """Actualiza los datos de un cliente."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(customer)
    return customer

def block_customer(db: Session, customer_id: int, reason: str = None) -> Customer:
    """Bloquea a un cliente."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.is_blocked = True
        customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(customer)
        
        # Añadir a la lista negra si no existe
        phone_number = customer.phone_number
        blacklist_entry = db.query(BlacklistEntry).filter(
            BlacklistEntry.phone_number == phone_number
        ).first()
        
        if not blacklist_entry:
            blacklist_entry = BlacklistEntry(
                phone_number=phone_number,
                reason=reason
            )
            db.add(blacklist_entry)
            db.commit()
    
    return customer

# === Blacklist Repository ===

def is_phone_blacklisted(db: Session, phone_number: str) -> bool:
    """Verifica si un número de teléfono está en la lista negra."""
    return db.query(BlacklistEntry).filter(
        BlacklistEntry.phone_number == phone_number
    ).first() is not None

def add_to_blacklist(db: Session, phone_number: str, reason: str = None) -> BlacklistEntry:
    """Añade un número a la lista negra."""
    entry = BlacklistEntry(
        phone_number=phone_number,
        reason=reason
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# === Product Repository ===

def get_product_by_code(db: Session, code: str) -> Optional[Product]:
    """Obtiene un producto por su código."""
    return db.query(Product).filter(
        Product.code == code,
        Product.is_active == True
    ).first()

def get_all_active_products(db: Session) -> List[Product]:
    """Obtiene todos los productos activos."""
    return db.query(Product).filter(Product.is_active == True).all()

# === Order Repository ===

def create_order(
    db: Session, 
    customer_id: int, 
    items: List[Dict[str, Union[int, float]]]
) -> Order:
    """
    Crea una nueva orden.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        items: Lista de diccionarios con product_id, quantity y unit_price
    
    Returns:
        Order: Objeto de orden creado
    """
    # Calcular el monto total
    total_amount = sum(item["quantity"] * item["unit_price"] for item in items)
    
    # Crear la orden
    order = Order(
        customer_id=customer_id,
        total_amount=total_amount,
        status=OrderStatus.PENDING
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Crear los items de la orden
    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"]
        )
        db.add(order_item)
    
    db.commit()
    return order

def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Order:
    """Actualiza el estado de una orden."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = status
        order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order)
    return order

def update_order_payment(
    db: Session, 
    order_id: int, 
    payment_link: str = None, 
    payment_id: str = None
) -> Order:
    """Actualiza la información de pago de una orden."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        if payment_link:
            order.payment_link = payment_link
            order.status = OrderStatus.PAYMENT_LINK_SENT
        if payment_id:
            order.payment_id = payment_id
            order.status = OrderStatus.PAID
        order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order)
    return order

# === Conversation Repository ===

def create_conversation(db: Session, customer_id: int) -> Conversation:
    """Crea una nueva conversación."""
    conversation = Conversation(
        customer_id=customer_id,
        status=ConversationStatus.ACTIVE
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_active_conversation(db: Session, customer_id: int) -> Optional[Conversation]:
    """Obtiene la conversación activa de un cliente."""
    return db.query(Conversation).filter(
        Conversation.customer_id == customer_id,
        Conversation.status == ConversationStatus.ACTIVE
    ).order_by(Conversation.created_at.desc()).first()

def update_conversation_status(
    db: Session, 
    conversation_id: int, 
    status: ConversationStatus,
    suspicious_score: float = None
) -> Conversation:
    """Actualiza el estado de una conversación."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.status = status
        if suspicious_score is not None:
            conversation.suspicious_score = suspicious_score
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)
    return conversation

def add_message(
    db: Session, 
    conversation_id: int, 
    content: str, 
    is_from_customer: bool = True,
    suspicious_score: float = 0.0,
    ai_analysis: Dict = None
) -> Message:
    """Añade un mensaje a una conversación."""
    message = Message(
        conversation_id=conversation_id,
        content=content,
        is_from_customer=is_from_customer,
        suspicious_score=suspicious_score,
        ai_analysis=ai_analysis
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Actualizar score de conversación si el mensaje es sospechoso
    if suspicious_score > 0:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        conversation_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_from_customer == True
        ).all()
        
        # Calcular score promedio de mensajes del cliente
        avg_score = sum(m.suspicious_score for m in conversation_messages) / len(conversation_messages)
        
        # Actualizar score de la conversación
        conversation.suspicious_score = avg_score
        
        # Si supera umbral, marcar como sospechoso
        from app.config import MIN_SUSPICIOUS_SCORE
        if avg_score >= MIN_SUSPICIOUS_SCORE:
            conversation.status = ConversationStatus.SUSPICIOUS
        
        db.commit()
    
    return message