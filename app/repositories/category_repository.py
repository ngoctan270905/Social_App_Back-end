from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client
from app.schemas.category import CategoryCreate, CategoryUpdate

class CategoryRepository:
    def __init__(self):
        self.db = mongodb_client.get_database() #lấy database đã đc kết nối
        self.collection = self.db.get_collection("categories") # lấy collection

    # truy vấn db lấy ds category
    async def get_all_category(self) -> List[Dict[str, Any]]:
        categories = []
        async for category in self.collection.find():
            categories.append(category)
        return categories

    # thao tác vs db tạo category mới
    async def create_category(self, category_create: CategoryCreate) -> Dict[str, Any]:
        category_data = category_create.model_dump()
        result = await self.collection.insert_one(category_data)
        category_data["_id"] = result.inserted_id
        return category_data

    # truy vấn db lấy category theo name
    async def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        category = await self.collection.find_one({"name": name})
        return category

    # truy vấn db lấy category theo id
    async def get_by_category_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        category = await self.collection.find_one({"_id": ObjectId(category_id)})
        return category

    # thao tác vs db để sửa category
    async def update_category(self, category_id: str, category_update: CategoryUpdate) -> Optional[Dict[str, Any]]:
        update_data = category_update.model_dump(exclude_unset=True)
        await self.collection.update_one(
            {"_id": ObjectId(category_id)},
            {"$set": update_data}
        )
        updated_category = await self.collection.find_one({"_id": ObjectId(category_id)})
        return updated_category

    # thao tác vs db để xóa category
    async def delete(self, category_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(category_id)})
        return result.deleted_count > 0
