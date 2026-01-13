# Kế hoạch Tối ưu Hiệu năng & Xử lý Ảnh (FastAPI + React)

Tài liệu này mô tả chi tiết các bước cần thực hiện để tối ưu hóa tốc độ tải trang và xử lý ảnh cho dự án mạng xã hội, dựa trên kiến trúc hiện tại (FastAPI serve static files).

## 1. Tối ưu hóa Kết nối & Mạng (Network & Latency)
**Vấn đề:** Trên Windows, việc phân giải DNS `localhost` có thể gây trễ (latency) từ 600ms - 1s do ưu tiên IPv6 `::1` trước IPv4 `127.0.0.1`.

**Giải pháp:**
- [x] **Frontend (Axios):** Đổi `baseURL` từ `localhost` sang `127.0.0.1`.
- [x] **Frontend (Vite):** Cấu hình `vite.config.ts` chạy host `127.0.0.1`.
- [ ] **Backend (.env):** Đổi cấu hình Database và Redis từ `localhost` sang `127.0.0.1`.
  ```env
  MYSQL_SERVER=127.0.0.1
  REDIS_HOST=127.0.0.1
  ```
- [x] **Backend (CORS):** Thêm `http://127.0.0.1:5173` vào danh sách `origins` trong `main.py`.

---

## 2. Xử lý Ảnh đầu vào (Image Processing Pipeline)
**Mục tiêu:** Giảm dung lượng ảnh lưu trữ, giảm băng thông tải xuống, tăng tốc độ load.

**Chiến lược:**
1.  **Không lưu ảnh gốc:** Ảnh gốc từ điện thoại (5-10MB) quá nặng.
2.  **Chuyển đổi sang WebP:** Định dạng WebP nhẹ hơn JPEG/PNG 30-50% chất lượng tương đương.
3.  **Resize:** Giới hạn kích thước tối đa.

**Triển khai (Backend):**
- Sử dụng thư viện `Pillow` (PIL).
- Tạo module `app/utils/image_processing.py`.
- **Logic xử lý:**
  - Avatar: Resize về `300x300`.
  - Bài viết (Post): Resize chiều ngang tối đa `1080px`.
  - Convert: `image.save(path, "WEBP", quality=80)`.
  - Threadpool: Chạy tác vụ xử lý ảnh trong `run_in_threadpool` để không chặn (block) các request khác.

---

## 3. Phân phối Ảnh (Serving Static Files)
**Mục tiêu:** Trình duyệt tải ảnh tức thì từ Cache đĩa cứng (Disk Cache) thay vì tải lại từ Server.

**Cấu hình FastAPI:**
1.  **Mount StaticFiles:**
    ```python
    app.mount("/media", StaticFiles(directory="media"), name="media")
    ```
2.  **Middleware Cache-Control (Quan trọng):**
    Mặc định `StaticFiles` không gửi header cache mạnh. Cần thêm Middleware để báo trình duyệt cache ảnh trong 1 năm.
    ```python
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    ```

---

## 4. Kiểm tra & Giám sát
- **Tab Network (DevTools):**
  - Kiểm tra `Status Code` của ảnh phải là `200` (lần đầu) và `200 (from disk cache)` hoặc `304` (các lần sau).
  - Thời gian phản hồi API `/me` phải dưới `100ms`.
- **Logging:** Theo dõi log của `LoggingMiddleware` ở backend để phát hiện các query DB chậm.
