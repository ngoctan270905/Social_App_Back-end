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


# Thêm bài viết mới ====================================================================================================
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

# Xem chi tiết bài viết ================================================================================================
@router.get("/{post_id}", response_model=ResponseModel[PostDetailResponse], summary="Xem chi tiết bài viết")
async def get_post(
        post_id:str,
        service: PostService = Depends(get_post_service)):

    post = await service.get_detail_post(post_id)
    return ResponseModel(data=post, message="Lấy thông tin bài viết thành công")


# Chỉnh sửa bài viết ===================================================================================================
@router.put("/{post_id}", response_model=ResponseModel[PostCreateResponse], summary="Cập nhật bài viết")
async def update_post(
        post_id: str,
        content: Optional[str] = Form(None),
        privacy: Optional[PostType] = Form(None),
        keep_media_ids: Optional[List[str]] = Form(None),  # Nhận list ID dạng form data
        files: Optional[List[UploadFile]] = File(None),  # Nhận file mới
        service: PostService = Depends(get_post_service),
        current_user: dict = Depends(get_current_user)
):
    # Xử lý trường hợp list gửi lên là None
    if keep_media_ids is None:
        keep_media_ids = []

    updated_post = await service.update_post(
        post_id=post_id,
        user_id=current_user['_id'],
        content=content,
        privacy=privacy,
        keep_media_ids=keep_media_ids,
        new_files=files if files else []
    )

    return ResponseModel(
        data=updated_post,
        message="Cập nhật bài viết thành công"
    )

# Xóa bài viết =========================================================================================================
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa bài viết")
async def delete_post(
        post_id:str,
        service: PostService = Depends(get_post_service),
        current_user: dict = Depends(get_current_user)):

    print(f"id người dùng: {current_user['_id']}")
    post = await service.delete_post(post_id, current_user['_id'])
    return {
        "message": "Xóa bài viết thành công"
    }