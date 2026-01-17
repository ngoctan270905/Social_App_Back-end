from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client


class PostRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("posts")

    async def get_all_posts(
            self,
            cursor: Optional[str] = None,  # ← Thêm cursor param
            limit: int = 10  # ← Thêm limit param
    ) -> List[Dict[str, Any]]:

        # 1. Tạo query filter
        query: Dict[str, Any] = {"privacy": "public"}

        # 2. Nếu có cursor → lấy bài CŨ HƠN cursor đó
        if cursor:
            query["_id"] = {"$lt": ObjectId(cursor)}  # _id < cursor

        db_cursor = self.collection.find(query).sort("_id", -1).limit(limit)

        posts = []
        async for post in db_cursor:
            posts.append(post)

        return posts



    async def create(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        insert_new = await self.collection.insert_one(post_data)
        post_data["_id"] = insert_new.inserted_id
        return post_data


