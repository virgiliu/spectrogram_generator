from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.constants import AUDIO_STATUS_PENDING


class Audio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    content_type: str
    data: bytes
    status: str = AUDIO_STATUS_PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
