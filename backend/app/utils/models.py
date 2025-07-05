from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageRole(str, Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageBase(BaseModel):
    """Base message model."""
    content: str = Field(..., min_length=1, max_length=4000)
    role: MessageRole = MessageRole.USER
    quoted_message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    """Model for creating a new message."""
    user_id: str = Field(..., min_length=1)


class MessageUpdate(BaseModel):
    """Model for updating an existing message."""
    content: Optional[str] = Field(None, min_length=1, max_length=4000)
    metadata: Optional[Dict[str, Any]] = None


class MessageInDB(MessageBase):
    """Message model as stored in the database."""
    id: str
    user_id: str
    timestamp: datetime

    class Config:
        orm_mode = True


class MessageResponse(MessageInDB):
    """Message model for API responses."""
    quoted_message: Optional['MessageResponse'] = None

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


class SummaryBase(BaseModel):
    """Base summary model."""
    summary_text: str
    message_ids: List[str] = Field(..., min_items=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SummaryCreate(SummaryBase):
    """Model for creating a new summary."""
    user_id: str = Field(..., min_length=1)


class SummaryInDB(SummaryBase):
    """Summary model as stored in the database."""
    id: str
    user_id: str
    timestamp: datetime

    class Config:
        orm_mode = True


class SummaryResponse(SummaryInDB):
    """Summary model for API responses."""
    messages: Optional[List[MessageResponse]] = None

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value


# Update forward refs for recursive models
MessageResponse.update_forward_refs()