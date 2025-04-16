from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON, Enum, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# Enumeraciones
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAYMENT_LINK_SENT = "payment_link_sent"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"
    ABANDONED = "abandoned"

class PaymentMethod(str, enum.Enum):
    CULQI = "culqi"
    YAPE = "yape"
    CASH = "cash"
    OTHER = "other"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    INITIATED = "initiated"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class SecurityIncidentType(enum.Enum):
    SUSPICIOUS_MESSAGE = "suspicious_message"
    SPAM = "spam"
    PHISHING = "phishing"
    BLACKLISTED_NUMBER = "blacklisted_number"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    HONEYPOT_TRIGGERED = "honeypot_triggered"
    SUSPICIOUS_PAYMENT = "suspicious_payment"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    OTHER = "other"

class SecurityIncidentSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True)
    name = Column(String(100), nullable=True)
    dni = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    orders = relationship("Order", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")
    interactions = relationship("Interaction", back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_id = Column(String(100), nullable=True)
    payment_link = Column(String(255), nullable=True)
    payment_details = Column(JSON, nullable=True)  # Stores payment-specific data like Yape phone or QR
    payment_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    # Relaciones
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    context = Column(Text, nullable=True)  # JSON serializado
    suspicious_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    content = Column(Text)
    is_from_customer = Column(Boolean, default=True)
    suspicious_score = Column(Float, default=0.0)
    ai_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    conversation = relationship("Conversation", back_populates="messages")


class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    direction = Column(String(20))  # incoming, outgoing
    content = Column(Text)
    threat_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    customer = relationship("Customer", back_populates="interactions")


class BlacklistEntry(Base):
    __tablename__ = "blacklist_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    reason = Column(String)
    source = Column(String, default="manual")  # manual, automatic, api
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiration_date = Column(DateTime, nullable=True)


class UnblockRequest(Base):
    __tablename__ = "unblock_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, failed
    verification_code = Column(String)
    request_date = Column(DateTime, default=datetime.utcnow)
    processed_date = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)


class HoneypotRecord(Base):
    __tablename__ = "honeypot_records"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(36), unique=True, index=True)
    phone_number = Column(String(50))
    message_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="created")  # created, clicked, completed
    clicks = Column(Integer, default=0)
    ip_addresses = Column(JSON, nullable=True)
    user_agents = Column(JSON, nullable=True)
    telegram_info = Column(JSON, nullable=True)
    location_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)


class SecurityIncident(Base):
    __tablename__ = "security_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    description = Column(Text)
    severity = Column(String(20), default="medium")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    phone_number = Column(String(20))
    ip_address = Column(String(50))
    message_content = Column(Text)
    confidence_score = Column(Float)  # Puntuación entre 0 y 1 para la confianza de la detección
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)
    
    customer = relationship("Customer")