import logging
from datetime import datetime

import cloudinary.uploader
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.repositories.upload_repository import UploadRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.media import MediaResponse

logger = logging.getLogger(__name__)

class UploadService:

    def __init__(self, upload_repo: UploadRepository, user_profile_repo: UserProfileRepository):
        self.upload_repo = upload_repo
        self.user_profile_repo = user_profile_repo

    # Giới hạn file type và size
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @staticmethod
    async def upload_image(file: UploadFile, folder: str, media_type: str):
        try:
            # 1. VALIDATE FILE TYPE
            if file.content_type not in UploadService.ALLOWED_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type không hợp lệ. Chỉ chấp nhận: {', '.join(UploadService.ALLOWED_TYPES)}"
                )

            # 2. VALIDATE FILE SIZE
            file_content = await file.read()
            if len(file_content) > UploadService.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File quá lớn. Tối đa {UploadService.MAX_FILE_SIZE / 1024 / 1024}MB"
                )

            # 3. VALIDATE FILE CONTENT (kiểm tra có phải ảnh thật không)
            # Đọc magic bytes để chắc chắn là ảnh
            if not file_content.startswith(b'\xff\xd8\xff') and \
                    not file_content.startswith(b'\x89PNG') and \
                    not file_content.startswith(b'RIFF'):
                raise HTTPException(status_code=400, detail="File không phải ảnh hợp lệ")

            # 4. UPLOAD với nhiều options
            upload_result = await run_in_threadpool(
                cloudinary.uploader.upload,
                file_content,
                folder=f"blog_facebook/{folder}",
                resource_type="image",
                transformation=[
                    {"quality": "auto", "fetch_format": "auto"},
                    {"width": 2000, "height": 2000, "crop": "limit"}
                ],
                allowed_formats=["jpg", "png", "webp"],
            )

            return {
                "type": media_type,
                "public_id": upload_result.get("public_id"),
                "url": upload_result.get("secure_url"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "format": upload_result.get("format"),  # webp, jpg, png
                "bytes": upload_result.get("bytes"),  # Kích thước file
                "privacy": "public"
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Cloudinary upload error: {str(e)}")
            raise HTTPException(status_code=500, detail="Lỗi upload ảnh lên server lưu trữ")

        finally:
            await file.close()

    async def upload(self, file: UploadFile, folder: str, media_type: str, user_id: str) -> MediaResponse:
        # 1. Upload lên Cloudinary
        try:
            upload_result = await self.upload_image(file, folder, media_type)
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
            saved_record = await self.upload_repo.create(media_data)
        except Exception as e:
            logger.error(f"Database save error: {e}")
            # Ở đây có thể thêm logic xóa ảnh trên Cloudinary nếu lưu DB thất bại
            raise HTTPException(status_code=500, detail="Lưu thông tin ảnh vào cơ sở dữ liệu thất bại")

        media_id = saved_record['_id']
        if media_type:
            update_profile = {}
            if media_type == "avatar":
                update_profile = {"avatar": ObjectId(media_id)}
            elif media_type == "cover":
                update_profile = {"cover": ObjectId(media_id)}

            if update_profile:
                try:
                    await self.user_profile_repo.update_by_user_id(
                        user_id,
                        update_profile
                    )
                except Exception as e:
                    logger.error(f"User profile update error: {e}")
                    # Không raise lỗi ở đây để tránh rollback cả quá trình upload thành công trước đó
                    # Hoặc bạn có thể chọn raise tùy logic business

        return MediaResponse(**saved_record)
