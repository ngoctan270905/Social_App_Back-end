# Triển khai tính năng: Xóa cuộc trò chuyện (Conversation) và Tin nhắn (Messages)

## 1. Mục tiêu
Cho phép người dùng xóa một cuộc trò chuyện cụ thể. 
**Lưu ý quan trọng:** Hành động này là **Xóa vĩnh viễn (Hard Delete)** khỏi cơ sở dữ liệu. Toàn bộ dữ liệu về cuộc trò chuyện và các tin nhắn bên trong sẽ bị mất hoàn toàn và không thể khôi phục. Không sử dụng cờ `deleted_at`.

## 2. Thiết kế API

*   **Method:** `DELETE`
*   **Endpoint:** `/api/v1/conversations/{conversation_id}`
*   **Authentication:** Yêu cầu đăng nhập (`current_user`).
*   **Response:**
    *   `200 OK`: Xóa thành công.
    *   `404 Not Found`: Không tìm thấy cuộc trò chuyện.
    *   `403 Forbidden`: Người dùng không có quyền xóa (không phải thành viên).

## 3. Luồng dữ liệu (Clean Architecture)

### A. Repository

#### 1. `ConversationRepository` (`app/repositories/conversation_repository.py`)
```python
async def delete(self, conversation_id: str) -> bool:
    result = await self.collection.delete_one({"_id": ObjectId(conversation_id)})
    return result.deleted_count > 0
```

#### 2. `MessageRepository` (`app/repositories/message_repository.py`)
```python
async def delete_by_conversation_id(self, conversation_id: str) -> int:
    result = await self.collection.delete_many({"conversation_id": ObjectId(conversation_id)})
    return result.deleted_count
```

### B. Service (`app/services/conversation_service.py`)
Cập nhật `__init__` để nhận `message_repo` và thêm hàm `delete_conversation`.

```python
class ConversationService:
    def __init__(self, conversation_repo, user_profile_repo, media_repo, message_repo):
        self.conversation_repo = conversation_repo
        self.user_profile_repo = user_profile_repo
        self.media_repo = media_repo
        self.message_repo = message_repo # Thêm mới

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return False
        
        # Check quyền thành viên
        is_participant = any(str(p["user_id"]) == user_id for p in conversation["participants"])
        if not is_participant:
             raise HTTPException(status_code=403, detail="Permission denied")

        # 1. Xóa tất cả tin nhắn
        await self.message_repo.delete_by_conversation_id(conversation_id)
        
        # 2. Xóa cuộc trò chuyện
        return await self.conversation_repo.delete(conversation_id)
```

### C. Endpoint (`app/api/v1/endpoints/conversations.py`)

```python
@router.delete("/{conversation_id}",
    response_model=ResponseModel[dict],
    status_code=status.HTTP_200_OK,
    summary="Xóa cuộc trò chuyện"
)
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service)
):
    success = await service.delete_conversation(
        conversation_id=conversation_id, 
        user_id=str(current_user["_id"])
    )
    
    if not success:
         raise HTTPException(status_code=404, detail="Conversation not found")
        
    return ResponseModel(data={"message": "Conversation and all messages deleted successfully"})
```

## 4. Các bước thực hiện
1.  **Bước 1:** Cập nhật `MessageRepository`: thêm `delete_by_conversation_id` (Đã có trong code hiện tại).
2.  **Bước 2:** Cập nhật `ConversationRepository`: thêm `delete`.
3.  **Bước 3:** Cập nhật `ConversationService`:
    *   Sửa `__init__` nhận `message_repo`.
    *   Thêm hàm `delete_conversation`.
4.  **Bước 4:** Cập nhật `app/api/v1/endpoints/conversations.py` thêm router `DELETE`.