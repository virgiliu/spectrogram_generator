from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class Audio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    content_type: str
    data: bytes
    status: str = "queued"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
