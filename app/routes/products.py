import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException
from sqlmodel import Session, select
from app.config import UPLOAD_DIR
from app.db import get_session
from app.models import Product, Store
from app.auth import get_admin_user
from app.utils import save_upload_uploadfile

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/")
def create_product(
    title: str = Form(...),
    price: int = Form(...),
    store_id: int = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    admin=Depends(get_admin_user),
):
    store = session.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    image_path = None
    if image:
        image_path = save_upload_uploadfile(image, UPLOAD_DIR)
    p = Product(title=title, price=price, description=description, store_id=store_id, image_path=image_path)
    session.add(p)
    session.commit()
    session.refresh(p)
    return {"id": p.id, "title": p.title}

@router.get("/")
def list_products(store_id: Optional[int] = None, session: Session = Depends(get_session)):
    q = select(Product)
    if store_id:
        q = q.where(Product.store_id == store_id)
    return session.exec(q).all()

@router.get("/{product_id}")
def get_product(product_id: int, session: Session = Depends(get_session)):
    p = session.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p