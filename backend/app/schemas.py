from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MenuCreate(BaseModel):
    name: str
    price: int
    stock: int
    
class MenuUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    
class MenuStockUpdate(BaseModel):
    stock: int

class MenuResponse(BaseModel):
    id: int
    name: str
    price: int
    stock: int
    
    class Config:
        from_attributes = True
class Item(BaseModel):
    menu_id: int
    qty: int

class TransactionCreate(BaseModel):
    items: List[Item]

class TransactionDetailResponse(BaseModel):
    menu_id: int
    qty: int
    subtotal: int
    
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    created_at: datetime
    total_price: int
    details: List[TransactionDetailResponse]
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str # "owner" atau "kasir"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str