from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from typing import List
from sqlmodel import select
from app.db import get_session
from app.models import Product
from app.auth import get_admin_user
from app.utils.files import save_upload_uploadfile
from os import environ


UPLOAD_DIR = environ.get('UPLOAD_DIR', './uploads')
router = APIRouter(prefix="/products", tags=["products"])


@router.post('/', response_model=dict)
def create_product(
    title: str = Form(...),
    price: int = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    session=Depends(get_session),
    admin=Depends(get_admin_user),
):
    image_path = None
    if image:
        image_path = save_upload_uploadfile(image, UPLOAD_DIR, prefix='product_')
    p = Product(title=title, price=price, description=description, image_path=image_path)
    session.add(p)
    session.commit()
    session.refresh(p)
    return {"id": p.id, "title": p.title}


@router.get('/', response_model=List[Product])
def list_products(session=Depends(get_session)):
    return session.exec(select(Product)).all()


@router.delete('/{product_id}')
def delete_product(product_id: int, session=Depends(get_session), admin=Depends(get_admin_user)):
    p = session.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail='Not found')
    session.delete(p)
    session.commit()
    return {"ok": True}