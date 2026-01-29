from enum import Enum
from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from .utils import ObjectIdStr

class ParticipantEmbedded(BaseModel):
    user_id: ObjectIdStr
    avatar: str
    name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationCreate(BaseModel):
    participant_ids: List[ObjectIdStr]
    is_group: bool = False


# Response trả về cho Client
class ConversationResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    participants: List[ParticipantEmbedded]
    is_group: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_by: List[DeletedBy] = []

class ConversationFindOrCreate(BaseModel):
    target_user_id: str

class ConversationCreateResponse(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    participants: List[ParticipantEmbedded]
    is_group: bool = False
    created_at: datetime

class ConversationPartner(BaseModel):
    user_id: ObjectIdStr
    name: str
    avatar: str

class ConversationListItem(BaseModel):
    id: ObjectIdStr = Field(..., alias="_id", serialization_alias="id")
    is_group: bool = False
    partner: Optional[ConversationPartner] = None
    deleted_by: List[DeletedBy] = []

class DeletedBy(BaseModel):
    user_id: ObjectIdStr
    deleted_at: datetime


