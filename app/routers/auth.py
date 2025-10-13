from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from app.db import get_session
from app.models import User
from app.schemas import Token
from app.auth import verify_password, create_access_token, get_password_hash


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: dict, session=Depends(get_session)):
    username = payload.get("username")
    password = payload.get("password")
    phone_number = payload.get("phoneNumber")
    full_name = payload.get("full_name", "")
    email = payload.get("email", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="username taken")

    hashed_password = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password,
                full_name=full_name, email=email)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"id": user.id, "username": user.username}



@router.post('/token', response_model=Token)
def token(form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail='Incorrect username or password')
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}