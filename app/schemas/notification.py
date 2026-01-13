from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "info" # info, warning, error, success
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Optional[Dict[str, Any]] = None # Dữ liệu kèm theo tùy ý

class NotificationResponse(NotificationBase):
    pass