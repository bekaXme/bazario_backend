from typing import Dict, Optional, List
from fastapi import FastAPI, Body, APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json
import os
import requests 

app = FastAPI()
router = APIRouter(prefix="/notifications", tags=["Notifications"])

FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY")
FCM_URL = "https://fcm.googleapis.com/fcm/send"

user_tokens: Dict[int, str] = {}  
admins = [1, 2]  

orders: Dict[int, Dict] = {}
order_counter = 1

class Order(BaseModel):
    user_id: int
    name: str
    phone: str
    location: str
    products: List[Dict]
    total_price: int

class ApproveBody(BaseModel):
    order_id: int
    approve: bool = True
    delivery_time: Optional[int] = None  # Minutes

# =====================================================
# Helper: Send Push Notification (updated to use requests)
# =====================================================
def send_push_notification(token: str, title: str, body: str, data: Optional[Dict] = None):
    payload = {
        "to": token,
        "notification": {
            "title": title,
            "body": body,
            "sound": "default"
        },
        "priority": "high",
        "data": data or {}
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"key={FIREBASE_SERVER_KEY}"
    }

    try:
        response = requests.post(FCM_URL, json=payload, headers=headers)
        return {
            "status_code": response.status_code,
            "response": response.text
        }
    except Exception as e:
        return {
            "status_code": 500,
            "response": str(e)
        }

# =====================================================
# Save Token
# =====================================================
@router.post("/save_token")
def save_token(body: Dict = Body(...)):
    user_id = body.get("user_id")
    token = body.get("token")

    if not user_id or not token:
        raise HTTPException(status_code=400, detail="user_id and token required")

    user_tokens[user_id] = token
    return {"success": True, "message": "Token saved"}

# =====================================================
# User Finishes Order
# =====================================================
@router.post("/order_finish")
def order_finish(order: Order):
    global order_counter

    order_id = order_counter
    order_counter += 1

    orders[order_id] = {
        "order_id": order_id,
        "user_id": order.user_id,
        "name": order.name,
        "phone": order.phone,
        "location": order.location,
        "products": order.products,
        "total_price": order.total_price,
        "status": "pending",
        "delivery_time": None,
        "created_at": datetime.utcnow().isoformat()
    }

    # Notify admins
    title = "🛍️ New Order Received"
    body_text = f"{order.name} placed an order totaling {order.total_price} UZS"

    results = []
    for admin_id in admins:
        token = user_tokens.get(admin_id)
        if token:
            res = send_push_notification(
                token,
                title,
                body_text,
                data={"type": "order", "order_id": order_id}
            )
            results.append({"admin_id": admin_id, "result": res})

    return {"success": True, "order_id": order_id, "admin_notifications": results}

# =====================================================
# Admin Approves or Denies Order
# =====================================================
@router.post("/approve_order")
def approve_order(body: ApproveBody):
    if body.order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[body.order_id]
    user_id = order["user_id"]

    if body.approve:
        if body.delivery_time is None or body.delivery_time <= 0:
            raise HTTPException(status_code=400, detail="delivery_time required and must be positive for approval")
        order["status"] = "approved"
        order["delivery_time"] = body.delivery_time
        title = "🚚 Delivery Confirmed"
        message = f"Your order will arrive in {body.delivery_time} minutes"
        data = {"type": "approved", "order_id": body.order_id, "delivery_time": body.delivery_time}
    else:
        order["status"] = "denied"
        order["delivery_time"] = None
        title = "❌ Order Denied"
        message = "Your order has been denied"
        data = {"type": "denied", "order_id": body.order_id}

    token = user_tokens.get(user_id)
    result = None
    if token:
        result = send_push_notification(token, title, message, data=data)
    else:
        raise HTTPException(status_code=404, detail="User FCM token not found")

    return {"success": True, "order": order, "fcm_result": result}

# =====================================================
# Admin: View All Pending Orders
# =====================================================
@router.get("/admin_orders")
def admin_orders():
    return {"success": True, "pending_orders": [o for o in orders.values() if o["status"] == "pending"]}

# =====================================================
# User: View All Their Orders
# =====================================================
@router.get("/user_orders/{user_id}")
def user_orders(user_id: int):
    return {"success": True, "orders": [o for o in orders.values() if o["user_id"] == user_id]}

# =====================================================
# Send Notification to Any User (optional utility)
# =====================================================
@router.post("/send_to_user")
def send_to_user(body: Dict = Body(...)):
    user_id = body.get("user_id")
    title = body.get("title")
    message = body.get("message")

    if not all([user_id, title, message]):
        raise HTTPException(status_code=400, detail="user_id, title, message required")

    token = user_tokens.get(user_id)
    if not token:
        raise HTTPException(status_code=404, detail="FCM token not found")

    result = send_push_notification(token, title, message)
    return {"success": True, "result": result}

app.include_router(router)