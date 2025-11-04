from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Delivery Location API")

router = APIRouter(prefix="/location", tags=["Location"])

# Simulate a simple in-memory "database"
USER_LOCATIONS: Dict[str, dict] = {}
DELIVERY_TIMES: Dict[str, str] = {}

# Request models
class LocationRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float

class DeliveryTimeRequest(BaseModel):
    user_id: str
    order_id: str
    delivery_time: str  

# 1️⃣ User sends location (from Yandex Map)
@router.post("/send")
def send_location(data: LocationRequest):
    USER_LOCATIONS[data.user_id] = {
        "latitude": data.latitude,
        "longitude": data.longitude
    }

    # In a real app, you could notify admin here via Telegram bot or dashboard
    print(f"📍 User {data.user_id} location: {data.latitude}, {data.longitude}")

    return {
        "status": "success",
        "message": "Location received and sent to admin",
        "data": USER_LOCATIONS[data.user_id]
    }

# 2️⃣ Admin checks user location
@router.get("/user/{user_id}")
def get_user_location(user_id: str):
    location = USER_LOCATIONS.get(user_id)
    if not location:
        raise HTTPException(status_code=404, detail="User location not found")

    return {
        "status": "success",
        "data": location
    }

# 3️⃣ Admin sends delivery time
@router.post("/delivery-time")
def set_delivery_time(data: DeliveryTimeRequest):
    if data.user_id not in USER_LOCATIONS:
        raise HTTPException(status_code=404, detail="User location not found")

    DELIVERY_TIMES[data.user_id] = data.delivery_time

    print(f"⏰ Admin set delivery time for {data.order_id}: {data.delivery_time}")

    return {
        "status": "success",
        "message": f"Delivery time set to {data.delivery_time} for user {data.user_id}"
    }

# 4️⃣ User checks delivery time
@router.get("/delivery-time/{order_id}")
def get_delivery_time(order_id: str):
    delivery_time = DELIVERY_TIMES.get(order_id)
    if not delivery_time:
        raise HTTPException(status_code=404, detail="Delivery time not set yet")

    return {
        "status": "success",
        "delivery_time": delivery_time
    }
