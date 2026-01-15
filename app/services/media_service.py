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

    async def upload_media_and_save(
            self,
            file: UploadFile,
            folder: str
    ) -> MediaResponse:

        # Upload Cloudinary (image hoặc video)
        try:
            upload_result = await self.upload_service.upload_media(
                file=file,
                folder=folder
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Có lỗi xảy ra trong quá trình upload media"
            )

        # Build media document
        media_data = {
            "type": upload_result["type"],
            "public_id": upload_result["public_id"],
            "url": upload_result["url"],
            "format": upload_result["format"],
            "bytes": upload_result["bytes"],
            "width": upload_result.get("width"),
            "height": upload_result.get("height"),
            "duration": upload_result.get("duration"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        print(f"Metadata: {media_data}")

        # Save DB
        try:
            saved = await self.media_repo.create(media_data)
        except Exception as e:
            logger.error(f"Database save error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Lưu media vào DB thất bại"
            )

        return MediaResponse(**saved)

    async def upload_many_media_and_save(
            self,
            files: list[UploadFile],
            folder: str,
    ) -> list[MediaResponse]:

        if not files:
            return []

        results = []

        for file in files:
            media = await self.upload_media_and_save(
                file=file,
                folder=folder
            )
            results.append(media)

        return results


