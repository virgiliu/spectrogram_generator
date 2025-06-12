from contextlib import contextmanager
from threading import Lock
from typing import Generator, Optional

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import Settings

_engine_lock = Lock()
_engine: Optional[Engine] = None


def _create_engine(settings: Settings) -> Engine:
    if settings is None:
        raise ValueError("Settings cannot be None")

    engine = create_engine(settings.database_url, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


def init(settings: Settings) -> Engine:
    """Initialise and return the global database engine."""

    global _engine
    if _engine is not None:
        with _engine_lock:
            if (
                _engine is None
            ):  # re-check engine just in case another thread called init in the meantime
                _engine = _create_engine(settings)
        return _engine

    _engine = _create_engine(settings)

    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError(
            "Database engine has not been initialised; call init() first"
        )
    return _engine


def destroy_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def session_generator() -> Generator[Session, None, None]:
    """This generator is intended for use with ``Depends`` in API routes. Yields a session for FastAPI dependencies."""
    with Session(get_engine()) as session:
        yield session


@contextmanager
def scoped_session() -> Generator[Session, None, None]:
    """Context manager that provides a session for background tasks.

    Use ``scoped_session`` over ``session_generator`` when you need an explicit ``with`` block (e.g.: in Celery tasks).
    """

    with Session(get_engine()) as session:
        yield session
