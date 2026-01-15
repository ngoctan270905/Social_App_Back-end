import logging
from datetime import datetime

import cloudinary.uploader
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.media import MediaResponse

logger = logging.getLogger(__name__)

class UploadService:

    def __init__(self, user_profile_repo: UserProfileRepository):
        self.user_profile_repo = user_profile_repo

    # Giới hạn file type và size
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}

    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    MAX_VIDEO_SIZE = 100 * 1024 * 1024


    async def upload_media(
            self,
            file: UploadFile,
            folder: str,
    ):
        try:
            content_type = file.content_type

            # Detect media type
            if content_type in self.ALLOWED_IMAGE_TYPES:
                media_type = "image"
                max_size = self.MAX_IMAGE_SIZE
                resource_type = "image"

            elif content_type in self.ALLOWED_VIDEO_TYPES:
                media_type = "video"
                max_size = self.MAX_VIDEO_SIZE
                resource_type = "video"

            else:
                raise HTTPException(
                    status_code=400,
                    detail="File không hợp lệ (chỉ hỗ trợ image hoặc video)"
                )

            # Read file
            file_content = await file.read()

            if len(file_content) > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File quá lớn. Tối đa {max_size / 1024 / 1024}MB"
                )

            # Validate image magic bytes
            if media_type == "image":
                if not (
                        file_content.startswith(b'\xff\xd8\xff') or
                        file_content.startswith(b'\x89PNG') or
                        file_content.startswith(b'RIFF')
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="File không phải ảnh hợp lệ"
                    )

            # Upload Cloudinary
            upload_result = await run_in_threadpool(
                cloudinary.uploader.upload,
                file_content,
                folder=f"blog_facebook/{folder}",
                resource_type=resource_type,
                transformation=(
                    [
                        {"quality": "auto", "fetch_format": "auto"},
                        {"width": 2000, "height": 2000, "crop": "limit"}
                    ] if media_type == "image" else None
                ),
                allowed_formats=(
                    ["jpg", "png", "webp"]
                    if media_type == "image"
                    else ["mp4", "mov", "webm"]
                )
            )

            return {
                "type": media_type,
                "public_id": upload_result.get("public_id"),
                "url": upload_result.get("secure_url"),
                "format": upload_result.get("format"),
                "bytes": upload_result.get("bytes"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "duration": upload_result.get("duration"),
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Cloudinary upload error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Lỗi upload media lên server"
            )

        finally:
            await file.close()



