# Kế hoạch Tái cấu trúc Tính năng Chat (Nhúng Participant)

Tài liệu này mô tả chi tiết các bước để tái cấu trúc (refactor) lại mô hình dữ liệu của tính năng chat, chuyển từ mô hình tham chiếu (referencing) sang mô hình nhúng (embedding) để tối ưu hiệu năng.

## 1. Mục tiêu

Gộp collection `participants` vào `conversations`. Mỗi document `conversation` sẽ chứa một mảng `participants` để giảm số lượng truy vấn tới database và tăng tốc độ tải dữ liệu.

## 2. Kế hoạch thực thi

1.  **Cập nhật Schemas:** Sửa `conversation.py`, xóa `participant.py`.
2.  **Cập nhật Repositories:** Sửa `conversation_repository.py`, xóa `participant_repository.py`.
3.  **Cập nhật Services:** Sửa `conversation_service.py`, xóa `participant_service.py`.
4.  **Cập nhật Endpoint:** Dọn dẹp dependencies trong `chat.py`.
5.  **Di chuyển dữ liệu cũ:** (Thực hiện thủ công) Chạy script để chuyển đổi dữ liệu đã có trong database sang cấu trúc mới.

## 3. Chi tiết thay đổi Code

---

### Bước 1: Cập nhật Schemas

#### 1.1. Sửa `app/schemas/conversation.py`

File này sẽ được cập nhật để chứa schema `ParticipantEmbedded` và sử dụng nó.

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

class ParticipantEmbedded(BaseModel):
    user_id: ObjectIdStr
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationBase(BaseModel):
    is_group: bool = False

class ConversationCreate(ConversationBase):
    # Khi tạo conversation, chỉ cần truyền user_ids
    participant_ids: List[ObjectIdStr]

# Response trả về cho Client
class ConversationResponse(ConversationBase):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    participants: List[ParticipantEmbedded]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
```

#### 1.2. Xóa `app/schemas/participant.py`

File này không còn cần thiết nữa.
**Hành động: Xóa file `Social_App_Back-end/app/schemas/participant.py`**

---

### Bước 2: Cập nhật Repositories

#### 2.1. Sửa `app/repositories/conversation_repository.py`

Repository này sẽ xử lý toàn bộ logic liên quan đến conversation.

```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ConversationRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("conversations")

    async def create(self, user_ids: List[str], is_group: bool = False) -> Dict[str, Any]:
        """Tạo cuộc hội thoại mới với danh sách người tham gia."""
        now = datetime.utcnow()
        participants = [{"user_id": ObjectId(uid), "joined_at": now} for uid in user_ids]
        
        doc = {
            "is_group": is_group,
            "participants": participants,
            "created_at": now,
            "updated_at": now
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def get_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(conversation_id)})

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

    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Lấy tất cả các cuộc hội thoại của một người dùng."""
        cursor = self.collection.find({"participants.user_id": ObjectId(user_id)})
        return await cursor.to_list(length=1000) # Or use pagination
```

#### 2.2. Xóa `app/repositories/participant_repository.py`

File này không còn cần thiết nữa.
**Hành động: Xóa file `Social_App_Back-end/app/repositories/participant_repository.py`**

---

### Bước 3: Cập nhật Services

#### 3.1. Sửa `app/services/conversation_service.py`

Service này sẽ được đơn giản hóa.

```python
from typing import Optional, List, Dict, Any
from app.repositories.conversation_repository import ConversationRepository

class ConversationService:
    def __init__(self, conversation_repo: ConversationRepository):
        self.conversation_repo = conversation_repo

    async def get_or_create_private_conversation(self, sender_id: str, target_user_id: str) -> str:
        """
        Kiểm tra xem đã có hội thoại 1-1 chưa.
        - Nếu có: Trả về ID.
        - Nếu chưa: Tạo mới và trả về ID.
        """
        existing_conv = await self.conversation_repo.find_direct_conversation_between_users(sender_id, target_user_id)
        if existing_conv:
            return str(existing_conv["_id"])
        
        # Tạo mới
        new_conv = await self.conversation_repo.create(user_ids=[sender_id, target_user_id], is_group=False)
        return str(new_conv["_id"])

    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Lấy tất cả các cuộc hội thoại của một người dùng."""
        return await self.conversation_repo.get_conversations_for_user(user_id)
```

#### 3.2. Xóa `app/services/participant_service.py`

File này không còn cần thiết nữa.
**Hành động: Xóa file `Social_App_Back-end/app/services/participant_service.py`**

---

### Bước 4: Cập nhật Endpoint

#### 4.1. Sửa `app/api/v1/endpoints/chat.py`

Cập nhật lại phần dependency injection.

```python
# ... imports ...
# Bỏ import liên quan đến Participant
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api import deps
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_service import MessageService
from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.repositories.conversation_repository import ConversationRepository

router = APIRouter()

# Dependency Injection Setup (đã được đơn giản hóa)
def get_message_repo():
    return MessageRepository()

def get_conversation_repo():
    return ConversationRepository()

def get_conversation_service(
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    return ConversationService(conversation_repo)

def get_message_service(
    message_repo: MessageRepository = Depends(get_message_repo),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    return MessageService(message_repo, conversation_service)

# ... (các hàm @router.post và @router.get giữ nguyên) ...
```

## 4. Lưu ý về Di chuyển Dữ liệu (Data Migration)

Sau khi áp dụng các thay đổi về code, dữ liệu cũ trong database của bạn sẽ không tương thích. Bạn sẽ cần viết một script riêng để:
1.  Đọc tất cả các `conversations`.
2.  Với mỗi `conversation`, tìm tất cả `participants` từ collection cũ.
3.  Nhúng thông tin `participants` vào `conversation` tương ứng.
4.  Xóa collection `participants` cũ.
Việc này cần được thực hiện cẩn thận để tránh mất dữ liệu.

---

## Bước 5: Hoàn thiện và Thêm API Lấy danh sách

Sau khi các bước tái cấu trúc cơ bản đã được hoàn thành, chúng ta cần thực hiện các điều chỉnh cuối cùng để hoàn thiện chức năng.

### 5.1. Hoàn thiện `app/schemas/conversation.py`

Thêm `Config` class vào `ConversationResponse` để đảm bảo Pydantic có thể map dữ liệu từ MongoDB (`_id`) sang model (`id`) một cách chính xác.

**Code cần thay đổi:**
```python
# In app/schemas/conversation.py

# ... (các schema khác) ...

# Response trả về cho Client
class ConversationResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    participants: List[ParticipantEmbedded]
    is_group: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
```

### 5.2. Dọn dẹp `app/api/v1/router.py`

Loại bỏ import `uploads` không được sử dụng.

**Code cần thay đổi:**
```python
# In app/api/v1/router.py
from fastapi import APIRouter
# Bỏ 'uploads' khỏi dòng import dưới đây
from app.api.v1.endpoints import books, categories, authors, auth, users, news, profiles, chat
from app.api.v1.endpoints import notifications

# ... (rest of the file) ...
```

### 5.3. Bổ sung Endpoint vào `app/api/v1/endpoints/chat.py`

Thêm 2 endpoint còn thiếu:
*   `GET /`: Lấy danh sách tất cả các cuộc hội thoại của người dùng hiện tại.
*   `GET /{conversation_id}`: Lấy danh sách các tin nhắn trong một cuộc hội thoại cụ thể.

**Code cần thêm vào `app/api/v1/endpoints/chat.py`:**

```python
# ... (các import và endpoint 'send_message' đã có) ...

# Thêm service mới vào dependency
def get_conversation_service(conversation_repo: ConversationRepository = Depends()):
    return ConversationService(conversation_repo)

# Thêm 2 endpoint dưới đây vào sau endpoint 'send_message'

@router.get("/", response_model=ResponseModel[List[ConversationResponse]], status_code=status.HTTP_200_OK)
async def get_conversations(
    *,
    current_user: dict = Depends(get_current_user),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get all conversations for the current user.
    """
    conversations = await conversation_service.get_conversations_for_user(user_id=current_user["_id"])
    return ResponseModel(data=conversations, message="Lấy danh sách cuộc trò chuyện thành công")


@router.get("/{conversation_id}", response_model=ResponseModel[List[MessageResponse]], status_code=status.HTTP_200_OK)
async def get_messages(
    *,
    conversation_id: str,
    current_user: dict = Depends(get_current_user), # To ensure user is authenticated
    message_repo: MessageRepository = Depends(), # Assuming you have a get_message_repo dependency
    skip: int = 0,
    limit: int = 50
):
    """
    Get messages from a specific conversation.
    """
    # TODO: Add a check to ensure the current_user is a participant of the conversation
    messages = await message_repo.get_by_conversation(conversation_id, skip=skip, limit=limit)
    return ResponseModel(data=messages, message="Lấy tin nhắn thành công")

```

**Lưu ý:** Phần `dependencies` trong `chat.py` có thể cần được điều chỉnh lại để `get_conversation_service` và `get_message_repo` được định nghĩa và sử dụng một cách nhất quán. Phần code trên đưa ra một gợi ý triển khai.