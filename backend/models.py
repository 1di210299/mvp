from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    cvs = relationship("CV", back_populates="user")
    cover_letters = relationship("CoverLetter", back_populates="user")
    interviews = relationship("Interview", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_content = Column(Text, nullable=False)
    improved_content = Column(Text)
    feedback = Column(Text)
    status = Column(String, default="pending")  # pending, processing, completed, error
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación
    user = relationship("User", back_populates="cvs")

class CoverLetter(Base):
    __tablename__ = "cover_letters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    job_description = Column(Text)
    user_experience = Column(Text)
    generated_content = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación
    user = relationship("User", back_populates="cover_letters")

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String, nullable=False)
    company_name = Column(String)
    conversation_history = Column(Text)  # JSON string
    current_question = Column(Text)
    feedback = Column(Text)
    status = Column(String, default="active")  # active, completed, paused
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación
    user = relationship("User", back_populates="interviews")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="PEN")  # Soles peruanos
    status = Column(String, nullable=False)  # pending, completed, failed, cancelled
    payment_method = Column(String)  # stripe, culqi, simulation
    transaction_id = Column(String, unique=True)
    subscription_type = Column(String)  # monthly, yearly, one-time
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación
    user = relationship("User", back_populates="payments")