from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from app.schemas.response import ResponseModel
from app.services.news_service import PostService
from app.schemas.news import NewsListResponse, PostCreateResponse, NewsCreate, PostCreate
from app.api.deps import get_post_service

router = APIRouter()


# @router.get(
#     "/",
#     response_model=ResponseModel[List[NewsListResponse]],
#     summary="Lấy danh sách tin tức"
# )
# async def get_news(service: PostService = Depends(get_post_service)):
#     news = await service.get_all_news()
#     return ResponseModel(data=news, message="Lấy danh sách bảng tin thành công")


@router.post(
    "/",
    response_model=ResponseModel[PostCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bài viết mới"
)
async def create_post(
    post_data: PostCreate,
    service: PostService = Depends(get_post_service)
):
    created = await service.create_post(post_data)
    return ResponseModel(data=created, message="Thêm bài viết thành công")