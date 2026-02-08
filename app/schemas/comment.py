from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.utils import ObjectIdStr
from app.schemas.posts import UserPublic

# =========== REQUEST DTO ==============================================================================================
class CommentCreate(BaseModel):
    post_id: ObjectIdStr = Field(...)
    content: str = Field(..., max_length=1000)
    reply_to_comment_id: Optional[ObjectIdStr] = None


# ================ RESPONSE DTO ========================================================================================
class UserReply(BaseModel):
    id: ObjectIdStr
    display_name: str

class CommentCreateResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    post_id: ObjectIdStr
    root_id: Optional[ObjectIdStr] = None
    reply_to_comment_id: Optional[ObjectIdStr] = None
    reply_to_user: Optional[UserReply] = None
    content: str
    has_replies: bool = False
    author: UserPublic
    created_at: datetime

class CommentResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    # post_id: ObjectIdStr
    root_id: Optional[ObjectIdStr] = None
    # reply_to_comment_id: Optional[ObjectIdStr] = None
    # reply_to_user_id: Optional[ObjectIdStr] = None
    content: str
    has_replies: bool = False
    author: UserPublic
    created_at: datetime

class CommentReplyResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    post_id: ObjectIdStr
    root_id: Optional[ObjectIdStr] = None
    reply_to_comment_id: Optional[ObjectIdStr] = None
    reply_to_user: Optional[UserReply] = None
    content: str
    has_replies: bool = False
    author: UserPublic
    created_at: datetime
