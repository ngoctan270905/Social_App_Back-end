from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

class UpdateProfileAvatar(BaseModel):
    avatar: Optional[ObjectIdStr] = Field(default=None, alias="_id", serialization_alias="id")