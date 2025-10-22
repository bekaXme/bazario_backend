import os
import shutil
from datetime import datetime
from app.db import UPLOAD_DIR

def save_upload_uploadfile(upload_file, dest_dir: str = None, prefix: str = "") -> str:
    """Save an uploaded file to the uploads directory"""
    from app.db import UPLOAD_DIR
    dest_dir = dest_dir or UPLOAD_DIR
    os.makedirs(dest_dir, exist_ok=True)
    filename = f"{prefix}{int(datetime.utcnow().timestamp())}_{upload_file.filename}"
    dest = os.path.join(dest_dir, filename)
    with open(dest, "wb") as buffer:
        import shutil
        shutil.copyfileobj(upload_file.file, buffer)
    return dest

from fastapi import Request

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

    