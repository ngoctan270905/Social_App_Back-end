from typing import Annotated
from fastapi import APIRouter, Depends, status, UploadFile, File, Form

from app.schemas.media import MediaResponse, MediaCreate, MediaType
from app.schemas.response import ResponseModel
from app.schemas.user_profile import UpdateProfileAvatar
from app.services.upload_service import UploadService
from app.services.user_profile_service import UserProfileService
from app.services.user_service import UserService
from app.core.dependencies import get_current_user
from app.api.deps import get_user_service, get_user_profile_service

router = APIRouter()

@router.patch(
    "/avatar",
    response_model=ResponseModel[UpdateProfileAvatar],
    status_code=status.HTTP_201_CREATED,
    summary="Upload Avatar",
)
async def upload_avatar(
        media_id: str,
        service: UserProfileService = Depends(get_user_profile_service),
        user: dict = Depends(get_current_user)
):
    updated_avatar = await service.update_profile(media_id, user_id=user['_id'])
    return ResponseModel(data=updated_avatar, message="OK")