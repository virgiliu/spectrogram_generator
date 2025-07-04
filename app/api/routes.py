from typing import Annotated, cast
from uuid import UUID

from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile)
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from app.api.schemas import HealthCheckResponse, UploadResponse
from app.celery_app import celery_app
from app.db import session_generator
from app.events import AUDIO_UPLOADED
from app.exceptions import InvalidAudioFile
from app.repositories.audio import AudioRepository
from app.services.audio_upload import AudioUploadService
from app.services.s3_storage import S3StorageService

router = APIRouter()


def get_audio_store(request: Request) -> S3StorageService:
    return request.app.state.audio_store


async def get_audio_repository(
    session: AsyncSession = Depends(session_generator),
) -> AudioRepository:
    return AudioRepository(session)


async def get_audio_upload_service(
    audio_repo: AudioRepository = Depends(get_audio_repository),
    audio_store: S3StorageService = Depends(get_audio_store),
) -> AudioUploadService:
    return AudioUploadService(audio_repo, audio_store)


@router.get("/", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok")


@router.post(
    "/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_audio(
    audio_file: Annotated[UploadFile, File(description="mp3 or wav file")],
    service: AudioUploadService = Depends(get_audio_upload_service),
) -> UploadResponse:

    try:
        uploaded_file = await service.handle_upload(audio_file)
    except InvalidAudioFile as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    celery_app.send_task(AUDIO_UPLOADED, args=[uploaded_file.id])

    return UploadResponse(audio_id=cast(UUID, uploaded_file.id))
