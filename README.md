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
**QUAN TRỌNG**: Thay thế các giá trị placeholder bằng thông tin xác thực và cài đặt thực tế của bạn.

```dotenv
# .env file

# Cấu hình Ứng dụng
PROJECT_NAME="Facebook Clone"
ENVIRONMENT="development"
SERVER_BASE_URL="http://localhost:8000"
CLIENT_BASE_URL="http://localhost:3000" # URL của frontend của bạn

# Cấu hình Cơ sở dữ liệu MySQL
MYSQL_USER="your_mysql_user"
MYSQL_PASSWORD="your_mysql_password"
MYSQL_SERVER="localhost"
MYSQL_PORT=3306
MYSQL_DB="your_mysql_database"

# Cấu hình Cơ sở dữ liệu MongoDB
MONGO_CONNECTION_STRING="mongodb://localhost:27017"
MONGO_DB_NAME="your_mongodb_database"

# Cấu hình JWT
SECRET_KEY="your_jwt_secret_key" # Sử dụng khóa ngẫu nhiên, mạnh
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_SECONDS=2592000 # 30 ngày

# Cấu hình Email (ví dụ: Gmail SMTP)
MAIL_USERNAME="your_email@example.com"
MAIL_PASSWORD="your_email_password" # Hoặc mật khẩu ứng dụng cho Gmail
MAIL_FROM="your_email@example.com"
MAIL_PORT=587
MAIL_SERVER="smtp.gmail.com"
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

# Thông tin xác thực OAuth2
GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"
GITHUB_CLIENT_ID="your_github_client_id"
GITHUB_CLIENT_SECRET="your_github_client_secret"
FACEBOOK_CLIENT_ID="your_facebook_client_id"
FACEBOOK_CLIENT_SECRET="your_facebook_client_secret"

# Cấu hình Redis
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0

# Giới hạn Tốc độ (Rate Limiting)
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT="100/minute"
RATE_LIMIT_AUTH="10/minute"

# Cấu hình Cloudinary
CLOUDINARY_CLOUD_NAME="your_cloudinary_cloud_name"
CLOUDINARY_API_KEY="your_cloudinary_api_key"
CLOUDINARY_API_SECRET="your_cloudinary_api_secret"
```

### 4. Cài đặt Cơ sở dữ liệu

#### MySQL
*   Đảm bảo máy chủ MySQL đang chạy.
*   Tạo cơ sở dữ liệu đã chỉ định trong `MYSQL_DB`.
*   Chạy các migration của Alembic để thiết lập các bảng:
    ```bash
    alembic upgrade head
    ```

#### MongoDB
*   Đảm bảo máy chủ MongoDB đang chạy.
*   Ứng dụng sẽ tự động tạo các collection khi cần thiết.

### 5. Cài đặt Redis

*   Đảm bảo máy chủ Redis đang chạy. Redis được sử dụng cho giới hạn tốc độ, caching và làm broker cho Celery.

### 6. Cài đặt Cloudinary

*   Tạo tài khoản Cloudinary và cấu hình `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, và `CLOUDINARY_API_SECRET` trong file `.env` của bạn.

### 7. Chạy Celery Worker (Tùy chọn, cho các tác vụ nền)

Để chạy các tác vụ nền (ví dụ: gửi email), bạn cần khởi động một Celery worker:

```bash
celery -A app.main.celery_app worker --loglevel=info
```
*(Lưu ý: `app.main.celery_app` có thể cần được điều chỉnh tùy thuộc vào nơi `celery_app` được khởi tạo trong dự án của bạn.)*

### 8. Khởi chạy Ứng dụng

Để khởi động ứng dụng FastAPI bằng Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Tài liệu API sẽ có sẵn tại `http://localhost:8000/docs` (Swagger UI) hoặc `http://localhost:8000/redoc` (ReDoc).
