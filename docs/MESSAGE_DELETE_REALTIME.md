# Triển khai Xóa tin nhắn Real-time (Message Deletion)

Tài liệu này hướng dẫn cách tích hợp tính năng xóa tin nhắn đồng bộ thời gian thực giữa người gửi và người nhận.

## 1. Quy trình xử lý (Workflow)

1.  **Client (Sender)**: Nhấn nút "Thu hồi" -> Gọi API `DELETE /conversations/{conv_id}/messages/{msg_id}`.
2.  **Server (Backend)**:
    *   Xác thực quyền sở hữu (chỉ người gửi mới được xóa).
    *   Xóa tin nhắn trong cơ sở dữ liệu (MongoDB).
    *   Bắn một sự kiện WebSocket `message_deleted` kèm theo `message_id` tới tất cả các thành viên trong cuộc trò chuyện thông qua Redis Pub/Sub.
3.  **Client (All Participants)**:
    *   Lắng nghe sự kiện `message_deleted`.
    *   Tìm và xóa tin nhắn có ID tương ứng ra khỏi state hiển thị (UI).

## 2. Chi tiết Backend

### Message Service (`app/services/message_service.py`)
Cập nhật hàm `delete_message` để bắn sự kiện WebSocket:

```python
async def delete_message(self, conversation_id: str, message_id: str, user_id: str) -> bool:
    # 1. Kiểm tra tồn tại và quyền sở hữu
    message = await self.message_repo.get_by_id(message_id)
    if not message or str(message.get("conversation_id")) != conversation_id:
        return False
    if str(message["sender_id"]) != user_id:
        raise ForbiddenError()

    # 2. Thực hiện xóa trong DB
    success = await self.message_repo.delete(message_id)
    if not success:
        return False

    # 3. Bắn Realtime cho các thành viên
    conversation = await self.conversation_repo.get_by_id(conversation_id)
    if conversation and "participants" in conversation:
        payload = {
            "type": "message_deleted",
            "conversation_id": conversation_id,
            "data": {"id": message_id}
        }
        recipient_ids = [str(p["user_id"]) for p in conversation["participants"] if "user_id" in p]
        await manager.broadcast_via_redis(recipient_ids, payload)

    return True
```

## 3. Chi tiết Frontend

### Service gọi API (`chatService.ts`)
```typescript
async deleteMessage(conversationId: string, messageId: string): Promise<void> {
  await axios.delete(`/conversations/${conversationId}/messages/${messageId}`);
}
```

### Xử lý UI và WebSocket (`ChatBox.tsx`)

**Xử lý khi click nút Thu hồi:**
```typescript
onRecall={async () => {
    if (activeConversationId) {
        try {
            await chatService.deleteMessage(activeConversationId, message.id);
            // Xóa local ngay lập tức (Optimistic Update)
            setMessages(prev => prev.filter(m => m.id !== message.id));
        } catch (error) {
            console.error("Failed to delete message:", error);
        }
    }
    setActiveMessageMenuId(null);
}}
```

**Lắng nghe WebSocket đồng bộ cho phía người nhận:**
```typescript
useEffect(() => {
  if (lastMessage && lastMessage.type === 'message_deleted') {
    if (lastMessage.conversation_id === activeConversationId) {
      const deletedMessageId = lastMessage.data.id;
      setMessages(prev => prev.filter(msg => msg.id !== deletedMessageId));
    }
  }
}, [lastMessage, activeConversationId]);
```
