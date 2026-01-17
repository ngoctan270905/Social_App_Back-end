from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

# Đối tượng em được bài viết ===========================================================================================
class PostType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS = "friends"


# Va
class NewsCreate(BaseModel):
    title: str
    content: str


# Validate tạo bài viết mới ============================================================================================
class PostCreate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    privacy: PostType


class MediaPublic(BaseModel):
    id: ObjectIdStr
    type: str
    url: str

class PostCreateResponse(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")
    content: str
    privacy: PostType
    media: Optional[list[MediaPublic]] = None
    created_at: datetime

# Schema trả về danh sách bài viết =====================================================================================
class UserPublic(BaseModel):
    id: ObjectIdStr
    display_name: str
    avatar: Optional[str] = None


class PostsListResponse(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")
    content: str
    media: Optional[list[MediaPublic]] = None
    author: Optional[UserPublic] = None
    privacy: PostType
    created_at: datetime

# class PostsListResponse(BaseModel):
#     id: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")
#     content: str
#     privacy: PostType
#     created_at: datetime

class PaginationInfo(BaseModel):
    next_cursor: Optional[str]
    has_more: bool
    limit: int

class PaginatedPostsResponse(BaseModel):
    data: List[PostsListResponse]
    pagination: PaginationInfo
