from pydantic import BaseModel
from typing import List, Optional

class MenuCreate(BaseModel):
    name: str
    price: int
    stock: int
    
class MenuUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None
    
class MenuResponse(BaseModel):
    id: int
    name: str
    price: int
    stock: int
    
    class Config:
        orm_mode = True
        
class MenuStockUpdate(BaseModel):
    stock: int

class SalesItem(BaseModel):
    menu_id: int
    qty: int

class TransactionCreate(BaseModel):
    items: List[SalesItem]