import asyncio
import logging
import sys
import os

# Thêm thư mục gốc vào sys.path để import được app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pymongo
from app.core.config import settings
from app.core.mongo_database import mongodb_client

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def create_indexes():
    """
    Tạo indexes cho các collections trong MongoDB.
    """
    try:
        logger.info("Đang kết nối tới MongoDB...")
        await mongodb_client.connect()
        db = mongodb_client.get_database()

        # ==========================================
        # 1. Collection: users
        # ==========================================
        logger.info("Đang xử lý collection: users")
        users_col = db.get_collection("users")
        
        # Unique Index cho email
        await users_col.create_index("email", unique=True)
        logger.info("  - Đã tạo unique index cho 'email'")
        
        # Index giảm dần cho created_at (hỗ trợ sort user mới nhất)
        await users_col.create_index([("created_at", pymongo.DESCENDING)])
        logger.info("  - Đã tạo index sort cho 'created_at'")

        # ==========================================
        # 2. Collection: user_profiles
        # ==========================================
        logger.info("Đang xử lý collection: user_profiles")
        profiles_col = db.get_collection("user_profiles")
        
        # Unique Index cho user_id (Mỗi user chỉ có 1 profile)
        await profiles_col.create_index("user_id", unique=True)
        logger.info("  - Đã tạo unique index cho 'user_id'")

        # ==========================================
        # 3. Collection: refresh_tokens
        # ==========================================
        logger.info("Đang xử lý collection: refresh_tokens")
        tokens_col = db.get_collection("refresh_tokens")
        
        # Unique Index cho token (để tìm kiếm nhanh khi refresh)
        await tokens_col.create_index("token", unique=True)
        logger.info("  - Đã tạo unique index cho 'token'")
        
        # Index cho user_id (để tìm tất cả token của 1 user - vd: logout all devices)
        await tokens_col.create_index("user_id")
        logger.info("  - Đã tạo index cho 'user_id'")

        # TTL Index (Time To Live): Tự động xóa token khi hết hạn
        # expireAfterSeconds=0 nghĩa là xóa ngay khi thời gian hiện tại > expires_at
        # Lưu ý: Trường expires_at phải lưu dạng datetime object (UTC), không phải string/timestamp
        # await tokens_col.create_index("expires_at", expireAfterSeconds=0)
        # logger.info("  - Đã tạo TTL index cho 'expires_at' (Tự động xóa token hết hạn)")


        logger.info("=" * 50)
        logger.info("HOÀN TẤT! Tất cả indexes đã được tạo thành công.")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Lỗi khi tạo indexes: {e}")
    finally:
        await mongodb_client.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_indexes())
