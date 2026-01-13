# Kế hoạch Tích hợp WebSocket: Realtime News Notification (Clean Architecture)

Tài liệu này mô tả chi tiết kiến trúc WebSocket, tập trung vào việc tách biệt logic xử lý kỹ thuật (Core) và giao diện kết nối (Endpoint).

---

## 1. Luồng hoạt động (Workflow)

Hệ thống hoạt động song song 2 cơ chế:
1.  **Broadcast (Chiều xuống):** Server -> All Clients (Thông báo tin mới).
2.  **Interaction (Chiều lên & Phản hồi):** Client -> Server -> Client (Ping/Pong, Xác nhận).

---

## 2. Chi tiết các thành phần (Phân lớp logic)

### A. Tầng lõi: `ConnectionManager` (`app/core/websocket.py`)
Đóng vai trò là "Bộ não" quản lý toàn bộ kỹ thuật WebSocket.

*   **`connect()` / `disconnect()`**: Quản lý danh sách kết nối.
*   **`broadcast()`**: Gửi tin nhắn đồng loạt.
*   **`handle_message()` (MỚI)**: Chứa logic xử lý nội dung tin nhắn gửi từ Client. Việc tách biệt ở đây giúp Endpoint không bị phình to.

```python
async def handle_message(self, websocket: WebSocket, data: str):
    if data == "ping":
        await websocket.send_text("pong")
    else:
        await websocket.send_text(f"Server received: {data}")
```

### B. Tầng giao tiếp: Endpoint (`app/api/v1/endpoints/websockets.py`)
Đóng vai trò là "Người gác cổng", chỉ lo việc thiết lập và duy trì kết nối.

*   Nhận request kết nối.
*   Gọi `manager.connect()`.
*   Trong vòng lặp `while`, nhận dữ liệu và **chuyển ngay** cho `manager.handle_message()` xử lý. Không xử lý logic tại đây.

### C. Tầng nghiệp vụ: `NewsService` (`app/services/news_service.py`)
*   Sau khi tạo tin thành công -> Gọi `manager.broadcast()`.

---

## 3. Tại sao lại xử lý ở ConnectionManager?

1.  **Tái sử dụng:** Nếu sau này bạn có thêm nhiều Endpoint WebSocket khác (VD: `/ws/chat`, `/ws/admin`), bạn có thể dùng chung bộ xử lý hoặc kế thừa từ Manager.
2.  **Dễ bảo trì:** Muốn thay đổi logic phản hồi (Ví dụ: thêm logic lưu log vào DB), bạn chỉ cần sửa ở một nơi duy nhất là Manager.
3.  **Endpoint gọn nhẹ:** Endpoint chỉ tập trung vào nhiệm vụ duy nhất là duy trì kết nối (Single Responsibility Principle).

---

## 4. Hướng dẫn Test (Postman)

1.  **Kết nối:** `ws://localhost:8000/ws/news`
2.  **Gửi lên:** `ping` -> **Nhận về:** `pong` (Do Manager xử lý).
3.  **Gửi lên:** `hello` -> **Nhận về:** `Server received: hello` (Do Manager xử lý).
4.  **Tạo tin mới (API):** -> **Nhận về:** JSON thông báo (Do Service gọi Manager Broadcast).
