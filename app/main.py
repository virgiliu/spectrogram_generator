from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from filetype import guess as guess_filetype
from filetype.types.audio import Mp3, Wav
from filetype.types.base import Type

import app.db as db
from app.celery_app import celery_app
from app.constants import FILE_HEADER_READ_SIZE
from app.events import AUDIO_UPLOADED
from app.models.audio import Audio
from app.repositories.audio import AudioRepository


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
    # Read just the start of the file so we can determine
    # if it's an expected audio type before reading the entire thing
    header = await audio_file.read(FILE_HEADER_READ_SIZE)

    audio_file.file.seek(0)

    guessed_type: Type | None = guess_filetype(header)

    # noinspection PyUnreachableCode
    match guessed_type:
        case Mp3() | Wav():
            mimetype = guessed_type.mime
        case _:
            raise HTTPException(status_code=400, detail="Unsupported audio file type")

    audio_bytes = await audio_file.read()

    with db.get_session() as session:
        repo = AudioRepository(session)
        uploaded_file = repo.create(
            Audio(filename=audio_file.filename, content_type=mimetype, data=audio_bytes)
        )

    celery_app.send_task(AUDIO_UPLOADED, args=[uploaded_file.id])

    return {
        "filename": audio_file.filename,
        "mimetype": mimetype,
        "audio_id": uploaded_file.id,
    }
