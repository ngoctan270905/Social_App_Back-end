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
            "type": "image",
            "path": f"image/{folder}/{filename}"
        }

    async def upload_video(self, file: UploadFile, folder: str) -> dict:
        if not file.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail="File không phải video")

        # tạo đường dẫn
        video_dir = os.path.join(BASE_DIR, "video", folder)
        os.makedirs(video_dir, exist_ok=True)

        # tạo tên
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"

        full_path = os.path.join(video_dir, filename)

        with open(full_path, "wb") as f:
            f.write(await file.read())

        return {
            "type": "video",
            "path": f"video/{folder}/{filename}"
        }

    async def upload_media(self, file: UploadFile, folder: str) -> dict:
        if file.content_type.startswith("image/"):
            return await self.upload_image(file, folder)
        elif file.content_type.startswith("video/"):
            return await self.upload_video(file, folder)
        else:
            raise HTTPException(status_code=400, detail="Định dạng file không được hỗ trợ (chỉ hỗ trợ ảnh và video)")
