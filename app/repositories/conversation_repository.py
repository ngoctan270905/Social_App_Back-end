from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ConversationRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("conversations")

    async def create(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo một document cuộc trò chuyện mới.
        """
        result = await self.collection.insert_one(conversation_data)
        conversation_data["_id"] = result.inserted_id
        return conversation_data

    # Tạo cuộc trò chuyện ==============================================================================================
    # async def create(self, user_ids: List[str], is_group: bool = False) -> Dict[str, Any]:
    #     now = datetime.utcnow()
    #     participants = [{"user_id": ObjectId(uid), "joined_at": now} for uid in user_ids]
    #
    #     doc = {
    #         "is_group": is_group,
    #         "participants": participants,
    #         "created_at": now,
    #         "updated_at": now
    #     }
    #     result = await self.collection.insert_one(doc)
    #     doc["_id"] = result.inserted_id
    #     return doc

    # Lấy chi tiết cuộc trò chuyện =====================================================================================
    async def get_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(conversation_id)})

    async def find_by_participants(self, participant_ids: List[str]) -> Optional[Dict[str, Any]]:
        """
        Tìm một cuộc trò chuyện 1-1 dựa trên ID của người tham gia.
        Giả định participant_ids là các chuỗi có thể chuyển đổi thành ObjectId.
        """
        object_ids = [ObjectId(p_id) for p_id in participant_ids]
        print(f"object_ids: {object_ids}")

        # Truy vấn này tìm một cuộc trò chuyện có chính xác hai người tham gia này
        # và không có người nào khác (cho cuộc trò chuyện riêng tư)
        # và cũng xem xét trường hợp thứ tự của người tham gia có thể bị tráo đổi trong DB

        # Điều này có thể cần tinh chỉnh dựa trên cách 'participants' được lưu trữ và lập chỉ mục.
        # Để đơn giản, giả sử có một trường mảng 'participant_ids'.
        query = {
            "participants.user_id": {
                "$all": object_ids
            },
            "is_group": False
        }

        print(f"query: {query}")
        result =  await self.collection.find_one(query)
        print(f"result: {result}")
        return result

    # Tìm cuộc hội thoại giữa 2 người dùng =============================================================================
    async def find_direct_conversation_between_users(self, user_id_1: str, user_id_2: str) -> Optional[Dict[str, Any]]:
        """Tìm cuộc hội thoại 1-1 giữa 2 người dùng."""
        return await self.collection.find_one({
            "is_group": False,
            "participants.user_id": {
                "$all": [ObjectId(user_id_1), ObjectId(user_id_2)]
            },
            # Sicherstellen, dass es genau zwei Teilnehmer gibt
            "participants": {"$size": 2}
        })


    # Lấy danh sách chat của người dùng ================================================================================
    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"participants.user_id": ObjectId(user_id)})
        return await cursor.to_list(length=1000)


    async def delete(self, conversation_id: str) -> bool:
        """
        Xóa document cuộc trò chuyện theo ID.
        Trả về True nếu xóa thành công, False nếu không tìm thấy.
        """
        result = await self.collection.delete_one({"_id": ObjectId(conversation_id)})
        return result.deleted_count > 0