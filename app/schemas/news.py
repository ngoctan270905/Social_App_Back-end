from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

# ============================================================================================
class NewsCreate(BaseModel):
    title: str
    content: str

class NewsCreateResponse(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")
    title: str
    content: str
    created_at: Optional[datetime] = None


# =================================================================================================
class NewsListResponse(BaseModel):
    id: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")
    title: str
    content: str
    created_at: datetime
