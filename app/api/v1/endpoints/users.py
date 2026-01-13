from typing import Annotated
from fastapi import APIRouter, Depends, status

from app.schemas.user import UserChangePasswordRequest, UserResponse
from app.services.user_service import UserService
from app.core.dependencies import get_current_user
from app.api.deps import get_user_service

router = APIRouter()


@router.post("/me/change-password", response_model=UserResponse)
async def change_current_user_password(
    password_data: UserChangePasswordRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[dict, Depends(get_current_user)]
):

    updated_user = await user_service.change_user_password(
        user_id=current_user["_id"],
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )

    return updated_user
