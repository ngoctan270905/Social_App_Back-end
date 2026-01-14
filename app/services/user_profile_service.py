import datetime
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.testing.pickleable import User

from app.core.websocket import manager
from app.repositories.news_repository import NewRepository
from typing import List, Optional

from app.repositories.user_profile_repository import UserProfileRepository
from app.schemas.news import NewsListResponse, NewsCreate, NewsCreateResponse
from app.schemas.user_profile import UpdateProfileAvatar


class UserProfileService:
    def __init__(self, user_profile_repo: UserProfileRepository):
        self.user_profile_repo = user_profile_repo

    async def update_profile(self, media_id: str, user_id:str) -> UpdateProfileAvatar:
        user_profile = await self.user_profile_repo.update_by_user_id(user_id,media_id)
        print(user_profile)
        return UpdateProfileAvatar(**user_profile)



