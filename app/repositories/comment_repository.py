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



    # Lấy bình luận gốc trong post (Cũ nhất trước, hỗ trợ cursor)
    async def get_root_comments(self, post_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {
            "post_id": ObjectId(post_id),
            "root_id": None
        }
        if cursor:
            query["_id"] = {"$gt": ObjectId(cursor)}
        
        cursor_obj = self.collection.find(query).sort("_id", 1).limit(limit)

        comments = []
        async for comment in cursor_obj:
            comments.append(comment)

        return comments

    # Lấy danh sách phản hồi của một bình luận (trong một luồng, cũ nhất trước)
    async def get_replies(self, root_id: str, limit: int = 10, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"root_id": ObjectId(root_id)}
        if cursor:
            query["_id"] = {"$gt": ObjectId(cursor)}
        
        # Replies should be sorted ascending by _id to appear in chronological order within a thread
        cursor_obj = self.collection.find(query).sort("_id", 1).limit(limit)

        replies = []
        async for reply in cursor_obj:
            replies.append(reply)

        return replies



    async def set_has_replies(self, comment_id: str, value: bool = True) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"has_replies": value}}
        )

    # Tìm comment theo ID ==============================================================================================
    async def get_by_id(self, comment_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(comment_id)})
