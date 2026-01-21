from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

# class MessageCreate(BaseModel):
#     conversation_id: Optional[ObjectIdStr]
#     content: str
#
# class MessageResponse(BaseModel):
#     id: ObjectIdStr = Field(alias="_id", serialization_alias="id")
#     sender_id: ObjectIdStr
#     content: str
#     created_at: datetime

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
