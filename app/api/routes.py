from typing import Annotated, cast

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session
from starlette import status

from app.api.schemas import HealthCheckResponse, UploadResponse
from app.celery_app import celery_app
from app.db import session_generator
from app.events import AUDIO_UPLOADED
from app.exceptions import InvalidAudioFile
from app.services.audio_upload import AudioUploadService

router = APIRouter()


def get_audio_upload_service(
    session: Session = Depends(session_generator),
) -> AudioUploadService:
    return AudioUploadService(session)


@router.get("/", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok")


@router.post("/upload", response_model=UploadResponse)
async def upload_audio(
    audio_file: Annotated[UploadFile, File(description="mp3 or wav file")],
    service: AudioUploadService = Depends(get_audio_upload_service),
) -> UploadResponse:

    try:
        uploaded_file = await service.handle_upload(audio_file)
    except InvalidAudioFile as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    celery_app.send_task(AUDIO_UPLOADED, args=[uploaded_file.id])

    return UploadResponse(audio_id=cast(int, uploaded_file.id))
