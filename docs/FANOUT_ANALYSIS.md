# Phân Tích Cơ Chế Fanout (Phân Tán Tin Nhắn)

Tài liệu này giải thích chi tiết vị trí và cách thức hệ thống "nhân bản" tin nhắn từ 1 người gửi đến N người nhận (Fanout).

## 1. Fanout là gì?
Trong hệ thống chat, **Fanout** là quá trình một tin nhắn đầu vào được nhân bản và chuyển phát tới nhiều đích đến (nhiều user, hoặc nhiều thiết bị của cùng một user).

Ví dụ: User A gửi tin vào nhóm có 100 người. Hệ thống phải thực hiện "Fanout" để 1 tin nhắn đó biến thành 100 thông báo gửi tới 100 socket khác nhau.

## 2. Vị Trí Fanout Trong Code
Hệ thống hiện tại có 2 cấp độ Fanout:

### Cấp độ 1: Fanout giữa các Server (Qua Redis)
*   **Vị trí:** `app/core/websocket.py` -> `broadcast_via_redis`
*   **Cơ chế:** Redis Pub/Sub.
*   **Mô tả:** Khi bạn gọi `redis.publish`, Redis sẽ thực hiện fanout tin nhắn này tới **tất cả** các Server Backend đang lắng nghe (subscribe) kênh đó.
*   **Tính chất:** Rất nhanh, do Redis đảm nhiệm.

### Cấp độ 2: Fanout tới từng User (Trong Code Python) -> **Điểm nghẽn tiềm tàng**
Đây là nơi bạn đang thắc mắc. Nó nằm trong hàm `process_redis_message` tại `app/core/websocket.py`.

```python
async def process_redis_message(self, raw_data: str):
    # ... parse dữ liệu ...
    target_ids = data.get("target_user_ids", []) # Danh sách 100 người nhận

    # === BẮT ĐẦU FANOUT ===
    for user_id in target_ids:  # <--- Vòng lặp 1: Duyệt qua từng người
        if user_id in self.active_connections:
            # <--- Vòng lặp 2: Duyệt qua từng thiết bị (Mobile, Web...) của người đó
            for connection in self.active_connections[user_id]:
                try:
                    # <--- ĐIỂM GỬI TIN (IO Operation)
                    # Nếu dùng 'await' ở đây trong vòng lặp --> BỊ TUẦN TỰ (Sequential)
                    await connection.send_json(payload) 
                except Exception as e:
                    logger.error(...)
    # === KẾT THÚC FANOUT ===
```

## 3. Tại sao nó bị "Tuần tự" (Sequential)?

Trong code cũ (trước khi tối ưu):
1.  Code gặp lệnh `await connection.send_json(payload)`.
2.  Python sẽ **dừng lại** và chờ cho đến khi tin nhắn này được gửi xong (hoặc timeout) mới chạy tiếp vòng lặp.
3.  Nếu gửi cho User 1 mất 0.5s (do mạng lag), thì User 2 phải chờ 0.5s mới bắt đầu được gửi. User 100 phải chờ `99 * 0.5s`.

## 4. Giải pháp: Parallel Fanout (Song song)
Để khắc phục, ta chuyển từ "Gửi xong mới tới người tiếp" sang "Ra lệnh gửi cho tất cả cùng lúc rồi chờ kết quả chung".

Sử dụng `asyncio.gather`:

```python
tasks = []
# Chỉ tạo danh sách công việc (Task), chưa chờ
for user_id in target_ids:
    if user_id in self.active_connections:
        for connection in self.active_connections[user_id]:
            # Thêm công việc vào danh sách
            tasks.append(connection.send_json(payload))

# Bây giờ mới kích hoạt tất cả cùng lúc
# Python sẽ bắn tin đi đồng thời, không cần chờ ông A xong mới tới ông B
if tasks:
    await asyncio.gather(*tasks, return_exceptions=True)
```

## 5. Tóm tắt luồng dữ liệu (Visual)

```text
[User A Gửi] 
     |
     v
[Backend API]
     |
     v
[Redis Pub/Sub]  <--- Fanout Level 1 (Redis làm)
     |
     +---------------------------+
     |                           |
[Server 1]                   [Server 2] ...
     |                           |
[process_redis_message]     [process_redis_message]
     |                           |
     | <--- Fanout Level 2 (Python Loop - Cần tối ưu asyncio.gather)
     |
     +---> [User B - Phone]
     +---> [User B - Web]
     +---> [User C - Web]
     ...
```
