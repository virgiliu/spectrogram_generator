import asyncio
import logging
from mimetypes import types_map
from uuid import UUID

from botocore.exceptions import ClientError

from app.celery_app import celery_app, get_audio_store, get_spectrogram_store
from app.db import scoped_session
from app.events import AUDIO_UPLOADED
from app.repositories.audio import AudioRepository
from app.services.spectrogram import generate_spectrogram

logger = logging.getLogger(__name__)


@celery_app.task(
    name=AUDIO_UPLOADED,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def handle_audio_uploaded(audio_id: UUID) -> None:
    asyncio.get_event_loop().run_until_complete(_handle_audio_uploaded_async(audio_id))


async def _handle_audio_uploaded_async(audio_id: UUID) -> None:
    async with scoped_session() as session:
        repo = AudioRepository(session)
        audio = await repo.get_by_id(audio_id)

        if audio is None:
            logger.warning(f"[WORKER] Audio with ID {audio_id} was not found")
            return

        # Store filename for later use in last log message.
        # Session will be closed when that log happens and trying to access `audio.filename` will raise Exception.
        filename = audio.filename

        logger.info(f"[WORKER] Handling audio ID {audio_id}, filename {filename}")

        try:
            audio_bytes = await get_audio_store().retrieve(audio_id)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                logger.fatal(
                    f"[WORKER] Audio with ID {audio_id} was not found in store but worker got a task to process it"
                )
            raise

        image_bytes = generate_spectrogram(audio_bytes, filename)

        await get_spectrogram_store().store(audio_id, image_bytes, types_map[".png"])

        await repo.mark_done(audio_id)

        logger.info(
            f"[WORKER] Finished handling audio ID {audio_id}, filename {filename}"
        )
