from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from .utils import ObjectIdStr


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

# ============= SHARED SUB MODELS ======================================================================================
class MediaPublic(BaseModel):
    id: ObjectIdStr
    type: str
    url: str


# Trả về cho frontend ==================================================================================================
class MediaResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    type: MediaType = Field(..., description="Loại media")
    url: str = Field(..., description="URL gốc của ảnh")


