import os
import shutil
from datetime import datetime


def save_upload_uploadfile(upload_file, dest_dir: str, prefix: str = "") -> str:
    os.makedirs(dest_dir, exist_ok=True)
    filename = f"{prefix}{int(datetime.utcnow().timestamp())}_{upload_file.filename}"
    dest = os.path.join(dest_dir, filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return dest