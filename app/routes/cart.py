# cart.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from uuid import uuid4

router = APIRouter(prefix="/cart", tags=["Cart"])

# In-memory cart storage (replace with DB in production)
CART_DB = {}

# Pydantic models
class CartItem(BaseModel):
    product_id: int
    name: str
    price: float
    amount: int

class CartResponse(BaseModel):
    items: List[CartItem]
    total_price: float

class AddToCartRequest(BaseModel):
    product_id: int
    name: str
    price: float
    amount: int

class UpdateCartRequest(BaseModel):
    product_id: int
    amount: int


def calculate_total(items: List[CartItem]):
    return sum(item.price * item.amount for item in items)


# Routes
@router.get("/", response_model=CartResponse)
def get_cart(user_id: str = "default_user"):
    cart_items = CART_DB.get(user_id, [])
    return CartResponse(items=cart_items, total_price=calculate_total(cart_items))


@router.post("/add", response_model=CartResponse)
def add_to_cart(data: AddToCartRequest, user_id: str = "default_user"):
    cart_items = CART_DB.get(user_id, [])
    
    # Check if product already exists
    for item in cart_items:
        if item.product_id == data.product_id:
            item.amount += data.amount
            CART_DB[user_id] = cart_items
            return CartResponse(items=cart_items, total_price=calculate_total(cart_items))
    
    # Add new product
    cart_items.append(CartItem(**data.dict()))
    CART_DB[user_id] = cart_items
    return CartResponse(items=cart_items, total_price=calculate_total(cart_items))


@router.post("/update", response_model=CartResponse)
def update_cart(data: UpdateCartRequest, user_id: str = "default_user"):
    cart_items = CART_DB.get(user_id, [])
    for item in cart_items:
        if item.product_id == data.product_id:
            item.amount = data.amount
            CART_DB[user_id] = cart_items
            return CartResponse(items=cart_items, total_price=calculate_total(cart_items))
    raise HTTPException(status_code=404, detail="Product not in cart")


@router.delete("/remove/{product_id}", response_model=CartResponse)
def remove_from_cart(product_id: int, user_id: str = "default_user"):
    cart_items = CART_DB.get(user_id, [])
    cart_items = [item for item in cart_items if item.product_id != product_id]
    CART_DB[user_id] = cart_items
    return CartResponse(items=cart_items, total_price=calculate_total(cart_items))


@router.delete("/clear", response_model=CartResponse)
def clear_cart(user_id: str = "default_user"):
    CART_DB[user_id] = []
    return CartResponse(items=[], total_price=0.0)
