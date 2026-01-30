import os
import uuid
import logging
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

BASE_DIR = "resource"


class UploadService:

    async def upload_image(self, file: UploadFile, folder: str) -> dict:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File không phải ảnh")

        # tạo đường dẫn
        image_dir = os.path.join(BASE_DIR, "image", folder)
        os.makedirs(image_dir, exist_ok=True)

        # tạo tên
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"

        full_path = os.path.join(image_dir, filename)

        with open(full_path, "wb") as f:
            f.write(await file.read())

        return {
            "path": f"{folder}/{filename}"
        }
