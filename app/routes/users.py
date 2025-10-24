from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from app.db import get_session
from app.models import User
from app.schemas import UserCreate, Token
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(user_create: UserCreate, session: Session = Depends(get_session)):
    if session.exec(select(User).where(User.username == user_create.username)).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user_create.password)
    user = User(
        username=user_create.username,
        hashed_password=hashed,
        email=user_create.email,
        phone_number=user_create.phone_number,
        full_name=user_create.full_name
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.username}, expires_delta=expires)
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "coins": current_user.coins,
        "is_admin": current_user.is_admin,
    }

@router.get("/users")
def list_users(session: Session = Depends(get_session), admin: User = Depends(get_admin_user)):
    return session.exec(select(User)).all()