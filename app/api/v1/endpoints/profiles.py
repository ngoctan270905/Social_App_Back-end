from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Query

from app.schemas.media import MediaResponse, MediaCreate, MediaType
from app.schemas.response import ResponseModel
from app.schemas.user_profile import UpdateProfileAvatar, UserProfileDetail
from app.services.news_service import PostService
from app.services.upload_service import UploadService
from app.services.user_profile_service import UserProfileService
from app.services.user_service import UserService
from app.core.dependencies import get_current_user
from app.api.deps import get_user_service, get_user_profile_service, get_post_service

router = APIRouter()

@router.patch(
    "/avatar",
    response_model=ResponseModel[UpdateProfileAvatar],
    status_code=status.HTTP_201_CREATED,
    summary="Upload Avatar",
)
async def upload_avatar(
        file: UploadFile = File(...),
        service: UserProfileService = Depends(get_user_profile_service),
        user: dict = Depends(get_current_user)
):
    updated_avatar = await service.update_profile_avatar(file=file, user_id=user['_id'])
    return ResponseModel(data=updated_avatar, message="OK")


@router.get("/{user_id}/posts", summary="Lấy danh sách bài viết của một người dùng")
async def get_user_posts(
        user_id: str,
        cursor: Optional[str] = None,
        limit: int = Query(default=5, le=50),
        service: PostService = Depends(get_post_service),
        current_user: dict = Depends(get_current_user)):
    return await service.get_user_posts(
        user_id=user_id,
        current_user_id=current_user["_id"],
        cursor=cursor,
        limit=limit
    )

@router.get("/{user_id}", response_model=ResponseModel[UserProfileDetail], summary="Lấy thông tin profile của người dùng")
async def get_profile_user(
        user_id: str,
        service: UserProfileService = Depends(get_user_profile_service),
        current_user: dict = Depends(get_current_user)):
    profile_user = await service.get_profile_by_id(user_id)
    return ResponseModel(data=profile_user, message="Lấy thông tin user thành công")
