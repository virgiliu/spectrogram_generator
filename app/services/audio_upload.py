from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from filetype import guess as guess_filetype
from filetype.types.audio import Mp3, Wav
from filetype.types.base import Type
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import InvalidAudioFile
from app.models.audio import Audio
from app.repositories.audio import AudioRepository
from app.services.constants import FILE_HEADER_READ_SIZE


class AudioUploadService:
    def __init__(self, session: AsyncSession):
        self.session = session

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

        repo = AudioRepository(self.session)

        return await repo.create(
            Audio(
                filename=sanitized_filename,
                content_type=mimetype,
                data=audio_bytes,
            )
        )
