from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Store, Product
from schemas import StoreCreate
from app.auth import get_admin_user

router = APIRouter(prefix="/stores", tags=["stores"])

@router.post("/")
def create_store(store_in: StoreCreate, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    s = Store(**store_in.dict())
    session.add(s)
    session.commit()
    session.refresh(s)
    return {"id": s.id, "name": s.name}

@router.get("/")
def list_stores(session: Session = Depends(get_session)):
    return session.exec(select(Store)).all()

@router.delete("/{store_id}")
def delete_store(store_id: int, session: Session = Depends(get_session), admin=Depends(get_admin_user)):
    store = session.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    products = session.exec(select(Product).where(Product.store_id == store_id)).all()
    if products:
        raise HTTPException(status_code=400, detail="Cannot delete store with products")
    session.delete(store)
    session.commit()
    return {"ok": True}
