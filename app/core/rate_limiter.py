import logging
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# lấy log
logger = logging.getLogger(__name__)

# tạo 1 đối tượng limit
limiter = Limiter(
    key_func=get_remote_address, # lấy địa chỉ ip
    enabled=settings.RATE_LIMIT_ENABLED,
    storage_uri=settings.REDIS_URL, # lưu vào redis
    strategy="fixed-window"

)

# ghi log khi khởi động ứng dụng
# nếu log được bật
if settings.RATE_LIMIT_ENABLED:
    logger.info(f"Rate Limit đã được bật: Giới hạn limit: {settings.RATE_LIMIT_DEFAULT}")
else:
    logger.info(f"Rate Limit đang không hoạt động")
