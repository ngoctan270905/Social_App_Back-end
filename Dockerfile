# Sử dụng image Python 3.12 nhẹ làm base image
FROM python:3.12-slim

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Copy file requirements.txt vào container
COPY requirements.txt /app/

# Cài đặt các package Python cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code vào container
COPY . /app

# Copy script entrypoint để chạy migration + start server
COPY entrypoint.sh /app/entrypoint.sh

# Cấp quyền thực thi cho entrypoint
RUN chmod +x /app/entrypoint.sh

# Khi container start, chạy entrypoint.sh
# entrypoint.sh sẽ:
# 1. Chờ DB sẵn sàng
# 2. Chạy Alembic migrations
# 3. Start Uvicorn server
CMD ["/app/entrypoint.sh"]
