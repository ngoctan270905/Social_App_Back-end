from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
from app.core.mongo_database import mongodb_client
from app.schemas.book import BookCreate, BookUpdate, BookResponse


class BookRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("books")

    # Truy vấn db lấy ds book
    async def get_all(self) -> List[Dict[str, Any]]:
        books = []
        async for book in self.collection.find():
            books.append(book)
        return books

    # Truy vấn db thêm book
    async def create_book(self, book_create: BookCreate) -> Dict[str, Any]:
        book_data = book_create.model_dump()
        result = await self.collection.insert_one(book_data)
        book_data["_id"] = result.inserted_id
        return book_data


    # Truy vấn db tìm book theo name
    async def get_book_by_name(self, title: str) -> Optional[Dict[str, Any]]:
        book = await self.collection.find_one({"title": title})
        return book


    # Truy vấn db tìm book theo id
    async def get_by_book_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        book = await self.collection.find_one({"_id": ObjectId(book_id)})
        return book


    # Truy vấn db update book
    async def update_book(self, book_id: str, book_update: BookUpdate) -> Optional[Dict[str, Any]]:
        book_update_data = book_update.model_dump(exclude_unset=True)
        result = await self.collection.update_one({"_id": ObjectId(book_id)}, {"$set": book_update_data})
        updated_book = await self.collection.find_one({"_id": ObjectId(book_id)})
        return updated_book


    async def delete_book(self, book_id: str) -> bool:
       result = await self.collection.delete_one({"_id": ObjectId(book_id)})
       return result.deleted_count > 0

