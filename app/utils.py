import os
import shutil
from datetime import datetime
from app.db import UPLOAD_DIR
from fastapi import Request, UploadFile
from uuid import uuid4


def save_upload_uploadfile(upload_file: UploadFile, upload_dir: str) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid4().int}_{datetime.now().strftime('%Y-%m-%d')}_{upload_file.filename}"
    file_path = os.path.join(upload_dir, filename)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())

    # ✅ Return only the *relative* path (no "./")
    return f"uploads/{filename}"


def product_to_dict(product, request: Request):
    return {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "store_id": product.store_id,
        "created_at": product.created_at,
        "image_path": str(request.url_for("uploads", path=os.path.basename(product.image_path)))
    }

    