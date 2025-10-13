from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    phoneNumber: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: str
    is_admin: bool = False
    coins: int = 0


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, auto_increment=True)
    title: str
    description: Optional[str] = None
    price: int
    image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CoinRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    amount: int
    image_path: Optional[str] = None
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