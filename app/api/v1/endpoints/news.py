from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.schemas.response import ResponseModel
from app.services.news_service import NewsService
from app.schemas.news import NewsListResponse, NewsCreateResponse, NewsCreate
from app.api.deps import get_news_service

router = APIRouter()


@router.get(
    "/",
    response_model=ResponseModel[List[NewsListResponse]],
    summary="Lấy danh sách tin tức"
)
async def get_news(service: NewsService = Depends(get_news_service)):
    news = await service.get_all_news()
    return ResponseModel(data=news, message="Lấy danh sách bảng tin thành công")


@router.post(
    "/",
    response_model=ResponseModel[NewsCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo tin tức mới"
)
async def create_news(
    news_data: NewsCreate,
    service: NewsService = Depends(get_news_service)
):
    new_news = await service.create_new(news_data)
    return ResponseModel(data=new_news, message="Thêm tin tức thành công")