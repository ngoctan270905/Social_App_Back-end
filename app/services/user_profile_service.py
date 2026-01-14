import datetime
from datetime import datetime
from fastapi import HTTPException, status
from app.core.websocket import manager
from typing import List, Optional
from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.user_profile import UpdateProfileAvatar


class UserProfileService:
    def __init__(self, user_profile_repo: UserProfileRepository):
        self.user_profile_repo = user_profile_repo

    async def update_profile(self, media_id: str, user_id:str) -> UpdateProfileAvatar:
        user_profile = await self.user_profile_repo.update_by_user_id(user_id,media_id)
        print(user_profile)
        return UpdateProfileAvatar(**user_profile)



