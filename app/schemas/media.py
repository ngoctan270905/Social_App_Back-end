from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .utils import ObjectIdStr


class MediaType(str, Enum):
    AVATAR = "avatar"
    COVER = "cover"
    POST = "post"
    COMMENT = "comment"
    STORY = "story"


class OwnerType(str, Enum):
    USER = "user"
    POST = "post"
    COMMENT = "comment"
    GROUP = "group"


class PrivacyType(str, Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


# Validate Dữ liệu thêm ================================================================================================
class MediaCreate(BaseModel):
    owner_id: ObjectIdStr = Field(..., description="ID của chủ sở hữu")
    owner_type: OwnerType = Field(..., description="Loại chủ sở hữu")
    type: MediaType = Field(..., description="Loại media")

    public_id: str = Field(..., description="Cloudinary public_id")
    url: str = Field(..., description="URL gốc của ảnh")

    width: int = Field(..., gt=0, description="Chiều rộng ảnh")
    height: int = Field(..., gt=0, description="Chiều cao ảnh")

    format: Optional[str] = Field(None, description="jpg, png, webp...")
    bytes: Optional[int] = Field(None, description="Kích thước file (bytes)")

    privacy: PrivacyType = Field(default=PrivacyType.PUBLIC)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



# Trả về cho frontend ==================================================================================================
class MediaResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    type: MediaType = Field(..., description="Loại media")
    url: str = Field(..., description="URL gốc của ảnh")


# Update ===============================================================================================================
class MediaUpdate(BaseModel):
    privacy: Optional[PrivacyType] = None
    type: Optional[MediaType] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

