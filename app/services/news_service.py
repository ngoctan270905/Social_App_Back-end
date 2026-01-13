import datetime
from datetime import datetime
from fastapi import HTTPException, status

from app.core.websocket import manager
from app.repositories.news_repository import NewRepository
from typing import List, Optional
from app.schemas.news import NewsListResponse, NewsCreate, NewsCreateResponse


class NewsService:
    def __init__(self, news_repo: NewRepository):
        self.news_repo = news_repo


    async def get_all_news(self) -> List[NewsListResponse]:
        news_list_dict = await self.news_repo.get_all_news()

        news = []
        for new in news:
            new_response = NewsListResponse(**new)
            news.append(new_response)

        return news


    # Logic thêm category
    async def create_new(self, new_create: NewsCreate) -> NewsCreateResponse:
        new_dict = new_create.model_dump()
        new_dict['created_at'] = datetime.utcnow()
        new_dict['updated_at'] = datetime.utcnow()
        new_dict['deleted_at'] = None
        create = await self.news_repo.create(new_dict)

        await manager.broadcast({
            "event": "new_post_created",
            "message": "Có bài viết mới"
        })

        return NewsCreateResponse(**create)


