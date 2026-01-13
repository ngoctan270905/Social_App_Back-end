import io
from PIL import Image
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

MAX_SIZE_POST = (1080, 1080)  # Full HD cho bài viết
MAX_SIZE_AVATAR = (300, 300)  # Avatar

async def process_and_save_image(file: UploadFile, output_path: str, is_avatar: bool = False) -> str:
    """
    Đọc file upload, resize, chuyển sang WebP và lưu xuống đĩa.
    Chạy trong threadpool để không block main loop của FastAPI.
    """
    content = await file.read()
    
    def _process():
        with Image.open(io.BytesIO(content)) as img:
            # Chuyển sang RGB nếu là RGBA (PNG) để lưu được dưới dạng WebP/JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize (giữ tỉ lệ)
            target_size = MAX_SIZE_AVATAR if is_avatar else MAX_SIZE_POST
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Lưu file dưới dạng WebP
            # output_path nên có đuôi .webp
            img.save(output_path, "WEBP", quality=80, optimize=True)
            
    # Xử lý ảnh là tác vụ CPU bound, cần đẩy vào threadpool
    await run_in_threadpool(_process)
    
    return output_path
