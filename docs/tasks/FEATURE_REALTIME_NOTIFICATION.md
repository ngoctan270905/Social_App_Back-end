# Kế hoạch Triển khai Real-time Notification (WebSocket)

Tài liệu này mô tả cách tích hợp WebSocket để gửi thông báo thời gian thực khi có tương tác (Comment/Reply).

## 1. Kiến trúc WebSocket

Sử dụng mô hình **Direct Connection Mapping**:
- Server giữ một `Dict[user_id, List[WebSocket]]`.
- Một User có thể login trên nhiều thiết bị (nhiều socket), nên cần lưu List.

### Flow hoạt động:
1. **Connect**: Client connect tới `ws://domain/api/v1/ws/notifications?token=...`.
2. **Auth**: Server verify token, lấy `user_id`, lưu vào `ConnectionManager`.
3. **Event**:
   - User A comment vào bài User B.
   - `CommentService` -> `NotificationService`.
   - `NotificationService` -> `ConnectionManager.send_to_user(user_id=B, message=...)`.
4. **Receive**: Client của User B nhận JSON, hiển thị Toast/Badge.

---

## 2. Cấu trúc Data (Notification Payload)

Dữ liệu bắn qua WebSocket cần gọn nhẹ:

```json
{
  "type": "NEW_COMMENT", 
  "data": {
    "notification_id": "...",
    "sender": {
      "id": "...",
      "display_name": "User A",
      "avatar": "..."
    },
    "post_id": "...",
    "preview": "Nội dung comment...",
    "created_at": "2026-02-01T..."
  }
}
```

---

## 3. Checklist triển khai

### Bước 1: WebSocket Connection Manager (`app/core/websocket.py`)
- [ ] Hàm `connect(websocket, user_id)`: Lưu socket vào dict theo user_id.
- [ ] Hàm `disconnect(websocket, user_id)`: Xóa socket khi mất kết nối.
- [ ] Hàm `send_personal_message(message, user_id)`: Gửi tin nhắn cho **tất cả** socket của user đó.

### Bước 2: WebSocket Endpoint (`app/api/v1/endpoints/websockets.py`)
- [ ] Tạo endpoint `/notifications`.
- [ ] Xác thực user qua Token (Query Param).
- [ ] Giữ kết nối alive (loop `receive_text`).

### Bước 3: Notification Service (`app/services/notification_service.py`)
- [ ] Inject `ConnectionManager` vào Service.
- [ ] Tạo hàm `create_and_notify(...)`:
    1. Lưu thông báo vào MongoDB (để lưu lịch sử).
    2. **Logic Check**: Nếu `sender_id` != `receiver_id` -> Gọi `manager.send_personal_message`.

### Bước 4: Tích hợp vào Comment Service (`app/services/comment_service.py`)
- [ ] Update `create_comment`:
    - Lấy `post.user_id` (chủ bài viết).
    - Nếu là Reply -> Lấy `parent_comment.user_id` (chủ comment cha).
    - Gọi `notification_service.create_and_notify`.

---

## 4. Lưu ý quan trọng (GEMINI.md)

1.  **Tránh Block**: Việc gửi WebSocket không được làm chậm response của API `create_comment`.
    - *Giải pháp*: Nên dùng `asyncio.create_task(...)` hoặc BackgroundTasks để bắn noti ngầm.
2.  **Self-Notification**: Kiểm tra kỹ điều kiện `if sender_id != receiver_id` để tránh nhận thông báo từ chính mình.
3.  **Error Handling**: Nếu WebSocket gửi lỗi, không được làm gián đoạn logic chính của comment.
