from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.utils import ObjectIdStr
from app.schemas.posts import UserPublic

# =========== REQUEST DTO ==============================================================================================
class CommentCreate(BaseModel):
    post_id: str = Field(...)
    content: str = Field(..., max_length=1000)
    parent_id: Optional[str] = None


# ================ RESPONSE DTO ========================================================================================
class CommentResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    post_id: ObjectIdStr
    parent_id: Optional[ObjectIdStr] = None
    content: str
    author: UserPublic
    created_at: datetime
    reply_count: int = 0
