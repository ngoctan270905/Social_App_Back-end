import datetime
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from app.core.websocket import manager
from typing import List, Optional
from app.repositories.media_repository import MediaRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.news import MediaPublic
from app.schemas.user_profile import UpdateProfileAvatar
from app.services.upload_service import UploadService
import logging
from loguru import logger


class UserProfileService:
    def __init__(self, user_profile_repo: UserProfileRepository, upload_service: UploadService, media_repo: MediaRepository):
        self.user_profile_repo = user_profile_repo
        self.upload_service = upload_service
        self.media_repo = media_repo


    async def update_profile_avatar(self,file: UploadFile,user_id: str) -> UpdateProfileAvatar:

        # Upload media
        media_data = await self.upload_service.upload_media(
            file=file,
            folder="avatars"
        )

        # Save media
        media = await self.media_repo.create({
            **media_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None,
        })

        media_id = media["_id"]

        user_profile = await self.user_profile_repo.update_avatar(
            user_id=user_id,
            avatar_id=media_id
        )

        return UpdateProfileAvatar(
            avatar=MediaPublic(
                id=media_id,
                type=media["type"],
                url=media["url"]
            )
        )




