from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, JSON, Column

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    hashed_password: str
    is_admin: bool = False
    coins: int = 0

class Store(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None  # Added latitude
    longitude: Optional[float] = None  # Added longitude
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    price: int
    image_path: Optional[str] = None
    store_id: int = Field(foreign_key="store.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CoinRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    amount: int
    image_path: Optional[str] = None  # Transaction picture
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    approved: Optional[bool] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[int] = None

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    title: str
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    products: List[dict] = Field(default_factory=list, sa_column=Column(JSON))  # List of {"product_id": int, "quantity": int}
    total_coins: int
    status: str = "pending"  # pending, approved, rejected, delivered
    delivery_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class CartItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    product_id: int
    quantity: int = 1
    added_at: datetime = Field(default_factory=datetime.utcnow)