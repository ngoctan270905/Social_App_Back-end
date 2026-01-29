# Kiến Trúc Design Patterns trong Hệ Thống Chat

Tài liệu này phân tích các Mẫu Thiết Kế (Design Patterns) được áp dụng trong module Chat của dự án `my_social_app`.

## 1. Tổng Quan
Hệ thống sử dụng mô hình **Async Monolith** kết hợp với kiến trúc hướng sự kiện (Event-Driven). Hai Design Pattern chủ đạo được sử dụng là:
1.  **Observer Pattern** (Mẫu Quan Sát Viên)
2.  **Publish/Subscribe (Pub/Sub) Pattern** (Mẫu Nhà Xuất Bản/Người Đăng Ký)

Mặc dù có điểm tương đồng, chúng được áp dụng ở hai tầng khác nhau của hệ thống.

---

## 2. Chi Tiết Triển Khai

### A. Publish/Subscribe Pattern (Tầng Hệ Thống - Redis)
Đây là xương sống giúp hệ thống có thể mở rộng (Scalability) và tách rời sự phụ thuộc (Decoupling).

*   **Publisher (Nhà Xuất Bản):** `MessageService`
    *   **Nhiệm vụ:** Khi có tin nhắn mới được lưu vào DB, nó "xuất bản" (publish) sự kiện này ra ngoài.
    *   **Đặc điểm:** Nó không quan tâm ai sẽ nhận tin, nó chỉ biết ném vào một "Kênh" (Channel).
    *   **Code:** `await manager.broadcast_via_redis(...)`

*   **Broker (Người Môi Giới):** `Redis`
    *   **Nhiệm vụ:** Trung chuyển tin nhắn. Nhận tin từ Publisher và chuyển phát cho tất cả những ai đang lắng nghe kênh `chat_broadcast_channel`.

*   **Subscriber (Người Đăng Ký):** `ConnectionManager` (trong `start_listening_redis`)
    *   **Nhiệm vụ:** Đăng ký lắng nghe kênh `chat_broadcast_channel`. Bất cứ khi nào Redis có tin mới, hàm này sẽ được đánh thức để xử lý.

**-> Tại sao dùng?** Để hỗ trợ chạy nhiều Server (Multi-instance). Nếu User A ở Server 1 nhắn tin, User B ở Server 2 vẫn nhận được nhờ Redis trung chuyển.

---

### B. Observer Pattern (Tầng Ứng Dụng - WebSocket)
Đây là cách Server quản lý kết nối trực tiếp với người dùng.

*   **Subject (Chủ Thể):** `ConnectionManager`
    *   **Nhiệm vụ:** Quản lý danh sách các "người quan sát" (WebSocket Connections).
    *   **Dữ liệu:** Biến `self.active_connections: Dict[str, List[WebSocket]]` lưu giữ trạng thái ai đang online.

*   **Observer (Quan Sát Viên):** Các kết nối `WebSocket` của User (Client)
    *   **Nhiệm vụ:** Duy trì kết nối với Server và chờ đợi dữ liệu được gửi xuống.
    *   **Hành động:** Khi `ConnectionManager` nhận được tin từ Redis (hoặc từ logic nội bộ), nó sẽ tìm trong danh sách `active_connections` và gọi phương thức `send_json()` để đẩy dữ liệu xuống cho Observer cụ thể.

**-> Tại sao dùng?** Để quản lý trạng thái Real-time. Server cần biết chính xác socket nào thuộc về user nào để gửi tin đúng đích.

---

## 3. Luồng Chạy Thực Tế (Data Flow)

Ví dụ: **User A** gửi tin nhắn cho **User B**.

1.  **Request (HTTP POST):** User A gọi API `send_message`.
2.  **Database:** `MessageService` lưu tin nhắn vào MongoDB.
3.  **Publisher (Redis Pub/Sub):**
    *   `MessageService` gọi `manager.broadcast_via_redis(["user_B_id"], payload)`.
    *   Tin nhắn được bắn lên kênh Redis `chat_broadcast_channel`.
    *   *API trả về response 200 OK cho User A ngay lập tức.*
4.  **Subscriber (Redis Pub/Sub):**
    *   Task ngầm `start_listening_redis` (đang chạy trên Server) nhận được tín hiệu từ Redis.
    *   Nó đọc payload: "Gửi cho user_B_id nội dung này...".
5.  **Subject (Observer Pattern):**
    *   Hàm `process_redis_message` kiểm tra `self.active_connections`.
    *   Nó thấy: "À, User B đang có kết nối socket tại đây!".
6.  **Notify Observer:**
    *   Server gọi `websocket.send_json(payload)`.
    *   Điện thoại của User B nhận được tin nhắn và hiển thị.

## 4. Tổng Kết
| Thành phần Code | Design Pattern | Vai trò |
| :--- | :--- | :--- |
| `manager.broadcast_via_redis` | **Pub/Sub** | Publisher (Gửi tin đi) |
| `Redis Server` | **Pub/Sub** | Broker (Trung chuyển) |
| `manager.start_listening_redis` | **Pub/Sub** | Subscriber (Nhận tin về) |
| `manager.active_connections` | **Observer** | Danh sách Observers (Quản lý User Online) |
| `websocket.send_json` | **Observer** | Notify (Thông báo cho Client) |
