from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class AgentBase(BaseModel):
    email: str
    name: str
    role: str = "agent"


class AgentCreate(AgentBase):
    password: str


class AgentUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class AgentRead(AgentBase):
    id: int
    created_at: datetime
    open_ticket_count: Optional[int] = 0

    class Config:
        from_attributes = True


class CallRecordBase(BaseModel):
    session_dir: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    language: str = "en"
    transcript: Optional[Any] = None
    escalated: bool = False
    audio_path: Optional[str] = None


class CallRecordRead(CallRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    issue_summary: str
    status: str = "open"
    conversation: Optional[Any] = None
    resolution_note: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    resolution_note: Optional[str] = None
    assigned_to: Optional[int] = None


class TicketRead(TicketBase):
    id: int
    call_record_id: Optional[int] = None
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    assignee: Optional[AgentRead] = None

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    content: str


class NoteRead(NoteCreate):
    id: int
    ticket_id: int
    agent_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationRead(BaseModel):
    id: int
    agent_id: int
    type: str
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    agent_id: Optional[int] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str
