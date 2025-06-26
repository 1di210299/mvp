from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Esquemas de Usuario
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_premium: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Esquemas de CV
class CVCreate(BaseModel):
    original_content: str

class CVResponse(BaseModel):
    id: int
    original_content: str
    improved_content: Optional[str] = None
    feedback: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas de Carta de Presentación
class CoverLetterCreate(BaseModel):
    job_title: str
    company_name: str
    job_description: Optional[str] = None
    user_experience: Optional[str] = None

class CoverLetterResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    job_description: Optional[str] = None
    user_experience: Optional[str] = None
    generated_content: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas de Entrevista
class InterviewCreate(BaseModel):
    job_title: str
    company_name: Optional[str] = None

class InterviewMessage(BaseModel):
    user_response: str

class InterviewResponse(BaseModel):
    id: int
    job_title: str
    company_name: Optional[str] = None
    current_question: Optional[str] = None
    feedback: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class InterviewChat(BaseModel):
    question: str
    feedback: Optional[str] = None
    next_question: Optional[str] = None

# Esquemas de Pago
class PaymentCreate(BaseModel):
    subscription_type: str  # monthly, yearly, one-time
    payment_method: str = "simulation"

class PaymentResponse(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    subscription_type: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas de respuesta general
class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    detail: str