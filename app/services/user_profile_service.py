import datetime
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from typing import List, Optional
from loguru import logger

from app.exceptions.post import NotFoundError
from app.schemas.posts import MediaPublic
from app.schemas.user_profile import UpdateProfileAvatar, UserProfileDetail, UpdateProfileCover

from app.repositories.media_repository import MediaRepository
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository


from app.services.upload_service import UploadService
from app.core.config import settings


class UserProfileService:
    def __init__(self,
             user_profile_repo: UserProfileRepository,
             upload_service: UploadService,
             media_repo: MediaRepository,
             user_repo: UserRepository):
        self.user_profile_repo = user_profile_repo
        self.upload_service = upload_service
        self.media_repo = media_repo
        self.user_repo = user_repo


    async def update_profile_avatar(self, file: UploadFile, user_id: str) -> UpdateProfileAvatar:
        upload_result = await self.upload_service.upload_image(file=file, folder="avatars")
        media = await self.media_repo.create({
            "type": "image",
            "url": upload_result["path"],
            "created_at": datetime.utcnow(),
            "deleted_at": None,
        })

        user_profile = await self.user_profile_repo.update_avatar(
            user_id=user_id,
            avatar_id=media["_id"]
        )

        return UpdateProfileAvatar(
            avatar=MediaPublic(
                id=media["_id"],
                type=media["type"],
                url=f"{settings.SERVER_BASE_URL}/{media['url']}"
            )
        )


    async def update_profile_cover(self, file: UploadFile, user_id: str) -> UpdateProfileCover:
        upload_result = await self.upload_service.upload_image(file=file, folder="covers")
        media = await self.media_repo.create({
            "type": "image",
            "url": upload_result["path"],
            "created_at": datetime.utcnow(),
            "deleted_at": None,
        })

        user_profile = await self.user_profile_repo.update_cover(
            user_id=user_id,
            cover_id=media["_id"]
        )

        return UpdateProfileCover(
            cover=MediaPublic(
                id=media["_id"],
                type=media["type"],
                url=f"{settings.SERVER_BASE_URL}/{media['url']}"
            )
        )


    async def get_profile_by_id(self, user_id: str) -> UserProfileDetail:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError()

        profile_user = await self.user_profile_repo.get_by_user_id(user_id)

        avatar_public = None
        if profile_user["avatar"]:
            media = await self.media_repo.get_by_id(profile_user["avatar"])
            if media:
                avatar_public = MediaPublic(
                    id = media["_id"],
                    type = media["type"],
                    url = f"{settings.SERVER_BASE_URL}/{media['url']}"
                )

        cover_public = None
        if profile_user.get("cover"):
            media = await self.media_repo.get_by_id(profile_user["cover"])
            if media:
                cover_public = MediaPublic(
                    id=media["_id"],
                    type=media["type"],
                    url=f"{settings.SERVER_BASE_URL}/{media['url']}"
                )

        return UserProfileDetail(
            _id=profile_user["_id"],
            avatar=avatar_public,
            cover=cover_public,
            name=profile_user["display_name"]
        )





