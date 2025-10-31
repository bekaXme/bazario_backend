import os
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, Request
from typing import Optional
from sqlmodel import Session, select
from app.db import get_session, UPLOAD_DIR
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

    p = Product(
        title=title,
        price=price,
        description=description,
        store_id=store_id,
        image_path=image_path,
    )
    session.add(p)
    session.commit()
    session.refresh(p)

    return {"id": p.id, "title": p.title}


@router.get("/")
def list_products(request: Request, store_id: Optional[int] = None, session: Session = Depends(get_session)):
    q = select(Product)
    if store_id:
        q = q.where(Product.store_id == store_id)
    products = session.exec(q).all()

    # ✅ Fix image URLs here
    base_url = str(request.base_url).rstrip("/")
    result = []
    for p in products:
        image_url = None
        if p.image_path:
            filename = os.path.basename(p.image_path)
            image_url = f"{base_url}/uploads/{filename}"
        result.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "price": p.price,
            "store_id": p.store_id,
            "created_at": p.created_at,
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