from typing import Optional, List, Dict, Any
from bson import ObjectId
from fastapi.concurrency import run_in_threadpool
from app.core.mongo_database import mongodb_client
from app.schemas.author import AuthorCreate, AuthorUpdate

class AuthorRepository:
    # Hàm khởi tạo
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("authors")


    # truy vấn db lấy tất cả ds author
    async def get_all(self) -> List[Dict[str, Any]]:
        authors = []
        async for author in self.collection.find():
            authors.append(author)
        return authors


    # truy vấn db thêm authors
    async def create(self, author_create: AuthorCreate) -> Dict[str, Any]:
        author_data = author_create.model_dump()
        result = await self.collection.insert_one(author_data)
        author_data["id"] = result.inserted_id
        return author_data


    # truy vấn db tìm tac gia theo name
    async def get_author_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        author = await self.collection.find_one({"name": name})
        return author


    # truy vấn db để lấy tác giả theo id
    async def get_by_id(self, author_id: str) -> Optional[Dict[str, Any]]:
        author = await self.collection.find_one({"_id":ObjectId(author_id)})
        return author


    # truy vấn db để update author
    async def update(self, author_id: str, author_update: AuthorUpdate) -> Optional[Dict[str, Any]]:
        update_data = author_update.model_dump(exclude_unset=True)
        await self.collection.update_one(
            {"_id": ObjectId(author_id)},
            {"$set": update_data}
        )
        updated_author = await self.collection.find_one({"_id": ObjectId(author_id)})
        return updated_author


    # truy vấn db để xóa author
    async def delete(self, author_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(author_id)})
        return result.deleted_count > 0