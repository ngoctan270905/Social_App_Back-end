from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
import redis.asyncio as redis

from app.exceptions.auth import Ban, XacMinhEmail
from app.repositories.user_profile_repository import UserProfileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.upload_repository import UploadRepository
from app.core.security import verify_scoped_token
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
from app.core.redis_client import get_redis_client
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Hàm xác minh người dùng dựa trên token cho mỗi Request
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        redis_client: redis.Redis = Depends(get_redis_client)
) -> Dict[str, Any]:
    user_repo = UserRepository()
    user_profile_repo = UserProfileRepository()
    upload_repo = UploadRepository()

    try:
        # Xác minh token để lấy user_id
        user_id = await verify_scoped_token(
            token,
            required_scope="access_token",
            redis_client=redis_client
        )
        # print(f"User:id {user_id}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Kiểm tra User tồn tại
    user = await user_repo.get_by_id(user_id)
    # print(f"test user{user}")
    # print(f"user_id {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # # Check status cho mỗi request
    if user.get("status") == "pending" or not user.get("email_verified", False):
         raise XacMinhEmail()

    if user.get("status") == "suspended":
         raise Ban()

    # 2. Lấy thông tin cá nhân
    profile = await user_profile_repo.get_by_user_id(user_id)

    avatar_url = None
    if profile and profile.get("avatar"):
        media = await upload_repo.get_by_id(profile["avatar"])
        if media:
            avatar_url = media.get("url")

    full_user_data = {
        "_id": str(user["_id"]),
        "email": user["email"],
        "status": user["status"],
        "created_at": user["created_at"],
        "first_name": profile.get("first_name") if profile else None,
        "last_name": profile.get("last_name") if profile else None,
        "avatar": avatar_url,
    }

    # if "_id" in user:
    #     user["id"] = str(user["_id"])

    return full_user_data




    #
    # return user