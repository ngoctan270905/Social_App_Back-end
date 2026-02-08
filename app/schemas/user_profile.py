from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .posts import MediaPublic
from .utils import ObjectIdStr

class UpdateProfileAvatar(BaseModel):
    avatar: MediaPublic

class UpdateProfileCover(BaseModel):
    cover: MediaPublic

class UserProfileDetail(BaseModel):
    id: ObjectIdStr = Field(alias="_id", serialization_alias="id")
    avatar: Optional[MediaPublic] = None
    cover: Optional[MediaPublic] = None
    name: str
