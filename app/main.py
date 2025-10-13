import os
from fastapi import FastAPI
from app.db import create_db_and_tables, Session, engine
from app.models import User
from app.auth import get_password_hash
from app.routes import users, stores, products


app = FastAPI(title="Bazario Backend")

app.include_router(users.router)
app.include_router(stores.router)
app.include_router(products.router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    os.makedirs("./uploads", exist_ok=True)
    # Create admin if not exists
    with Session(engine) as session:
        admin = session.exec(
            "SELECT * FROM user WHERE username='meadminBoss'"
        ).first()
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
