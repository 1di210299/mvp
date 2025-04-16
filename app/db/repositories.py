from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import json
import csv
import logging
from pathlib import Path

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

# Configurar logging
logger = logging.getLogger(__name__)

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

def import_products_from_file(db: Session, file_path: str) -> Dict[str, Any]:
    """
    Importa productos desde un archivo CSV o JSON proporcionado por la empresa.
    
    Args:
        db: Sesión de base de datos
        file_path: Ruta al archivo de productos (CSV o JSON)
        
    Returns:
        dict: Información sobre los productos importados
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {
                "status": "error",
                "message": f"El archivo {file_path} no existe"
            }
        
        file_extension = path.suffix.lower()
        products_data = []
        
        # Procesar según el tipo de archivo
        if file_extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
        elif file_extension == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                products_data = list(reader)
        else:
            return {
                "status": "error",
                "message": f"Formato de archivo no soportado: {file_extension}. Use CSV o JSON."
            }
        
        # Estadísticas de importación
        stats = {
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
        
        # Procesar cada producto
        for item in products_data:
            try:
                # Validar datos mínimos requeridos
                if not item.get('code') or not item.get('name') or not item.get('price'):
                    stats["skipped"] += 1
                    logger.warning(f"Producto sin datos requeridos: {item}")
                    continue
                
                # Convertir precio a float
                try:
                    price = float(item.get('price'))
                except ValueError:
                    stats["errors"] += 1
                    logger.error(f"Precio inválido para producto {item.get('code')}: {item.get('price')}")
                    continue
                
                # Verificar si el producto ya existe
                existing_product = db.query(Product).filter(Product.code == item.get('code')).first()
                
                if existing_product:
                    # Actualizar producto existente
                    existing_product.name = item.get('name')
                    existing_product.description = item.get('description', existing_product.description)
                    existing_product.price = price
                    existing_product.stock = int(item.get('stock', existing_product.stock))
                    existing_product.image_url = item.get('image_url', existing_product.image_url)
                    existing_product.is_active = item.get('is_active', True) in [True, 'true', 'True', '1', 1]
                    existing_product.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                else:
                    # Crear nuevo producto
                    new_product = Product(
                        code=item.get('code'),
                        name=item.get('name'),
                        description=item.get('description', ''),
                        price=price,
                        stock=int(item.get('stock', 0)),
                        image_url=item.get('image_url', None),
                        is_active=item.get('is_active', True) in [True, 'true', 'True', '1', 1],
                    )
                    db.add(new_product)
                    stats["added"] += 1
            
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error procesando producto {item.get('code')}: {str(e)}")
        
        # Guardar cambios en la base de datos
        db.commit()
        
        logger.info(f"Importación de productos completada: {stats}")
        return {
            "status": "success",
            "message": "Importación de productos completada",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error importando productos: {str(e)}")
        return {
            "status": "error",
            "message": f"Error importando productos: {str(e)}"
        }

def import_products_from_documentation(db: Session, company_info_path: str, products_path: str) -> Dict[str, Any]:
    """
    Importa productos y actualiza información de la empresa desde documentación proporcionada.
    
    Args:
        db: Sesión de base de datos
        company_info_path: Ruta al archivo con información de la empresa
        products_path: Ruta al archivo con lista de productos
        
    Returns:
        dict: Información sobre la importación
    """
    results = {
        "company_info": None,
        "products": None
    }
    
    # Importar información de la empresa (podría guardarla en otra tabla o configuración)
    if company_info_path:
        try:
            path = Path(company_info_path)
            if path.exists():
                file_extension = path.suffix.lower()
                company_data = {}
                
                if file_extension == '.json':
                    with open(company_info_path, 'r', encoding='utf-8') as f:
                        company_data = json.load(f)
                elif file_extension == '.csv':
                    with open(company_info_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            company_data = rows[0]  # Tomar la primera fila
                
                # Aquí podrías guardar la información de la empresa en una tabla específica
                # o en una tabla de configuración general
                
                results["company_info"] = {
                    "status": "success",
                    "data": company_data
                }
                
                logger.info(f"Información de empresa actualizada desde {company_info_path}")
            else:
                results["company_info"] = {
                    "status": "error",
                    "message": f"El archivo {company_info_path} no existe"
                }
        except Exception as e:
            logger.error(f"Error procesando información de empresa: {str(e)}")
            results["company_info"] = {
                "status": "error",
                "message": str(e)
            }
    
    # Importar productos
    if products_path:
        results["products"] = import_products_from_file(db, products_path)
    
    return results

def get_product_updates(db: Session, since_date: datetime = None) -> List[Dict[str, Any]]:
    """
    Obtiene productos actualizados desde una fecha específica.
    
    Args:
        db: Sesión de base de datos
        since_date: Fecha desde la cual buscar actualizaciones
        
    Returns:
        list: Lista de productos actualizados desde la fecha especificada
    """
    query = db.query(Product)
    
    if since_date:
        query = query.filter(Product.updated_at >= since_date)
    
    # Ordenar por fecha de actualización, más recientes primero
    query = query.order_by(Product.updated_at.desc())
    
    products = query.all()
    
    # Formatear para la respuesta
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "code": product.code,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "is_active": product.is_active,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        })
    
    return result

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
        # Calcular el subtotal para cada item
        subtotal = item["quantity"] * item["unit_price"]
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            subtotal=subtotal  # Añadir el subtotal calculado
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

def add_to_cart(db: Session, customer_id: int, product_codes: List[str], quantities: List[int] = None) -> Dict[str, Any]:
    """
    Añade productos al carrito (crea una orden pendiente o la actualiza).
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        product_codes: Lista de códigos de productos
        quantities: Lista de cantidades (opcional, por defecto 1)
        
    Returns:
        dict: Información sobre los productos añadidos y el total
    """
    # Validar datos de entrada
    if not product_codes:
        return {
            "status": "error",
            "message": "No se proporcionaron códigos de productos"
        }
    
    # Si no se proporcionan cantidades, asumir 1 para cada producto
    if not quantities:
        quantities = [1] * len(product_codes)
    elif len(quantities) != len(product_codes):
        return {
            "status": "error",
            "message": "La cantidad de cantidades no coincide con la cantidad de productos"
        }
    
    # Verificar si el cliente tiene una orden pendiente
    pending_order = db.query(Order).filter(
        Order.customer_id == customer_id,
        Order.status == OrderStatus.PENDING
    ).first()
    
    # Si no hay orden pendiente, crear una nueva
    if not pending_order:
        pending_order = Order(
            customer_id=customer_id,
            total_amount=0,
            status=OrderStatus.PENDING
        )
        db.add(pending_order)
        db.commit()
        db.refresh(pending_order)
    
    # Lista para almacenar información de productos añadidos
    added_items = []
    total_order_amount = 0
    
    # Añadir cada producto al carrito
    for i, code in enumerate(product_codes):
        quantity = quantities[i]
        
        # Buscar el producto por código
        product = get_product_by_code(db, code)
        if not product:
            continue  # Saltar productos que no existen
        
        # Verificar si el producto ya está en la orden
        existing_item = db.query(OrderItem).filter(
            OrderItem.order_id == pending_order.id,
            OrderItem.product_id == product.id
        ).first()
        
        # Si el producto ya está en la orden, actualizar cantidad
        if existing_item:
            existing_item.quantity += quantity
            existing_item.updated_at = datetime.utcnow()
        else:
            # Si no, crear nuevo item de orden
            item_subtotal = quantity * product.price
            existing_item = OrderItem(
                order_id=pending_order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                subtotal=item_subtotal  # Añadir el subtotal calculado
            )
            db.add(existing_item)
        
        # Actualizar total
        item_total = product.price * quantity
        added_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "code": product.code,
            "quantity": quantity,
            "unit_price": product.price,
            "total": item_total
        })
    
    # Recalcular el total de la orden
    db.commit()  # Guardar primero para asegurar que los ítems estén en la DB
    
    # Obtener todos los items de la orden actualizada
    order_items = db.query(OrderItem).filter(OrderItem.order_id == pending_order.id).all()
    total_amount = sum(item.quantity * item.unit_price for item in order_items)
    
    # Actualizar el total de la orden
    pending_order.total_amount = total_amount
    pending_order.updated_at = datetime.utcnow()
    db.commit()
    
    # Obtener todos los ítems de la orden para el resumen del carrito
    all_items = []
    for item in order_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        all_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "code": product.code,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item.quantity * item.unit_price
        })
    
    return {
        "status": "success",
        "added_items": added_items,
        "all_items": all_items,
        "order_id": pending_order.id,
        "total_amount": total_amount
    }

def get_cart(db: Session, customer_id: int) -> Dict[str, Any]:
    """
    Obtiene el carrito actual (orden pendiente) de un cliente.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        
    Returns:
        dict: Información sobre los productos en el carrito y el total
    """
    # Buscar orden pendiente
    pending_order = db.query(Order).filter(
        Order.customer_id == customer_id,
        Order.status == OrderStatus.PENDING
    ).first()
    
    # Si no hay orden pendiente, retornar carrito vacío
    if not pending_order:
        return {
            "status": "success",
            "items": [],
            "total_amount": 0
        }
    
    # Obtener items de la orden
    order_items = db.query(OrderItem).filter(OrderItem.order_id == pending_order.id).all()
    
    # Formatear items para la respuesta
    items = []
    for item in order_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        items.append({
            "product_id": product.id,
            "product_name": product.name,
            "code": product.code,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total": item.quantity * item.unit_price
        })
    
    return {
        "status": "success",
        "order_id": pending_order.id,
        "items": items,
        "total_amount": pending_order.total_amount
    }

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