from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Transaction(BaseModel):
    gender: str
    edad: int
    categoria: str
    cantidad: int
    payment_method: str
    fecha: datetime
    shopping_mall: str
    StockCode: str
    Description: str
    Country: str
    Customer_Name: str
    Product: str
    City: str
    Store_Type: str
    Discount_Applied: float
    Customer_Category: str
    Season: str
    Promotion: str
    TransactionNo: str
    recarga: float
    precio_final: float
    precio_unitario: float
    mail: str
    number: str
    Customer_ID: str

class CustomerProfile(BaseModel):
    Customer_ID: str
    Customer_Name: str
    gender: str
    edad: int
    Customer_Category: str
    mail: str
    number: str