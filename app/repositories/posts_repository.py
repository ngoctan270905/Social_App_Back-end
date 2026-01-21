from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client


class PostRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("posts")

    # Query lấy danh sách bài viết kèm phân trang ======================================================================
    async def get_all_posts(
            self,
            cursor: Optional[str] = None,
            limit: int = 5
    ) -> List[Dict[str, Any]]:

        # 1. Tạo query filter
        query: Dict[str, Any] = {"privacy": "public"}

        # 2. Nếu có cursor lấy bài cũ hơn cursor đó
        if cursor:
            query["_id"] = {"$lt": ObjectId(cursor)}

        db_cursor = self.collection.find(query).sort("_id", -1).limit(limit)

        posts = []
        async for post in db_cursor:
            posts.append(post)

        return posts


    # Query thêm bài viết mới ==========================================================================================
    async def create(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        insert_new = await self.collection.insert_one(post_data)
        post_data["_id"] = insert_new.inserted_id
        return post_data


    # Query lấy thông tin 1 bài viết ===================================================================================
    async def get_by_id(self, post_id:str) -> Dict[str, Any]:
        post = await self.collection.find_one({"_id": ObjectId(post_id)})
        return post


    # Query update bài viết ============================================================================================
    async def update(self, post_data: Dict[str, Any], post_id: str) -> Dict[str, Any]:
        update = await self.collection.update_one({"_id": ObjectId(post_id)},
                                                  {"$set": post_data})
        result = await self.collection.find_one({"_id": ObjectId(post_id)})
        return result


    # Xóa bài viết =====================================================================================================
    async def delete(self, post_id: str) -> bool:
        deleted = await self.collection.delete_one({"_id": ObjectId(post_id)})
        return deleted.deleted_count

    async def get_posts_by_user(
            self,
            user_id: str,
            privacy_filter: Optional[List[str]] = None,
            cursor: Optional[str] = None,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        query = {"user_id": ObjectId(user_id)}
        if privacy_filter:
            query["privacy"] = {"$in": privacy_filter}
        if cursor:
            query["_id"] = {"$lt": ObjectId(cursor)}

        db_cursor = self.collection.find(query).sort("_id", -1).limit(limit)
        posts = []
        async for post in db_cursor:
            posts.append(post)
        return posts