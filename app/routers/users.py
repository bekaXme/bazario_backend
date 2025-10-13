from fastapi import APIRouter, Depends
from typing import List
from app.auth import get_admin_user, get_current_user
from app.db import get_session
from sqlmodel import select
from app.models import User
from app.schemas import NotificationOut


router = APIRouter(prefix="/users", tags=["users"])


@router.get('/', response_model=List[dict])
def list_users(session=Depends(get_session), admin=Depends(get_admin_user)):
    users = session.exec(select(User)).all()
    return [{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in users]


@router.get('/me')
def me(current_user=Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "coins": current_user.coins}