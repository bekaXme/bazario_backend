from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class ProductCreate(BaseModel):
    title: str
    price: int
    description: Optional[str] = None


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