from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client


class PostRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("posts")

    async def get_all_posts(self) -> List[Dict[str, Any]]:
        posts = []
        cursor = self.collection.find({"privacy": "public"})
        async for post in cursor:
            posts.append(post)
        return posts


    async def create(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        insert_new = await self.collection.insert_one(post_data)
        post_data["_id"] = insert_new.inserted_id
        return post_data


