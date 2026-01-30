from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime

from .media import MediaPublic
from .utils import ObjectIdStr

# ============== DOMAIN ENUM ===========================================================================================
class PostType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS = "friends"


# =========== REQUEST DTO ==============================================================================================
class PostCreate(BaseModel):
    content: Optional[str] = Field(default=None, max_length=5000)
    privacy: PostType


class PostUpdate(BaseModel):
    content: Optional[str] = Field(default=None, max_length=5000)
    privacy: Optional[PostType] = None



class UserPublic(BaseModel):
    id: ObjectIdStr
    display_name: str
    avatar: Optional[str] = None


# ================ RESPONSE DTO ========================================================================================
class PostCreateResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    content: str
    privacy: PostType
    media: Optional[list[MediaPublic]] = None
    created_at: datetime


class PostUpdateResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    content: str
    privacy: PostType
    media: Optional[list[MediaPublic]] = None
    created_at: datetime


class PostsListResponse(BaseModel):
    id: Optional[ObjectIdStr] = Field(..., alias="_id", serialization_alias="id")
    content: str
    media: Optional[list[MediaPublic]] = None
    author: Optional[UserPublic] = None
    privacy: PostType
    created_at: datetime


class PostDetailResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    content: Optional[str] = None
    media: Optional[List[MediaPublic]] = None
    author: UserPublic
    privacy: PostType
    created_at: datetime


# ================= PAGINATION =========================================================================================
class PaginationInfo(BaseModel):
    next_cursor: Optional[str]
    has_more: bool
    limit: int


class PaginatedPostsResponse(BaseModel):
    data: List[PostsListResponse]
    pagination: PaginationInfo
