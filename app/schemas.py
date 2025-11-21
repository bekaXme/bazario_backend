# app/schemas.py (Updated StoreCreate, added OrderCreate, OrderOut)
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class StoreCreate(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: Optional[float] = None  # Added
    longitude: Optional[float] = None  # Added

class ProductCreate(BaseModel):
    title: str
    price: int
    description: Optional[str] = None
    store_id: int

class CoinRequestCreate(BaseModel):
    amount: int

class CoinRequestOut(BaseModel):
    id: int
    user_id: int
    amount: int
    image_path: Optional[str]
    created_at: datetime
    reviewed: bool
    approved: Optional[bool]

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    read: bool
    created_at: datetime

class OrderCreate(BaseModel):
    products: List[Dict[str, int]]  # [{"product_id": 1, "quantity": 2}, ...]
    name: str
    phone_number: str
    address: str
    total_price: int

class OrderOut(BaseModel):
    id: int
    user_id: int
    products: List[Dict[str, int]]
    total_coins: int
    status: str
    delivery_time: Optional[datetime]
    created_at: datetime

class OrderApprove(BaseModel):
    delivery_time: datetime
    
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1