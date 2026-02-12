from datetime import datetime
from typing import Optional, Dict, Any, Coroutine
from app.core.mongo_database import mongodb_client
import hashlib

class TokenRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db["refresh_tokens"]

    # băm mã refresh token
    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    # thêm refresh token
    async def create_refresh_token(self, refresh_token: str, user_id: str, expires_at: datetime) -> str:
        # gọi hash_token để băm mã refresh token ra
        hashed_token = self._hash_token(refresh_token)
        # tìm mã refresh token trong db xem đã có chưa
        existing = await self.get_refresh_token(refresh_token)
        if existing: # nếu đã có mã refresh token
            raise ValueError("Đã phát hiện xung đột mã refresh token. vui lòng thử lại")

        new_refresh_token = {
            "token": hashed_token,
            "user_id": user_id,
            "expires_at": expires_at
        }
        await self.collection.insert_one(new_refresh_token)
        return refresh_token


    # Thao tác với DB tìm mã refresh_token
    async def get_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        hashed_token = self._hash_token(token) # băm token trước
        refresh_token = await self.collection.find_one({"token": hashed_token})
        return refresh_token


    # thu hồi refresh token
    async def revoke_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        token_obj = await self.get_refresh_token(token)
        if token_obj:
            await self.collection.update_one(
                {"_id": token_obj['_id']},
                {"$set": {"revoked_at": datetime.utcnow()}}
            )
            # trả về token đã bị thu hồi (cập nhật revoked_at)
            token_obj['revoked_at'] = datetime.utcnow()
            return token_obj
        return None

    # Xóa refresh token
    async def delete_refresh_token(self, token: str) -> bool:
        hashed_token = self._hash_token(token)
        result = await self.collection.delete_one({"token": hashed_token})
        return result.deleted_count > 0

    # Xóa refresh token đã hết hạn
    async def delete_expired_tokens(self) -> int:
        now = datetime.utcnow()
        result = await self.collection.delete_many({"expires_at": {"$lte": now}})
        return result.deleted_count
