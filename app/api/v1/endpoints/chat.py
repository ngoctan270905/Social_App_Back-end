from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional

from app.core.dependencies import get_current_user

from app.schemas.response import ResponseModel
from app.schemas.posts import PostCreateResponse, PostCreate, PostType, PostsListResponse, \
    PaginatedPostsResponse, PostDetailResponse

from app.services.news_service import PostService
from app.api.deps import get_post_service

router = APIRouter()

# GET lấy danh sách bài viết ===========================================================================================
@router.get("/", summary="Lấy danh sách bài viết")
async def get_news(
        cursor: Optional[str] = None,
        limit: int = Query(default=5, le=50),
        service: PostService = Depends(get_post_service)):

    posts = await service.get_all_posts(cursor=cursor, limit=limit)
    return posts