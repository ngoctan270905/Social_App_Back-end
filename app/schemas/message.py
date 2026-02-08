from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime

from .posts import PaginationInfo
from .utils import ObjectIdStr

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    conversation_id: ObjectIdStr
    sender_id: ObjectIdStr
    content: str
    created_at: datetime

class PaginatedMessagesResponse(BaseModel):
    data: List[MessageResponse]
    pagination: PaginationInfo


