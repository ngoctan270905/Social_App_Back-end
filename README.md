# Facebook Clone Backend

## Giới thiệu Dự án

Đây là hệ thống backend được phát triển bằng FastAPI, thiết kế để cung cấp năng lượng cho một nền tảng mạng xã hội tương tự Facebook. Dự án cung cấp một bộ API mạnh mẽ cho việc xác thực người dùng, quản lý hồ sơ, tạo bài đăng, bình luận, trò chuyện theo thời gian thực và thông báo.

### Các Tính năng Chính

*   **Xác thực Người dùng**: Đăng ký, đăng nhập, Quên mật khẩu qua OTP
*   **Hồ sơ Người dùng**: Quản lý và hiển thị thông tin hồ sơ người dùng.
*   **Bài đăng**: Tạo, xem và tương tác với các bài đăng.
*   **Bình luận**: Thêm và quản lý bình luận trên các bài đăng.
*   **Trò chuyện**: Nhắn tin và quản lý cuộc hội thoại theo thời gian thực.
*   **Thông báo**: Hệ thống thông báo theo thời gian thực.


### Công nghệ Sử dụng

*   **Framework**: FastAPI
*   **Ngôn ngữ**: Python
*   **Cơ sở dữ liệu**:
    *   MongoDB
*   **Redis**
*   **Xác thực**: JWT
*   **WebSockets**: Cho các tính năng thời gian thực.

## Cài đặt và Chạy Ứng dụng

Thực hiện các bước sau để thiết lập và chạy dự án trên môi trường cục bộ của bạn.

### 1. Clone Repository

```bash
git clone https://github.com/your-username/facebook-clone-backend.git
cd facebook-clone-backend
```

### 2. Tạo Môi trường ảo và Cài đặt Thư viện

```bash
python -m venv venv
./venv/Scripts/activate # Đối với Windows
source venv/bin/activate # Đối với macOS/Linux
pip install -r requirements.txt
```

### 3. Cấu hình Biến Môi trường (.env)

Tạo một file `.env` tại thư mục gốc của dự án, dựa trên file `.env.example`.

### 4. Cài đặt Cơ sở dữ liệu

#### MongoDB
*   Đảm bảo máy chủ MongoDB đang chạy.
*   Ứng dụng sẽ tự động tạo các collection khi cần thiết.

### 5. Cài đặt Redis

*   Đảm bảo máy chủ Redis đang chạy.

### 6. Khởi chạy Ứng dụng

Để khởi động ứng dụng FastAPI bằng Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Tài liệu API sẽ có sẵn tại `http://localhost:8000/docs` (Swagger UI) hoặc `http://localhost:8000/redoc` (ReDoc).
