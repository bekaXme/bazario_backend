from fastapi import FastAPI
from sqlmodel import SQLModel, Session, select
from app.db import get_session, engine, UPLOAD_DIR
from app.models import User
from app.auth import get_password_hash
from app.routes import users, stores, products, orders, coins, cart
import os
from fastapi.staticfiles import StaticFiles



app = FastAPI(title="Bazario Backend")

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# Include routers
app.include_router(users.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(coins.router)
app.include_router(cart.router)

@app.on_event("startup")
async def on_startup():
    SQLModel.metadata.create_all(engine)
    os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure upload dir exists
    with next(get_session()) as session:
        admin = session.exec(select(User).where(User.username == "meadminBoss")).first()
        if not admin:
            u = User(
                username="meadminBoss",
                hashed_password=get_password_hash("MuslimbekMalika32@"),
                full_name="Main Admin",
                is_admin=True,
                email="admin@bazario.com"
            )
            session.add(u)
            session.commit()
            print("✅ Admin user created: meadminBoss / MuslimbekMalika32@")

@app.get("/")
def root():
    return {"message": "Welcome to Bazario Backend API"}
