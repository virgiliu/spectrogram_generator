import logging
from pathlib import Path

from app.celery_app import celery_app
from app.db import scoped_session
from app.events import AUDIO_UPLOADED
from app.repositories.audio import AudioRepository
from app.services.spectrogram import generate_spectrogram

logger = logging.getLogger(__name__)


@celery_app.task(
    name=AUDIO_UPLOADED,
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def handle_audio_uploaded(self, audio_id: int) -> None:
    with scoped_session() as session:
        repo = AudioRepository(session)
        audio = repo.get_by_id(audio_id)
        if audio is None:
            logger.warning(f"Audio with ID {audio_id} was not found")
            return
        logger.info(f"[WORKER] Handling audio ID {audio.id}, filename {audio.filename}")

        image_bytes = generate_spectrogram(audio.data, audio.filename)

        output_dir = Path.cwd() / "output"
        output_dir.mkdir(exist_ok=True)

        img_path = output_dir / f"{Path(audio.filename)}_spectrogram.png"

        with open(img_path, "wb") as f:
            f.write(image_bytes)

        repo.mark_done(audio_id)
        logger.info(
            f"[WORKER] Finished handling audio ID {audio.id}, filename {audio.filename}"
        )
