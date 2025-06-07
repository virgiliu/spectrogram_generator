from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from starlette import status

import app.db as db
from app.celery_app import celery_app
from app.constants import FILE_HEADER_READ_SIZE
from app.events import AUDIO_UPLOADED
from app.services.audio_upload import AudioUploadService


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_audio(
    audio_file: Annotated[UploadFile, File(description="mp3 or wav file")],
):

    try:
        service = AudioUploadService()
        uploaded_file = await service.handle_upload(audio_file)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    celery_app.send_task(AUDIO_UPLOADED, args=[uploaded_file.id])

    return {
        "audio_id": uploaded_file.id,
    }
