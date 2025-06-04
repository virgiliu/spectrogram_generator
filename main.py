from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from filetype import guess as guess_filetype
from filetype.types.audio import Mp3, Wav
from filetype.types.base import Type

from constants import FILE_HEADER_READ_SIZE

app = FastAPI()


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_audio(
    audio_file: Annotated[UploadFile, File(description="mp3 or wav file")],
):
    file_content = await audio_file.read(FILE_HEADER_READ_SIZE)

    audio_file.file.seek(0)

    guessed_type: Type | None = guess_filetype(file_content)

    # noinspection PyUnreachableCode
    match guessed_type:
        case Mp3() | Wav():
            mimetype = guessed_type.mime
        case _:
            raise HTTPException(status_code=400, detail="Unsupported audio file type")

    return {"filename": audio_file.filename, "mimetype": mimetype}
