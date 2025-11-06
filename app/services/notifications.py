from typing import Dict, Optional, List
from fastapi import FastAPI, Body, APIRouter
import requests
import json

app = FastAPI()
router = APIRouter(prefix="/notifications", tags=["Notifications"])

# -----------------------------
# Firebase server key
# -----------------------------
FIREBASE_SERVER_KEY = "BHkmvG6hhHssmPsF54qUKKbcbbcpCZdqvg6LyzMMX_bkbrhd1YwG3nXZHXe8NQ-LVSwcUaqj0Q8fYhpjgCHdlTI"

# -----------------------------
# In-memory storage
# -----------------------------
user_tokens: Dict[int, str] = {}   # FCM tokens
admins = [1, 2]                    # Admin user IDs

# Store all orders
# order_id -> order info
orders: Dict[int, Dict] = {}
order_counter = 1  # Auto-increment order_id


# -----------------------------
# Helper: send push notification
# -----------------------------
def send_push_notification(token: str, title: str, body: str, data: Optional[Dict] = None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"key={FIREBASE_SERVER_KEY}"
    }
    payload = {
        "to": token,
        "notification": {
            "title": title,
            "body": body,
            "sound": "default"
        },
        "priority": "high"
    }
    if data:
        payload["data"] = data

    response = requests.post(
        "https://fcm.googleapis.com/fcm/send",
        headers=headers,
        data=json.dumps(payload)
    )
    return {"status_code": response.status_code, "response": response.text}


# -----------------------------
# Save token
# -----------------------------
@router.post("/save_token")
def save_token(body: Dict = Body(...)):
    user_id = body.get("user_id")
    token = body.get("token")
    if not user_id or not token:
        return {"success": False, "message": "user_id and token are required"}

    user_tokens[user_id] = token
    return {"success": True, "message": f"Token saved for user {user_id}"}


# -----------------------------
# User finishes order
# -----------------------------
@router.post("/order_finish")
def order_finish(body: Dict = Body(...)):
    global order_counter
    user_id = body.get("user_id")
    name = body.get("name")
    phone = body.get("phone")
    location = body.get("location")
    products = body.get("products")
    total_price = body.get("total_price")

    if not all([user_id, name, phone, location, products, total_price]):
        return {"success": False, "message": "All fields are required"}

    order_id = order_counter
    order_counter += 1

    # Store the order
    orders[order_id] = {
        "order_id": order_id,
        "user_id": user_id,
        "name": name,
        "phone": phone,
        "location": location,
        "products": products,
        "total_price": total_price,
        "status": "pending",  # pending / approved / denied
        "delivery_time": None
    }

    # Notify admins
    title = "🛍️ New Order Received"
    body_text = f"{name} placed an order totaling {total_price} UZS"

    results = []
    for admin_id in admins:
        token = user_tokens.get(admin_id)
        if token:
            res = send_push_notification(token, title, body_text, data={"type": "order", "order_id": order_id, "user_id": user_id})
            results.append({"admin_id": admin_id, "fcm_result": res})

    return {"success": True, "message": "Order notification sent to admins", "results": results, "order_id": order_id}


# -----------------------------
# Admin approves order
# -----------------------------
@router.post("/approve_order")
def approve_order(body: Dict = Body(...)):
    order_id = body.get("order_id")
    delivery_time = body.get("delivery_time")
    approve = body.get("approve", True)  # True = approved, False = denied

    if order_id not in orders:
        return {"success": False, "message": "Order not found"}

    orders[order_id]["status"] = "approved" if approve else "denied"
    orders[order_id]["delivery_time"] = delivery_time if approve else None
    user_id = orders[order_id]["user_id"]

    # Send notification to user
    if approve:
        title = "🚚 Delivery Confirmed"
        body_text = f"Your order will be delivered in {delivery_time} minutes"
    else:
        title = "❌ Order Denied"
        body_text = f"Your order has been denied by the admin"

    token = user_tokens.get(user_id)
    result = None
    if token:
        result = send_push_notification(token, title, body_text, data={"type": "delivery_time" if approve else "order_denied", "order_id": order_id})

    return {"success": True, "message": "Order status updated", "fcm_result": result, "order": orders[order_id]}


# -----------------------------
# Admin: get all pending orders
# -----------------------------
@router.get("/admin_orders")
def admin_orders():
    pending_orders = [o for o in orders.values() if o["status"] == "pending"]
    return {"success": True, "pending_orders": pending_orders}


# -----------------------------
# User: get all orders
# -----------------------------
@router.get("/user_orders/{user_id}")
def user_orders(user_id: int):
    user_orders_list = [o for o in orders.values() if o["user_id"] == user_id]
    return {"success": True, "orders": user_orders_list}


# Register router
app.include_router(router)
