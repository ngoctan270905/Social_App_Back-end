# Kế hoạch Triển khai Tính năng Chat (Phase 1: 1-1)

Tài liệu này mô tả chi tiết các bước, mã nguồn cần sửa đổi và bổ sung để hoàn thiện tính năng chat 1-1 dựa trên `chat.txt`.

## 1. Data Layer (Schemas & Models)

Cần bổ sung các trường trả về (Response) còn thiếu để Frontend hiển thị đầy đủ thông tin.

### 1.1. Schemas (`app/schemas/conversation.py`)
Bổ sung `id`, `created_at` cho response.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .utils import ObjectIdStr

# Base cho request tạo/update
class ConversationBase(BaseModel):
    is_group: bool = False

class ConversationCreate(ConversationBase):
    pass

# Response trả về cho Client
class ConversationResponse(ConversationBase):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
```

### 1.2. Schemas (`app/schemas/message.py`)
Bổ sung `conversation_id` vào response.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .utils import ObjectIdStr

class MessageCreate(BaseModel):
    # target_user_id dùng để tìm/tạo conversation nếu chưa có id
    target_user_id: Optional[ObjectIdStr] = None 
    conversation_id: Optional[ObjectIdStr] = None
    content: str

class MessageResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    conversation_id: ObjectIdStr
    sender_id: ObjectIdStr
    content: str
    created_at: datetime
    
    class Config:
        populate_by_name = True
```

### 1.3. Schemas (`app/schemas/participant.py`)
Đã ổn, chỉ cần đảm bảo import đúng.

---

## 2. Data Access Layer (Repositories)

Sửa lỗi Typo tên bảng và viết logic `insert/find` thực tế.

### 2.1. `app/repositories/conversation_repository.py`

```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ConversationRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        # FIX: Sửa tên collection từ "conversationa" -> "conversations"
        self.collection = self.db.get_collection("conversations")

    async def create(self, is_group: bool = False) -> Dict[str, Any]:
        """Tạo cuộc hội thoại mới"""
        doc = {
            "is_group": is_group,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(conversation_id)})
```

### 2.2. `app/repositories/participant_repository.py`

Repository giữ nguyên tắc "Dumb Repository", chỉ thực hiện các truy vấn cơ bản, không chứa logic nghiệp vụ phức tạp.

```python
from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ParticipantRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("participants")

    async def create_many(self, participants_data: List[Dict[str, Any]]):
        """Insert nhiều record cùng lúc"""
        if participants_data:
            await self.collection.insert_many(participants_data)

    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Lấy tất cả các record participant của một user"""
        cursor = self.collection.find({"user_id": ObjectId(user_id)})
        return await cursor.to_list(length=1000)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Tìm một record dựa trên query tùy ý"""
        return await self.collection.find_one(query)
```

### 2.3. `app/repositories/message_repository.py`

```python
from datetime import datetime
from typing import Dict, Any, List
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class MessageRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("messages")

    async def create(self, conversation_id: str, sender_id: str, content: str) -> Dict[str, Any]:
        doc = {
            "conversation_id": ObjectId(conversation_id),
            "sender_id": ObjectId(sender_id),
            "content": content,
            "created_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_by_conversation(self, conversation_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"conversation_id": ObjectId(conversation_id)}
        ).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
```

---

## 3. Business Logic (Services)

Tách logic thành 3 Service riêng biệt để đảm bảo tính module và dễ bảo trì.

### 3.1. `app/services/participant_service.py`
Chịu trách nhiệm xử lý logic liên quan đến thành viên (tìm kiếm quan hệ, thêm thành viên).

```python
from typing import List, Optional
from bson import ObjectId
from app.repositories.participant_repository import ParticipantRepository

class ParticipantService:
    def __init__(self, participant_repo: ParticipantRepository):
        self.participant_repo = participant_repo

    async def add_participants(self, conversation_id: str, user_ids: List[str]):
        """Thêm danh sách user vào cuộc hội thoại"""
        now = datetime.utcnow()
        participants_data = [
            {
                "conversation_id": ObjectId(conversation_id),
                "user_id": ObjectId(uid),
                "joined_at": now
            }
            for uid in user_ids
        ]
        await self.participant_repo.create_many(participants_data)

    async def find_direct_conversation_id(self, user_id_1: str, user_id_2: str) -> Optional[str]:
        """Tìm ID cuộc hội thoại 1-1 giữa 2 người (Logic tách từ Repo)"""
        # 1. Lấy tất cả hội thoại User 1 tham gia
        u1_participations = await self.participant_repo.get_by_user(user_id_1)
        u1_conv_ids = [p["conversation_id"] for p in u1_participations]

        if not u1_conv_ids:
            return None

        # 2. Tìm xem User 2 có trong danh sách hội thoại đó không
        existing_participant = await self.participant_repo.find_one({
            "user_id": ObjectId(user_id_2),
            "conversation_id": {"$in": u1_conv_ids}
        })

        if existing_participant:
            return str(existing_participant["conversation_id"])
        return None
```

### 3.2. `app/services/conversation_service.py`
Chịu trách nhiệm quản lý vòng đời cuộc hội thoại (Tạo mới, lấy thông tin). Sử dụng `ParticipantService` để xử lý thành viên.

```python
from typing import Optional
from app.repositories.conversation_repository import ConversationRepository
from app.services.participant_service import ParticipantService

class ConversationService:
    def __init__(
        self, 
        conversation_repo: ConversationRepository,
        participant_service: ParticipantService
    ):
        self.conversation_repo = conversation_repo
        self.participant_service = participant_service

    async def create_private_chat(self, user_id_1: str, user_id_2: str) -> str:
        """Tạo cuộc hội thoại 1-1 mới"""
        # 1. Tạo conversation
        new_conv = await self.conversation_repo.create(is_group=False)
        conv_id = str(new_conv["_id"])
        
        # 2. Thêm participants
        await self.participant_service.add_participants(conv_id, [user_id_1, user_id_2])
        
        return conv_id

    async def get_or_create_private_conversation(self, sender_id: str, target_user_id: str) -> str:
        """
        Kiểm tra xem đã có hội thoại chưa.
        - Nếu có: Trả về ID.
        - Nếu chưa: Tạo mới và trả về ID.
        """
        existing_id = await self.participant_service.find_direct_conversation_id(sender_id, target_user_id)
        if existing_id:
            return existing_id
        
        return await self.create_private_chat(sender_id, target_user_id)
```

### 3.3. `app/services/message_service.py`
Chỉ tập trung vào việc xử lý tin nhắn. Gọi `ConversationService` để đảm bảo hội thoại tồn tại.

```python
from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.schemas.message import MessageCreate, MessageResponse

class MessageService:
    def __init__(
        self, 
        message_repo: MessageRepository,
        conversation_service: ConversationService
    ):
        self.message_repo = message_repo
        self.conversation_service = conversation_service

    async def send_message(self, sender_id: str, data: MessageCreate) -> MessageResponse:
        conversation_id = data.conversation_id
        
        # Nếu chưa có conversation_id, nhờ ConversationService xử lý
        if not conversation_id and data.target_user_id:
            conversation_id = await self.conversation_service.get_or_create_private_conversation(
                sender_id, 
                data.target_user_id
            )
        
        if not conversation_id:
             raise ValueError("Must provide either conversation_id or target_user_id")

        # Lưu tin nhắn
        msg = await self.message_repo.create(
            conversation_id=str(conversation_id),
            sender_id=sender_id,
            content=data.content
        )
        
        return MessageResponse(**msg)
```

## 4. Các bước tiếp theo

1. Copy code từ mục 1 và 2 vào các file tương ứng trong thư mục `app/schemas` và `app/repositories`.
2. Copy code logic mục 3 vào `app/services/message_service.py`.
3. Tạo Controller (Router) tại `app/api/v1/endpoints/chat.py` để gọi Service này.
4. Đăng ký Router vào `main.py`.
