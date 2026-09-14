import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class SessionCreate(BaseModel):
    username: str
    email: EmailStr


class SessionCreateOut(BaseModel):
    session_id: uuid.UUID


class SessionOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    started_at: datetime
    ended_at: datetime | None
    status: str

    class Config:
        from_attributes = True


class SDPIn(BaseModel):
    sdp: str
    type: str


class SDPOut(BaseModel):
    sdp: str
    type: str


class VideoSegmentOut(BaseModel):
    segment_index: int
    duration_seconds: float | None
    started_at: datetime
    ended_at: datetime | None

    class Config:
        from_attributes = True
