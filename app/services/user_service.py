from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def change_user_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        # Lấy user từ Mongo
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Kiểm tra password cũ
        if not verify_password(old_password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )

        # Hash password mới
        hashed = hash_password(new_password)

        # Update vào MongoDB
        updated_user = await self.user_repo.update(
            user_id,
            {"hashed_password": hashed}
        )

        # Trả về user mới
        user["hashed_password"] = hashed
        updated_user["id"] = str(updated_user.pop("_id"))
        return updated_user

