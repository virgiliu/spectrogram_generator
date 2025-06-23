import asyncio
from contextlib import AsyncExitStack
from functools import lru_cache
from typing import Any, Dict

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app import db
from app.config import get_settings
from app.services.constants import AUDIO_BUCKET, SPECTROGRAM_BUCKET
from app.services.s3_storage import S3StorageService, open_s3_stores

_audio_store: S3StorageService | None = None
_spectrogram_store: S3StorageService | None = None
_s3_context_manager_stack: AsyncExitStack | None = None


def get_audio_store() -> S3StorageService:
    if _audio_store is None:
        raise RuntimeError("_audio_store is not initialized")

    return _audio_store


def get_spectrogram_store() -> S3StorageService:
    if _spectrogram_store is None:
        raise RuntimeError("_spectrogram_store is not initialized")

    return _spectrogram_store


@worker_process_init.connect
def _init_resources(**_: Any) -> None:
    """Runs once per worker and does the following:
    1) Initialize the SQLAlchemy engine inside every Celery worker process.
    FastAPI runs its own db.init() at startup, this covers the worker side.
    2) Open S3 clients and keeps them open
    """
    db.init(get_settings())

    async def _setup() -> None:
        global _audio_store, _spectrogram_store, _s3_context_manager_stack
        _s3_context_manager_stack = AsyncExitStack()
        # enter_async_context keeps open_s3_stores alive for the worker lifetime
        stores: Dict[str, S3StorageService] = (
            await _s3_context_manager_stack.enter_async_context(
                open_s3_stores(AUDIO_BUCKET, SPECTROGRAM_BUCKET)
            )
        )
        _audio_store = stores[AUDIO_BUCKET]
        _spectrogram_store = stores[SPECTROGRAM_BUCKET]

    asyncio.get_event_loop().run_until_complete(_setup())


@worker_process_shutdown.connect
def _close_resources(**_: Any) -> None:
    """Called once when the worker process exits.
    Cleans up DB engine and S3 clients."""

    async def _cleanup() -> None:
        if _s3_context_manager_stack is not None:
            await _s3_context_manager_stack.aclose()
        await db.destroy_engine()

    asyncio.get_event_loop().run_until_complete(_cleanup())


@lru_cache()
def _get_celery_app() -> Celery:
    settings = get_settings()

    _celery_app = Celery(
        "tasks", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BROKER_URL
    )

    _celery_app.conf.task_acks_late = True
    _celery_app.conf.worker_prefetch_multiplier = 1
    _celery_app.conf.task_acks_on_failure_or_timeout = False
    _celery_app.autodiscover_tasks(["app.tasks"], related_name="audio")

    return _celery_app


celery_app: Celery = _get_celery_app()
