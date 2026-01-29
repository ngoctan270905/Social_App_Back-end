# So Sánh Kiến Trúc Chat System

Tài liệu này so sánh hai mô hình xử lý tin nhắn Real-time bằng biểu đồ Sequence Diagram.

## 1. Luồng Hiện Tại (Phase 1: Redis Pub/Sub)
Đây là cách code hiện tại đang chạy. API Server trực tiếp Publish sự kiện lên Redis.

```mermaid
sequenceDiagram
    autonumber
    actor UserA as Sender (User A)
    participant API as API Server (FastAPI)
    participant DB as MongoDB
    participant Redis as Redis (Pub/Sub)
    actor UserB as Receiver (User B)

    UserA->>API: 1. POST /send_message
    
    activate API
    API->>DB: 2. Lưu tin nhắn
    
    %% Đây là bước Synchronous (Đồng bộ)
    API->>Redis: 3. Publish "New Message"
    
    par Parallel Process (Song song)
        Redis-->>API: 4. Notify Listener (Background Task)
        API->>UserB: 5. WebSocket Send (Realtime)
    and
        API-->>UserA: 6. Response 200 OK
    end
    deactivate API
```

**Nhận xét:**
*   Bước 3 nằm trong luồng xử lý chính của API.
*   User A phải đợi xong bước 3 mới nhận được phản hồi.

---

## 2. Luồng Mục Tiêu (Phase 2: Async Queue - Recommended)
Đây là mô hình "Response trước, xử lý sau" sử dụng Queue (Celery/RabbitMQ).

```mermaid
sequenceDiagram
    autonumber
    actor UserA as Sender (User A)
    participant API as API Server (FastAPI)
    participant DB as MongoDB
    participant Queue as Task Queue (Celery/Redis)
    participant Worker as Worker Process
    participant Redis as Redis (Pub/Sub)
    actor UserB as Receiver (User B)

    UserA->>API: 1. POST /send_message
    
    activate API
    API->>DB: 2. Lưu tin nhắn
    
    %% Bước này cực nhanh, chỉ đẩy task vào hàng đợi
    API->>Queue: 3. Enqueue Task (Send Broadcast)
    
    API-->>UserA: 4. Response 200 OK (Trả về NGAY LẬP TỨC)
    deactivate API

    %% Phần xử lý bất đồng bộ (User A không cần chờ phần này)
    rect rgb(240, 240, 240)
        Note right of Queue: Async Processing
        Worker->>Queue: 5. Pop Task
        activate Worker
        Worker->>Worker: 6. Xử lý logic (Filter, AI check...)
        Worker->>Redis: 7. Publish "New Message"
        deactivate Worker
        
        Redis-->>API: 8. Notify Listener
        API->>UserB: 9. WebSocket Send
    end
```

**Nhận xét:**
*   API trả về ở Bước 4 (ngay sau khi ném task vào Queue).
*   Toàn bộ việc Publish Redis và gửi Socket diễn ra ngầm ở phía sau (trong hộp màu xám).
*   Nếu Redis bị chậm hoặc chết, User A vẫn thấy tin nhắn đã gửi thành công (vì API đã trả về rồi).
