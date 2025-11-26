from typing import Dict, Optional, List
from fastapi import FastAPI, Body, APIRouter
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from datetime import datetime
import json
import os
import http.client

app = FastAPI()
router = APIRouter(prefix="/notifications", tags=["Notifications"])

FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY")
FCM_URL = "https://fcm.googleapis.com/fcm/send"
FCM_HOST = "fcm.googleapis.com"
FCM_PATH = "/fcm/send"

# =====================================================
# In-memory storage (replace with DB in production)
# =====================================================
user_tokens: Dict[int, str] = {}   # Maps user_id -> FCM token
admins = [1, 2]

orders: Dict[int, Dict] = {}
order_counter = 1


# =====================================================
# Helper: Send Push Notification
# =====================================================
def send_push_notification(token: str, title: str, body: str, data: Optional[Dict] = None):

    conn = http.client.HTTPSConnection(FCM_HOST)

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

    conn.request("POST", FCM_PATH, body=json.dumps(payload), headers=headers)
    res = conn.getresponse()
    response_text = res.read().decode()

    return {
        "status_code": res.status,
        "response": response_text
    }


# =====================================================
# Save Token
# =====================================================
@router.post("/save_token")
def save_token(body: Dict = Body(...)):
    user_id = body.get("user_id")
    token = body.get("token")

    if not user_id or not token:
        return {"success": False, "message": "user_id and token required"}

    user_tokens[user_id] = token
    return {"success": True, "message": "Token saved"}


# =====================================================
# User Finishes Order
# =====================================================
@router.post("/order_finish")
def order_finish(body: Dict = Body(...)):
    global order_counter

    required_fields = ["user_id", "name", "phone", "location", "products", "total_price"]
    for f in required_fields:
        if f not in body:
            return {"success": False, "message": f"{f} is required"}

    order_id = order_counter
    order_counter += 1

    orders[order_id] = {
        "order_id": order_id,
        "user_id": body["user_id"],
        "name": body["name"],
        "phone": body["phone"],
        "location": body["location"],
        "products": body["products"],
        "total_price": body["total_price"],
        "status": "pending",
        "delivery_time": None
    }

    # Notify admins
    title = "🛍️ New Order Received"
    body_text = f"{body['name']} placed an order totaling {body['total_price']} UZS"

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
def approve_order(body: Dict = Body(...)):
    order_id = body.get("order_id")
    approve = body.get("approve", True)
    delivery_time = body.get("delivery_time", None)

    if order_id not in orders:
        return {"success": False, "message": "Order not found"}

    order = orders[order_id]
    user_id = order["user_id"]

    if approve:
        order["status"] = "approved"
        order["delivery_time"] = delivery_time
        title = "🚚 Delivery Confirmed"
        message = f"Your order will arrive in {delivery_time} minutes"
        data = {"type": "approved", "order_id": order_id}
    else:
        order["status"] = "denied"
        order["delivery_time"] = None
        title = "❌ Order Denied"
        message = "Your order has been denied"
        data = {"type": "denied", "order_id": order_id}

    token = user_tokens.get(user_id)
    result = None
    if token:
        result = send_push_notification(token, title, message, data=data)

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
# Send Notification to Any User
# =====================================================
@router.post("/send_to_user")
def send_to_user(body: Dict = Body(...)):
    user_id = body.get("user_id")
    title = body.get("title")
    message = body.get("message")

    if not all([user_id, title, message]):
        return {"success": False, "message": "user_id, title, message required"}

    token = user_tokens.get(user_id)
    if not token:
        return {"success": False, "message": "FCM token not found"}

    result = send_push_notification(token, title, message)
    return {"success": True, "result": result}


app.include_router(router)



