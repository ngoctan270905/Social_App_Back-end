# Kế hoạch Refactor: Chuyển đổi từ Cloudinary sang Lưu trữ Cục bộ

**Mục tiêu:** Loại bỏ hoàn toàn sự phụ thuộc vào dịch vụ Cloudinary, thay thế bằng giải pháp lưu trữ file (ảnh, video) trực tiếp trên server. Database sẽ chỉ lưu đường dẫn (URL) có thể truy cập được tới file đó.

---

## Các bước thực hiện

### Bước 1: Sửa đổi Logic Upload trong `app/services/upload_service.py`

Đây là bước quan trọng nhất, nơi logic upload lên cloud được thay thế bằng logic lưu file cục bộ.

1.  **Thêm các import cần thiết** ở đầu file:
    ```python
    import aiofiles
    import uuid
    from pathlib import Path
    ```

2.  **Xóa import của Cloudinary:**
    ```python
    # Xóa dòng này
    import cloudinary.uploader
    ```

3.  Trong hàm `upload_media`, **tìm và xóa bỏ hoàn toàn** khối code sau:
    ```python
    # XÓA BỎ KHỐI CODE NÀY
    # Upload Cloudinary
    upload_result = await run_in_threadpool(
        cloudinary.uploader.upload,
        file_content,
        folder=f"blog_facebook/{folder}",
        resource_type=resource_type,
        transformation=(
            [
                {"quality": "auto", "fetch_format": "auto"},
                {"width": 2000, "height": 2000, "crop": "limit"}
            ] if media_type == "image" else None
        ),
        allowed_formats=(
            ["jpg", "png", "webp"]
            if media_type == "image"
            else ["mp4", "mov", "webm"]
        )
    )

    return {
        "type": media_type,
        "public_id": upload_result.get("public_id"),
        "url": upload_result.get("secure_url"),
        # ...
    }
    ```

4.  **Thêm logic mới** vào vị trí vừa xóa để lưu file cục bộ:
    ```python
    # THÊM LOGIC MỚI NÀY
    # Tạo tên file duy nhất và đường dẫn lưu
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # Tổ chức file vào các thư mục con images/videos trong `resource`
    save_dir = Path(f"resource/{resource_type}s") 
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / unique_filename

    # Ghi file vào thư mục (bất đồng bộ)
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(file_content)

    # Trả về thông tin file đã lưu
    # URL là đường dẫn web, không phải đường dẫn hệ thống
    return {
        "type": media_type,
        "public_id": None,  # Không còn public_id từ cloud
        "url": f"/static/{resource_type}s/{unique_filename}", 
    }
    ```

### Bước 2: Cấu hình Phục vụ File Tĩnh trong `app/main.py`

Để trình duyệt có thể truy cập file qua URL, bạn cần "mount" thư mục `resource` thành một đường dẫn tĩnh.

1.  Thêm import `StaticFiles`:
    ```python
    from fastapi.staticfiles import StaticFiles
    ```
2.  Thêm dòng sau khi khởi tạo `app = FastAPI()`:
    ```python
    # Mount thư mục 'resource' vào đường dẫn '/static'
    app.mount("/static", StaticFiles(directory="resource"), name="static")
    ```

### Bước 3: Dọn dẹp Cấu hình và Thư viện

1.  **File `app/core/config.py`:**
    *   Xóa bỏ các biến môi trường liên quan đến Cloudinary:
        ```python
        # Xóa các dòng này
        CLOUDINARY_CLOUD_NAME: str
        CLOUDINARY_API_KEY: int
        CLOUDINARY_API_SECRET: str
        ```

2.  **File `requirements.txt`:**
    *   Xóa dòng `cloudinary`.
    *   Thêm dòng `aiofiles` nếu chưa có.

---

## Kiểm tra sau khi thay đổi

1.  Chạy lại ứng dụng.
2.  Thử chức năng upload avatar.
3.  Kiểm tra xem file ảnh mới có được tạo trong thư mục `resource/images` không.
4.  Kiểm tra trong database (bảng `media`), đảm bảo cột `url` lưu đường dẫn có dạng `/static/images/ten-file-duy-nhat.jpg`.
5.  Kiểm tra trên giao diện xem avatar có hiển thị đúng không.
