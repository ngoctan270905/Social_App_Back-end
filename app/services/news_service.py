import datetime
from datetime import datetime
from fastapi import HTTPException, status

from app.core.websocket import manager
from app.repositories.news_repository import PostRepository
from typing import List, Optional
from app.schemas.news import NewsListResponse, NewsCreate, PostCreate, PostCreateResponse


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo


    # async def get_all_news(self) -> List[NewsListResponse]:
    #     news_list_dict = await self.news_repo.get_all_news()
    #
    #     news = []
    #     for new in news:
    #         new_response = NewsListResponse(**new)
    #         news.append(new_response)
    #
    #     return news


    # Logic thêm category
    async def create_post(self, post_data: PostCreate) -> PostCreateResponse:
        post_dict = post_data.model_dump()
        post_dict['created_at'] = datetime.utcnow()
        post_dict['updated_at'] = datetime.utcnow()
        post_dict['deleted_at'] = None

        create = await self.post_repo.create(post_dict)

        # await manager.broadcast({
        #     "event": "new_post_created",
        #     "message": "Có bài viết mới"
        # })

        return PostCreateResponse(**create)


