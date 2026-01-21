from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

class ConversationCreate(BaseModel):
    is_group: bool = False

# Response trả về cho Client
class ConversationResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    is_group: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
