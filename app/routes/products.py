import os
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Request
from typing import Optional
from sqlmodel import Session, select
from app.db import get_session, UPLOAD_DIR
from app.models import Product, Store
from app.auth import get_admin_user, get_current_user
from app.utils import save_upload_uploadfile

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/")
def create_product(
    title_in_uzb: str = Form(...),
    title_in_rus: str = Form(...),
    title_in_eng: str = Form(...),
    price: int = Form(...),
    store_id: int = Form(...),
    description_in_uzb: Optional[str] = Form(None),
    description_in_rus: Optional[str] = Form(None),
    description_in_eng: Optional[str] = Form(None),
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
        title_in_uzb=title_in_uzb,
        title_in_rus=title_in_rus,
        title_in_eng=title_in_eng,

        description_in_uzb=description_in_uzb,
        description_in_rus=description_in_rus,
        description_in_eng=description_in_eng,

        price=price,
        store_id=store_id,
        image_path=image_path,
    )

    session.add(p)
    session.commit()
    session.refresh(p)

    return {
        "id": p.id,
        "title_in_uzb": p.title_in_uzb,
        "title_in_rus": p.title_in_rus,
        "title_in_eng": p.title_in_eng,
        "description_in_uzb": p.description_in_uzb,
        "description_in_rus": p.description_in_rus,
        "description_in_eng": p.description_in_eng,
        "price": p.price,
        "store_id": p.store_id,
        "image_path": p.image_path,
    }


def product_by_language(product, language):
    if language == 0:
        return product.title_in_uzb, product.description_in_uzb
    elif language == 1:
        return product.title_in_rus, product.description_in_rus
    else:
        return product.title_in_eng, product.description_in_eng


@router.get("/")
def list_products(
    request: Request,
    store_id: Optional[int] = None,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    q = select(Product)
    if store_id:
        q = q.where(Product.store_id == store_id)

    products = session.exec(q).all()
    base_url = str(request.base_url).rstrip("/")

    result = []
    for p in products:
        title, description = product_by_language(p, user.language)

        image_url = None
        if p.image_path:
            image_url = f"{base_url}/uploads/{os.path.basename(p.image_path)}"

        result.append({
            "id": p.id,
            "title": title,
            "description": description,
            "price": p.price,
            "store_id": p.store_id,
            "image_url": image_url,
        })

    return result


@router.get("/{product_id}")
def get_product(product_id: int, request: Request, session: Session = Depends(get_session)):
    p = session.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    base_url = str(request.base_url).rstrip("/")
    image_url = None
    if p.image_path:
        filename = os.path.basename(p.image_path)
        image_url = f"{base_url}/uploads/{filename}"

    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "store_id": p.store_id,
        "created_at": p.created_at,
        "image_url": image_url,
    }


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    admin=Depends(get_admin_user),
):
    p = session.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(p)
    session.commit()

    return {"status": "success", "message": "Product deleted"}