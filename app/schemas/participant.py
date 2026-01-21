from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

class Participant(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    conversation_id: ObjectIdStr
    user_id: ObjectIdStr
    joined_at: datetime