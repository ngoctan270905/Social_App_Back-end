# Kế hoạch Triển khai Unread Badge & Real-time Notification

Tài liệu này mô tả chi tiết cách triển khai tính năng đếm tin nhắn chưa đọc (unread count) và hiển thị badge thông báo Real-time.

## 1. Thiết kế Cơ sở dữ liệu (MongoDB)

Cập nhật cấu trúc document trong collection `conversations`. Mỗi phần tử trong mảng `participants` sẽ có thêm field `unread_count`.

```json
{
  "_id": ObjectId("..."),
  "participants": [
    {
      "user_id": ObjectId("UserA"),
      "unread_count": 0  // Số tin chưa đọc của User A
    },
    {
      "user_id": ObjectId("UserB"),
      "unread_count": 5  // User B có 5 tin nhắn chưa đọc từ User A
    }
  ],
  "last_message": { ... },
  "updated_at": ISODate("...")
}
```

## 2. Quy trình Xử lý (Workflow)

### A. Khi Gửi Tin Nhắn (Send Message)
1.  **Client A** gửi tin nhắn.
2.  **Backend** (`MessageService`):
    *   Lưu tin nhắn vào collection `messages`.
    *   Gọi `ConversationRepository.increment_unread_count(conv_id, sender_id=A)`.
        *   Tăng `unread_count` lên +1 cho tất cả participant ngoại trừ A.
        *   Cập nhật `updated_at` mới nhất.
    *   Gửi WebSocket `new_message` kèm theo thông tin `unread_count` (nếu cần) hoặc Client tự tính.

### B. Khi Người Dùng Mở/Đọc Tin Nhắn (Read Message)
1.  **Client B** mở cửa sổ chat với A (hoặc focus vào cửa sổ đó).
2.  **Client B** gọi API `POST /conversations/{id}/read`.
3.  **Backend**:
    *   Gọi `ConversationRepository.mark_as_read(conv_id, user_id=B)`.
    *   Reset `unread_count` của B trong `participants` về 0.
4.  **Client B**: Cập nhật UI badge về 0.

### C. Real-time Update (WebSocket)
1.  Khi **Client B** nhận được sự kiện `new_message`:
    *   Nếu cửa sổ chat đang mở & focus:
        *   **QUAN TRỌNG:** Sử dụng **Debounce** (ví dụ: 2000ms) để gọi API `mark_as_read`. Tránh việc gọi API liên tục nếu nhận nhiều tin nhắn dồn dập (Spam/Flood), tuân thủ quy tắc chống "Fan-out không kiểm soát" trong GEMINI.md.
    *   Nếu cửa sổ chat đóng/minimized: Tăng biến state `unreadCount` cục bộ lên +1 để hiện badge đỏ.

## 3. Chi tiết Implementation

### Backend

**1. ConversationRepository (`repositories/conversation_repository.py`)**
*   Thêm hàm `increment_unread_count(conversation_id, sender_id)`: Dùng `$inc` và `arrayFilters` để tăng count cho người nhận.
*   Thêm hàm `mark_as_read(conversation_id, user_id)`: Dùng `$set` để reset count về 0.

**2. MessageService (`services/message_service.py`)**
*   Trong hàm `send_message`: Sau khi tạo tin nhắn, gọi `conversation_repo.increment_unread_count`.

**3. API Endpoint (`api/v1/endpoints/conversations.py`)**
*   Thêm API `POST /{conversation_id}/read`.

### Frontend

**1. Types (`types/chat.ts`)**
*   Cập nhật interface `Conversation` để có thêm trường `unread_count`.

**2. Chat Service (`services/chatService.ts`)**
*   Thêm hàm `markAsRead(conversationId)`.

**3. Chat Context/Component**
*   Hiển thị badge đỏ dựa trên `unread_count` trong danh sách chat.
*   Lắng nghe socket `new_message` để tăng count realtime.
*   Gọi `markAsRead` khi `useEffect` kích hoạt việc mở chat box.
