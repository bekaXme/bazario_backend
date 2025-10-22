import os
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Request
from sqlmodel import Session, select
from app.db import get_session, UPLOAD_DIR
from app.models import Product, Store
from app.auth import get_admin_user
from app.utils import save_upload_uploadfile, product_to_dict

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

    p = Product(
        title=title,
        price=price,
        description=description,
        store_id=store_id,
        image_path=image_path
    )
    session.add(p)
    session.commit()
    session.refresh(p)

    return product_to_dict(p, request=None)  # Pass None if you don't need URL for this response


@router.get("/")
def list_products(request: Request, store_id: Optional[int] = None, session: Session = Depends(get_session)):
    q = select(Product)
    if store_id:
        q = q.where(Product.store_id == store_id)
    products = session.exec(q).all()
    return [product_to_dict(p, request) for p in products]


@router.get("/{product_id}")
def get_product(product_id: int, request: Request, session: Session = Depends(get_session)):
    p = session.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_dict(p, request)
