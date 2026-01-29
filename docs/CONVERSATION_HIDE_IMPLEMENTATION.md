# Kế hoạch Triển khai tính năng Ẩn/Hiện Cuộc trò chuyện

Tài liệu này mô tả các bước cần thiết để triển khai tính năng cho phép người dùng ẩn một cuộc trò chuyện khỏi danh sách của họ và hiện lại nó khi họ chủ động truy cập lại.

## Mục tiêu

- Người dùng có thể "xóa bản sao" (ẩn) một cuộc trò chuyện.
- Cuộc trò chuyện đã ẩn sẽ không xuất hiện trong danh sách chat của người dùng.
- Khi người dùng bấm nút "Nhắn tin" trên trang cá nhân của người khác, cuộc trò chuyện đã ẩn (nếu có) sẽ được "hồi sinh" và hiển thị lại đầy đủ lịch sử.

## Các bước triển khai

### 1. Cập nhật Schema (`app/schemas/conversation.py`)

- Định nghĩa một Pydantic model mới là `DeletedBy` để lưu trữ thông tin người dùng đã ẩn và thời điểm họ ẩn.
- Thêm trường `deleted_by: List[DeletedBy] = []` vào các model `ConversationResponse`, `ConversationCreateResponse` và `ConversationListItem` để dữ liệu này được nhất quán trên toàn hệ thống.

```python
# app/schemas/conversation.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .utils import ObjectIdStr

# ... các class khác

class DeletedBy(BaseModel):
    user_id: ObjectIdStr
    deleted_at: datetime

class ConversationResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    participants: List[ParticipantEmbedded]
    is_group: bool = False
    deleted_by: List[DeletedBy] = [] # <--- Thêm vào
    created_at: datetime
    updated_at: Optional[datetime] = None

# ... cập nhật tương tự cho các class Response khác nếu cần
```

### 2. Cập nhật Repository Layer (`app/repositories/conversation_repository.py`)

Lớp này cần các phương thức mới để thao tác với trạng thái "ẩn" trong database.

```python
# app/repositories/conversation_repository.py

from datetime import datetime, timezone
# ... các import khác

class ConversationRepository:
    # ... các phương thức hiện có

    # Sửa đổi phương thức này
    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        user_obj_id = ObjectId(user_id)
        query = {
            "participants.user_id": user_obj_id,
            "deleted_by.user_id": {"$ne": user_obj_id} # <--- Thêm điều kiện lọc
        }
        cursor = self.collection.find(query).sort("updated_at", -1)
        return await cursor.to_list(length=1000)

    # Thêm phương thức mới
    async def hide_for_user(self, conversation_id: str, user_id: str) -> bool:
        """Thêm user vào danh sách đã ẩn của một conversation."""
        delete_record = {
            "user_id": ObjectId(user_id),
            "deleted_at": datetime.now(timezone.utc)
        }
        # Dùng $pull để xóa record cũ (nếu có) trước khi push để tránh trùng lặp
        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$pull": {"deleted_by": {"user_id": ObjectId(user_id)}}}
        )
        # Dùng $push để thêm record mới
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$push": {"deleted_by": delete_record}}
        )
        return result.modified_count > 0

    # Thêm phương thức mới
    async def resurrect_for_user(self, conversation_id: str, user_id: str) -> bool:
        """Xóa user khỏi danh sách đã ẩn của một conversation."""
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$pull": {"deleted_by": {"user_id": ObjectId(user_id)}}}
        )
        return result.modified_count > 0
```

### 3. Cập nhật Service Layer (`app/services/conversation_service.py`)

Lớp service sẽ chứa logic nghiệp vụ chính.

```python
# app/services/conversation_service.py

# ... các import khác
from app.exceptions.base import ForbiddenError, NotFoundError

class ConversationService:
    # ... __init__ và các phương thức khác

    # Thêm phương thức mới
    async def hide_conversation_for_user(self, conversation_id: str, user_id: str) -> bool:
        """Service để ẩn một cuộc trò chuyện cho user."""
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise NotFoundError("Conversation not found")

        # Kiểm tra user có phải là thành viên của cuộc trò chuyện không
        is_participant = any(
            str(p["user_id"]) == user_id for p in conversation.get("participants", [])
        )
        if not is_participant:
            raise ForbiddenError("You are not a participant of this conversation")

        return await self.conversation_repo.hide_for_user(conversation_id, user_id)


    # Sửa đổi phương thức này
    async def find_or_create_private_conversation(
            self,
            user_id: str,
            target_user_id: str
    ) -> ConversationResponse:
        
        # 1. Tìm cuộc trò chuyện đã tồn tại
        conversation_doc = await self.conversation_repo.find_direct_conversation_between_users(
            user_id, target_user_id
        )

        # 2. Nếu tìm thấy:
        if conversation_doc:
            conversation_id = str(conversation_doc["_id"])

            # Kiểm tra xem người dùng hiện tại có đang ẩn nó không
            is_hidden = any(
                str(item["user_id"]) == user_id for item in conversation_doc.get("deleted_by", [])
            )

            # Nếu có, "hồi sinh" nó
            if is_hidden:
                await self.conversation_repo.resurrect_for_user(conversation_id, user_id)
            
            # Trả về chi tiết cuộc trò chuyện (hàm _get_existing_private_conversation đã làm việc này)
            # Ta có thể refactor lại để gọi một hàm build response chung
            return await self._get_existing_private_conversation(user_id, target_user_id)

        # 3. Nếu không tìm thấy, tạo mới
        return await self._create_private_conversation(user_id, target_user_id)
```

### 4. Cập nhật API Layer (`app/api/v1/endpoints/conversations.py`)

Đây là lớp giao tiếp cuối cùng với client.

```python
# app/api/v1/endpoints/conversations.py

# ... các import khác

# Thêm endpoint mới
@router.delete("/{conversation_id}/me",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Ẩn cuộc trò chuyện (xóa bản sao)"
               )
async def hide_conversation_for_oneself(
        conversation_id: str,
        current_user: dict = Depends(get_current_user),
        service: ConversationService = Depends(get_conversation_service)
):
    """
    Ẩn một cuộc trò chuyện khỏi danh sách của người dùng hiện tại.
    Cuộc trò chuyện vẫn tồn tại và hiển thị với những người khác.
    """
    await service.hide_conversation_for_user(
        conversation_id=conversation_id,
        user_id=str(current_user["_id"])
    )
    return None


# Endpoint `POST /conversations` ("Tìm hoặc Tạo") không cần thay đổi code ở đây
# vì logic đã được cập nhật trong service.

# Endpoint `GET /` (Lấy danh sách) không cần thay đổi code ở đây
# vì logic lọc đã được cập nhật trong repository.
```
