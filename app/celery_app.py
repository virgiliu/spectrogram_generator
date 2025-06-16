from functools import lru_cache

from celery import Celery
from celery.signals import worker_process_init

from app import db
from app.config import get_settings


@worker_process_init.connect
def _init_db(**_):
    """
    Initialize the SQLAlchemy engine inside every Celery worker process.
    FastAPI runs its own db.init() at startup, this covers the worker side.
    """
    db.init(get_settings())


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


celery_app = _get_celery_app()
