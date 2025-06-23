from pathlib import Path
from typing import Optional, cast
from uuid import UUID

from fastapi import UploadFile
from filetype import guess as guess_filetype
from filetype.types.audio import Mp3, Wav
from filetype.types.base import Type

from app.exceptions import InvalidAudioFile
from app.models.audio import Audio
from app.repositories.audio import AudioRepository
from app.services.constants import FILE_HEADER_READ_SIZE
from app.services.s3_storage import S3StorageService


class AudioUploadService:
    def __init__(self, audio_repo: AudioRepository, audio_store: S3StorageService):
        self.audio_repo = audio_repo
        self.audio_store = audio_store

    async def handle_upload(self, audio_file: UploadFile) -> Audio:
        if not audio_file.filename:
            raise InvalidAudioFile("Uploaded file must have a filename")

        # Read just the start of the file so we can determine
        # if it's an expected audio type before reading the entire thing.
        # No point reading possibly lots of MB if the header is wrong.
        header = await audio_file.read(FILE_HEADER_READ_SIZE)

        guessed_type: Optional[Type] = guess_filetype(header)

        # noinspection PyUnreachableCode
        match guessed_type:
            case Mp3() | Wav():
                mimetype = guessed_type.mime
            case _:
                raise InvalidAudioFile("Unsupported audio file type")

        # File passed validation so move the cursor to the start
        await audio_file.seek(0)

        audio_bytes = await audio_file.read()

        sanitized_filename = Path(audio_file.filename).name

        audio = await self.audio_repo.create(
            Audio(
                filename=sanitized_filename,
                content_type=mimetype,
            )
        )

        await self.audio_store.store(cast(UUID, audio.id), audio_bytes)

        return audio
