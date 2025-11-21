from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from app.db import get_session
from app.models import Order, User, Product, Notification
from app.schemas import OrderCreate, OrderOut, OrderApprove
from app.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/orders", tags=["orders"])


# -----------------------------
# CREATE ORDER
# -----------------------------
@router.post("/", response_model=Dict)
def create_order(
    order_in: OrderCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    total_price = 0
    total_coins = 0

    # Validate products and calculate total
    for item in order_in.products:
        product = session.get(Product, item["product_id"])
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")
        quantity = item.get("quantity", 1)
        total_price += product.price * quantity
        total_coins += product.price * quantity

    # Create order
    order = Order(
        user_id=current_user.id,
        products=order_in.products,  # JSON column
        total_coins=total_coins,
        total_price=total_price,
        status="pending",
        name=order_in.name,
        phone_number=order_in.phone_number,
        address=order_in.address,
        created_at=datetime.utcnow(),
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
            message=f"User {current_user.username} placed order #{order.id}. Total: {total_price} coins",
            created_at=datetime.utcnow()
        )
        session.add(note)

    session.commit()

    return {
        "id": order.id,
        "status": order.status,
        "total_price": total_price
    }

# -----------------------------
# LIST ORDERS (ADMIN)
# -----------------------------
@router.get("/", response_model=List[OrderOut])
def list_orders(session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    return session.exec(select(Order)).all()


# -----------------------------
# APPROVE ORDER
# -----------------------------
@router.post("/{order_id}/approve")
def approve_order(
    order_id: int,
    approve_in: OrderApprove,
    session: Session = Depends(get_session),
    admin=Depends(get_admin_user)
):
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
        message=f"Your order #{order.id} is approved. Delivery time: {approve_in.delivery_time}",
        created_at=datetime.utcnow(),
    )
    session.add(note)

    session.commit()
    return {"ok": True, "status": "approved"}


# -----------------------------
# REJECT ORDER
# -----------------------------
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
        message=f"Your order #{order.id} was rejected.",
        created_at=datetime.utcnow(),
    )
    session.add(note)

    session.commit()
    return {"ok": True, "status": "rejected"}


# -----------------------------
# DELETE ORDER
# -----------------------------
@router.delete("/{order_id}")
def delete_order(order_id: int, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    session.delete(order)
    session.commit()
    return {"ok": True}


# -----------------------------
# FINISH ORDER (USER)
# -----------------------------
@router.post("/{order_id}/finish")
def finish_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user)
):
    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")

    if order.status != "approved":
        raise HTTPException(status_code=400, detail="Order must be approved first")

    user = session.get(User, current_user.id)

    # User must have enough coins
    if user.coins < order.total_price:
        raise HTTPException(status_code=400, detail="Not enough coins")

    # Deduct coins
    user.coins -= order.total_price

    # Transfer coins to admin
    admin = session.exec(select(User).where(User.is_admin == True)).first()
    if admin:
        admin.coins += order.total_price
        session.add(admin)

    order.status = "finished"

    session.add(order)
    session.add(user)

    # Notify user
    note = Notification(
        user_id=user.id,
        title="Order Completed",
        message=f"You paid {order.total_price} coins. New balance: {user.coins}",
        created_at=datetime.utcnow(),
    )
    session.add(note)

    session.commit()

    return {
        "ok": True,
        "new_balance": user.coins
    }
