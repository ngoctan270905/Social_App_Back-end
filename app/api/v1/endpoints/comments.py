from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from app.api.deps import get_comment_service
from app.core.dependencies import get_current_user
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.response import ResponseModel
from app.services.comment_service import CommentService

router = APIRouter()

@router.post(
    "/",
    response_model=ResponseModel[CommentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Thêm bình luận mới"
)
async def create_comment(
    data: CommentCreate,
    current_user: dict = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    """
    Tạo một bình luận mới cho bài viết.
    """
    new_comment = await service.create_comment(
        user_id=str(current_user["_id"]),
        data=data
    )

    return ResponseModel(
        data=new_comment,
        message="Bình luận thành công"
    )

@router.get(
    "/{post_id}",
    response_model=ResponseModel[List[CommentResponse]],
    summary="Lấy danh sách bình luận"
)
async def get_comments(
    post_id: str,
    limit: int = Query(default=10, le=100),
    cursor: Optional[str] = Query(None),
    service: CommentService = Depends(get_comment_service)
):
    comments = await service.get_comments_by_post(post_id, limit, cursor)
    return ResponseModel(
        data=comments,
        message="Lấy danh sách bình luận thành công"
    )

@router.get(
    "/{comment_id}/replies",
    response_model=ResponseModel[List[CommentResponse]],
    summary="Lấy danh sách phản hồi của bình luận"
)
async def get_replies(
    comment_id: str,
    limit: int = Query(default=10, le=100),
    cursor: Optional[str] = Query(None),
    service: CommentService = Depends(get_comment_service)
):
    replies = await service.get_replies_by_comment(comment_id, limit, cursor)
    return ResponseModel(
        data=replies,
        message="Lấy danh sách phản hồi thành công"
    )
