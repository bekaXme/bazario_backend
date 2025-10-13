from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from app.db import get_session
from app.models import Order, User, Product, Notification
from app.schemas import OrderCreate, OrderOut, OrderApprove
from app.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/")
def create_order(order_in: OrderCreate, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    total_coins = 0
    for item in order_in.products:
        product = session.get(Product, item["product_id"])
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
        total_coins += product.price * item["quantity"]
    order = Order(
        user_id=current_user.id,
        products=order_in.products,
        total_coins=total_coins,
        status="pending"
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    # Notify admins
    admins = session.exec(select(User).where(User.is_admin == True)).all()
    for admin in admins:
        note = Notification(
            user_id=admin.id,
            title="New Order",
            message=f"User {current_user.username} placed an order #{order.id} for {total_coins} coins."
        )
        session.add(note)
    session.commit()
    return {"id": order.id, "status": "pending"}

@router.get("/", response_model=List[OrderOut])
def list_orders(session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    return session.exec(select(Order)).all()

@router.post("/{order_id}/approve")
def approve_order(order_id: int, approve_in: OrderApprove, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order already processed")
    order.status = "approved"
    order.delivery_time = approve_in.delivery_time
    session.add(order)
    # Notify user
    note = Notification(
        user_id=order.user_id,
        title="Order Approved",
        message=f"Your order #{order.id} has been approved. Delivery time: {approve_in.delivery_time}"
    )
    session.add(note)
    session.commit()
    return {"ok": True, "status": "approved"}

@router.post("/{order_id}/reject")
def reject_order(order_id: int, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="Order already processed")
    order.status = "rejected"
    session.add(order)
    # Notify user
    note = Notification(
        user_id=order.user_id,
        title="Order Rejected",
        message=f"Your order #{order.id} has been rejected."
    )
    session.add(note)
    session.commit()
    return {"ok": True, "status": "rejected"}

@router.delete("/{order_id}")
def delete_order(order_id: int, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    session.delete(order)
    session.commit()
    return {"ok": True}