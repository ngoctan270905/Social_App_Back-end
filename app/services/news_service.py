import datetime
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, status, UploadFile

from app.core.websocket import manager
from app.repositories.news_repository import PostRepository
from typing import List, Optional
from app.schemas.news import NewsCreate, PostCreate, PostCreateResponse, MediaPublic, \
    PostsListResponse
from app.services.media_service import MediaService


class PostService:
    def __init__(self, post_repo: PostRepository, media_service: MediaService):
        self.post_repo = post_repo
        self.media_service = media_service

    async def get_all_posts(self) -> List[PostsListResponse]:
        posts =await self.post_repo.get_all_posts()
        list_of_posts = []
        for post in posts:
            list_of_posts.append(post)

        return list_of_posts



    async def create_post(
            self,
            post_data: PostCreate,
            files: Optional[List[UploadFile]],
            user_id: str
    ) -> PostCreateResponse:

        post_dict = post_data.model_dump()

        medias = []

        # Upload media nếu có
        if files:
            medias = await self.media_service.upload_many_media_and_save(
                files=files,
                folder="posts",
            )
            post_dict["media_ids"] = [ObjectId(m.id) for m in medias]
        else:
            post_dict["media_ids"] = []

        # Add fields hệ thống
        post_dict.update({
            "user_id": ObjectId(user_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None
        })

        # Save post
        post = await self.post_repo.create(post_dict)

        media_public = [
            MediaPublic(
                id=m.id,
                type=m.type,
                url=m.url,
            )
            for m in medias
        ]

        # Trả response
        return PostCreateResponse(
            _id=post["_id"],
            content=post["content"],
            privacy=post["privacy"],
            media=media_public,
            created_at=post["created_at"]
        )




