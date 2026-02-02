from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.utils import ObjectIdStr
from app.schemas.posts import UserPublic

# ================= FOR REAL-TIME PAYLOAD =================
class NotificationResponse(BaseModel):
    type: str
    message: str
    data: Dict[str, Any]


# ================= FOR DATABASE STORAGE =================
class NotificationBase(BaseModel):
    recipient_id: ObjectIdStr
    actor: UserPublic
    type: str
    message: str
    is_read: bool = False
    entity_ref: Dict[str, ObjectIdStr]
    
class NotificationCreate(NotificationBase):
    created_at: datetime

class Notification(NotificationBase):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    created_at: datetime