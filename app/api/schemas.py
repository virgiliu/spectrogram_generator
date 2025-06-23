from uuid import UUID

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str


class UploadResponse(BaseModel):
    audio_id: UUID
