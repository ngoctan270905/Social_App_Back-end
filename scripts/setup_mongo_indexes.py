import asyncio
import logging
import sys
import os
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

        # TTL Index (Time To Live): Tự động xóa token khi hết hạ
        # ==========================================
        # 4. Collection: posts
        # ==========================================
        logger.info("Đang xử lý collection: posts")
        posts_col = db.get_collection("posts")

        # Index cho trang cá nhân (Lấy bài viết của user, sắp xếp mới nhất)
        await posts_col.create_index([("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        logger.info("  - Đã tạo compound index (user_id, created_at) cho trang cá nhân")

        # Index cho News Feed public (Lấy bài public, sắp xếp mới nhất)
        await posts_col.create_index([("privacy", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        logger.info("  - Đã tạo compound index (privacy, created_at) cho Public Feed")

        # Text Index cho tìm kiếm nội dung bài viết
        await posts_col.create_index([("content", pymongo.TEXT)])
        logger.info("  - Đã tạo text index cho 'content' để tìm kiếm")

        # ==========================================
        # 5. Collection: media
        # ==========================================
        logger.info("Đang xử lý collection: media")
        media_col = db.get_collection("media")

        # Unique Index cho public_id

        await media_col.create_index("public_id", unique=True, sparse=True)
        logger.info("  - Đã tạo unique sparse index cho 'public_id'")

        # Index cho created_at (Để quét và xóa file rác cũ)
        await media_col.create_index([("created_at", pymongo.DESCENDING)])
        logger.info("  - Đã tạo index cho 'created_at'")

        # ==========================================
        # 6. Collection: comments
        # ==========================================
        logger.info("Đang xử lý collection: comments")
        comments_col = db.get_collection("comments")

        # Index 1: Lấy comment gốc của post
        # Query: {post_id: <id>, root_id: null} sort by created_at DESC
        await comments_col.create_index([("post_id", pymongo.ASCENDING), ("root_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
        logger.info("  - Đã tạo compound index ({post_id: 1, root_id: 1, created_at: -1}) cho comment gốc")

        # Index 2: Lấy replies của 1 comment (trong một luồng)
        # Query: {root_id: <id>} sort by created_at ASC
        await comments_col.create_index([("root_id", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)])
        logger.info("  - Đã tạo compound index ({root_id: 1, created_at: 1}) cho replies trong luồng")


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
