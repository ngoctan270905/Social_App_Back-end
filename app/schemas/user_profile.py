from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime

from .news import MediaPublic
from .utils import ObjectIdStr

class UpdateProfileAvatar(BaseModel):
    avatar: MediaPublic