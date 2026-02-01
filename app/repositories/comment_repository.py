from typing import Dict, Any, List, Optional
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class CommentRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("comments")

    # Thêm comment mới =================================================================================================
    async def create(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        insert_result = await self.collection.insert_one(comment_data)
        comment_data["_id"] = insert_result.inserted_id
        return comment_data



    # Lấy bình luận trong post (Chỉ lấy Root Comments) =================================================================
    async def get_by_post_id(self, post_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {
            "post_id": ObjectId(post_id),
            "parent_id": None
        }

        if cursor:
             query["_id"] = {"$lt": ObjectId(cursor)}

        cursor = self.collection.find(query).sort("_id", -1).limit(limit)

        comments = []
        async for comment in cursor:
            comments.append(comment)

        return comments

    # Lấy danh sách phản hồi của một bình luận =========================================================================
    async def get_replies(self, parent_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"parent_id": ObjectId(parent_id)}

        if cursor:
            query["_id"] = {"$lt": ObjectId(cursor)}

        cursor = self.collection.find(query).sort("_id", -1).limit(limit)

        replies = []
        async for reply in cursor:
            replies.append(reply)

        return replies

    # Tăng số lượng phản hồi ===========================================================================================
    async def increment_reply_count(self, comment_id: str, amount: int = 1) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$inc": {"reply_count": amount}}
        )

    # Tìm comment theo ID ==============================================================================================
    async def get_by_id(self, comment_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(comment_id)})
