# Triển khai tính năng: Xóa một tin nhắn (Single Message)

## 1. Mục tiêu
Cho phép người dùng xóa một tin nhắn cụ thể mà họ đã gửi trong cuộc trò chuyện.

## 2. Thiết kế API

*   **Method:** `DELETE`
*   **Endpoint:** `/api/v1/conversations/{conversation_id}/messages/{message_id}`
*   **Authentication:** Yêu cầu đăng nhập (`current_user`).
*   **Response:**
    *   `200 OK`: Xóa thành công.
    *   `404 Not Found`: Không tìm thấy tin nhắn.
    *   `403 Forbidden`: Người dùng không có quyền xóa (không phải là người gửi tin nhắn này).

## 3. Luồng dữ liệu (Clean Architecture)

### A. Repository (`app/repositories/message_repository.py`)
Thêm phương thức xóa tin nhắn theo ID.

```python
async def delete(self, message_id: str) -> bool:
    """
    Xóa document tin nhắn theo ID.
    """
    result = await self.collection.delete_one({"_id": ObjectId(message_id)})
    return result.deleted_count > 0

async def get_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
    return await self.collection.find_one({"_id": ObjectId(message_id)})
```

### B. Service (`app/services/message_service.py`)
Logic kiểm tra quyền sở hữu tin nhắn.

```python
async def delete_message(self, conversation_id: str, message_id: str, user_id: str) -> bool:
    # 1. Lấy thông tin tin nhắn
    message = await self.message_repo.get_by_id(message_id)
    if not message:
        return False
        
    # 2. Kiểm tra xem tin nhắn có thuộc về conversation_id không (để an toàn)
    if str(message.get("conversation_id")) != conversation_id:
        return False

    # 3. Kiểm tra quyền: Chỉ người gửi (sender_id) mới được xóa
    if str(message["sender_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )

    # 4. Thực hiện xóa
    return await self.message_repo.delete(message_id)
```

### C. Endpoint (`app/api/v1/endpoints/conversations.py` hoặc `messages.py`)
Vì endpoint có dạng `/conversations/...`, nên đặt trong `conversations.py` là hợp lý.

```python
@router.delete("/{conversation_id}/messages/{message_id}",
    response_model=ResponseModel[dict],
    status_code=status.HTTP_200_OK,
    summary="Xóa tin nhắn"
)
async def delete_message(
    conversation_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    success = await message_service.delete_message(
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=str(current_user["_id"])
    )
    
    if not success:
         raise HTTPException(status_code=404, detail="Message not found")
        
    return ResponseModel(data={"message": "Message deleted successfully"})
```

## 4. Các bước thực hiện
1.  **Bước 1:** Cập nhật `MessageRepository`: thêm hàm `delete` và `get_by_id` (nếu chưa có).
2.  **Bước 2:** Cập nhật `MessageService`: thêm hàm `delete_message`.
3.  **Bước 3:** Cập nhật Router: thêm endpoint DELETE message.