from typing import Optional, List, Dict, Any
from bson import ObjectId
from sqlalchemy import select
import uuid
from app.core.mongo_database import mongodb_client
from app.schemas.auth import UserRegister


class UserRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("users")

    # Truy vấn DB lấy thông tin User theo ID ===========================================================================
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        # print(f"test {user}")
        return user



    # Truy vấn DB tìm name user ========================================================================================
    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        user_name = await self.collection.find_one({"username": username})
        return user_name


    # Truy vấm DB tìm email user =======================================================================================
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        user_email = await self.collection.find_one({"email": email})
        return user_email


    # Truy vấn DB thêm user ============================================================================================
    async def create(self, user_dict: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        return user_dict


    # Truy vấn DB update user ==========================================================================================
    async def update(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.update_one({"_id": user_id}, {"$set": user_data})
        updated_user = await self.collection.find_one({"_id": ObjectId(user_id)})
        return updated_user



