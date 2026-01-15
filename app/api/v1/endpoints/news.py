from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from typing import List, Optional

from app.core.dependencies import get_current_user
from app.schemas.response import ResponseModel
from app.services.news_service import PostService
from app.schemas.news import PostCreateResponse, NewsCreate, PostCreate, PostType, PostsListResponse
from app.api.deps import get_post_service

router = APIRouter()


@router.get(
    "/",
    response_model=ResponseModel[List[PostsListResponse]],
    summary="Lấy danh sách bài viết"
)
async def get_news(service: PostService = Depends(get_post_service)):
    posts = await service.get_all_posts()
    return ResponseModel(data=posts, message="Lấy danh sách bảng tin thành công")


@router.post(
    "/",
    response_model=ResponseModel[PostCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bài viết mới"
)
async def create_post(
    content: str = Form(...),
    privacy: PostType = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    service: PostService = Depends(get_post_service),
    current_user: dict = Depends(get_current_user),
):
    post_data = PostCreate(
        content=content,
        privacy=privacy
    )

    created = await service.create_post(
        post_data=post_data,
        files=files,
        user_id=current_user['_id']
    )

    return ResponseModel(
        data=created,
        message="Thêm bài viết thành công"
    )