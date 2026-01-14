import datetime
import logging
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, status, FastAPI, UploadFile

from app.core.websocket import manager
from app.repositories.media_repository import MediaRepository
from typing import List, Optional
from app.schemas.media import MediaResponse
from app.services.upload_service import UploadService


logger = logging.getLogger(__name__)

class MediaService:
    def __init__(self, upload_service: UploadService, media_repo: MediaRepository ) -> None:
        self.upload_service = upload_service
        self.media_repo = media_repo

    async def upload(self, file: UploadFile, folder: str, media_type: str, user_id: str) -> MediaResponse:
        # 1. Upload lên Cloudinary
        try:
            upload_result = await self.upload_service.upload_image(file, folder, media_type)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            raise HTTPException(status_code=500, detail="Có lỗi xảy ra trong quá trình xử lý ảnh")

        media_data = {
            "owner_id": ObjectId(user_id),
            "owner_type": "user",
            "type": upload_result["type"],
            "public_id": upload_result["public_id"],
            "url": upload_result["url"],
            "width": upload_result["width"],
            "height": upload_result["height"],
            "format": upload_result["format"],
            "bytes": upload_result["bytes"],
            "privacy": upload_result["privacy"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # 2. Lưu vào DB
        try:
            saved_record = await self.media_repo.create(media_data)
        except Exception as e:
            logger.error(f"Database save error: {e}")
            raise HTTPException(status_code=500, detail="Lưu thông tin ảnh vào cơ sở dữ liệu thất bại")

        return MediaResponse(**saved_record)
