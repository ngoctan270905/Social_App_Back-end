# Kế hoạch: Xây dựng Hệ thống Lưu trữ File Linh hoạt (Strategy Pattern)

**Mục tiêu:** Thiết kế lại module upload để có thể dễ dàng chuyển đổi giữa các nhà cung cấp dịch vụ lưu trữ (ví dụ: `local` server, `S3`) thông qua một biến cấu hình duy nhất, mà không cần thay đổi code logic ở tầng service.

---

## Các bước thực hiện

### Bước 1: Cập nhật Cấu hình (`app/core/config.py`)

Thêm một biến mới để xác định "kho" lưu trữ mặc định. Đồng thời, thêm các cấu hình cho S3 để chuẩn bị sẵn.

```python
class Settings(BaseSettings):
    # ... các cấu hình hiện tại ...

    # Cấu hình lưu trữ
    STORAGE_PROVIDER: str = "local"  # Có thể đổi thành "s3"
    
    # (Tùy chọn) Cấu hình cho AWS S3
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: Optional[str] = None

    # ...
```

### Bước 2: Định nghĩa "Khuôn mẫu" Lưu trữ (Interface)

Tạo một file mới `app/services/storage/base.py` để định nghĩa cấu trúc chung mà mọi "kho" lưu trữ phải tuân theo.

```python
# app/services/storage/base.py

from abc import ABC, abstractmethod
from fastapi import UploadFile

class StorageInterface(ABC):
    """
    Khuôn mẫu (Interface) cho tất cả các dịch vụ lưu trữ.
    Mọi class lưu trữ (Local, S3) đều phải kế thừa và triển khai các phương thức này.
    """
    @abstractmethod
    async def upload(
        self, 
        file: UploadFile, 
        file_name: str, 
        folder: str
    ) -> str:
        """
        Tải file lên và trả về URL công khai có thể truy cập.
        
        :param file: Đối tượng UploadFile từ FastAPI.
        :param file_name: Tên file duy nhất đã được tạo.
        :param folder: Thư mục con để lưu file (ví dụ: 'avatars', 'posts').
        :return: URL công khai của file.
        """
        pass

    @abstractmethod
    async def delete(self, file_url: str):
        """
        Xóa một file dựa trên URL của nó.
        """
        pass
```
*(Lưu ý: Bạn cần tạo thư mục `app/services/storage/` và file `__init__.py` bên trong nó)*

### Bước 3: Triển khai Kho "Local"

Tạo file `app/services/storage/local.py` để triển khai việc lưu file trên server.

```python
# app/services/storage/local.py

import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from .base import StorageInterface

class LocalStorage(StorageInterface):
    def __init__(self, base_directory: str = "resource"):
        self.base_directory = Path(base_directory)

    async def upload(
        self, 
        file: UploadFile, 
        file_name: str, 
        folder: str
    ) -> str:
        save_dir = self.base_directory / folder
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / file_name

        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi lưu file cục bộ: {e}"
            )
        
        # Trả về URL có thể truy cập qua web
        return f"/static/{folder}/{file_name}"

    async def delete(self, file_url: str):
        # ... (Logic xóa file cục bộ sẽ được triển khai sau)
        pass
```

### Bước 4: (Tùy chọn) Triển khai Kho "S3"

Tạo file `app/services/storage/s3.py` để triển khai việc lưu file lên AWS S3.

```python
# app/services/storage/s3.py

# Cần cài đặt: pip install boto3 aiobotocore
from .base import StorageInterface
from fastapi import UploadFile, HTTPException, status
# ... (code logic dùng boto3 để upload, cần cấu hình access key, secret key, bucket)

class S3Storage(StorageInterface):
    def __init__(self, access_key, secret_key, bucket_name, region):
        # Khởi tạo S3 client
        pass

    async def upload(
        self, 
        file: UploadFile, 
        file_name: str, 
        folder: str
    ) -> str:
        # Logic upload file lên S3
        # Trả về URL của file trên S3
        return "URL_S3_CUA_FILE"

    async def delete(self, file_url: str):
        pass
```

### Bước 5: Tạo "Nhà máy" (Factory) để chọn kho

Tạo một factory trong `app/api/deps.py` để tự động chọn đúng "kho" dựa trên cấu hình.

```python
# app/api/deps.py

# ... các import khác ...
from app.core.config import settings
from app.services.storage.base import StorageInterface
from app.services.storage.local import LocalStorage
from app.services.storage.s3 import S3Storage

def get_storage_service() -> StorageInterface:
    """
    Factory để lấy ra instance của Storage Service dựa trên cấu hình.
    """
    provider = settings.STORAGE_PROVIDER
    if provider == "local":
        return LocalStorage()
    elif provider == "s3":
        return S3Storage(
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.S3_REGION
        )
    else:
        raise ValueError(f"Nhà cung cấp lưu trữ không hợp lệ: {provider}")

# ... (sửa get_upload_service để inject storage_service)
```

### Bước 6: Refactor `UploadService` để sử dụng "Kho"

Sửa `app/services/upload_service.py` để nó không còn chứa logic upload trực tiếp nữa, mà chỉ điều phối và sử dụng "kho" đã được inject.

```python
# app/services/upload_service.py

# ... imports ...
import uuid
from pathlib import Path
from app.services.storage.base import StorageInterface # Import khuôn mẫu

class UploadService:
    def __init__(self, storage_service: StorageInterface): # Nhận "kho" từ bên ngoài
        self.storage_service = storage_service

    async def upload_media(self, file: UploadFile, folder: str) -> dict:
        # ... (giữ lại logic validate file type, size) ...
        
        # 1. Tạo tên file duy nhất
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # 2. Ủy quyền việc upload cho "kho" đã được chọn
        media_url = await self.storage_service.upload(
            file=file,
            file_name=unique_filename,
            folder=folder
        )

        # 3. Trả về kết quả
        return {
            "type": media_type, # media_type từ logic validate
            "url": media_url,
        }
```

### Bước 7: Cập nhật Dependency Injection và `requirements.txt`

1.  **Sửa `app/api/deps.py`:** Cập nhật hàm `get_upload_service` để nó nhận `StorageInterface` từ factory `get_storage_service`.
2.  **Sửa `requirements.txt`:**
    *   Thêm `boto3` và `aiobotocore` nếu bạn triển khai S3.
    *   Đảm bảo có `aiofiles`.

---

Bằng cách này, `UploadService` chỉ cần biết nó đang nói chuyện với một `StorageInterface`, không cần quan tâm đó là `LocalStorage` hay `S3Storage`. Bạn chỉ cần thay đổi `STORAGE_PROVIDER` trong file `.env` để chuyển đổi qua lại.
