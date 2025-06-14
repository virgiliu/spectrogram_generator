from contextlib import asynccontextmanager
from threading import Lock
from typing import AsyncGenerator, AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import Settings

_engine_lock = Lock()
_engine: Optional[AsyncEngine] = None


async def _create_engine(settings: Settings) -> AsyncEngine:
    if settings is None:
        raise ValueError("Settings cannot be None")

    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    return engine


async def init(settings: Settings) -> AsyncEngine:
    """Initialise and return the global database engine."""

    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:  # re-check, in case another thread set it already
                _engine = await _create_engine(settings)

    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError(
            "Database engine has not been initialised; call init() first"
        )
    return _engine


async def destroy_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def session_generator() -> AsyncGenerator[AsyncSession, None]:
    """This generator is intended for use with ``Depends`` in API routes. Yields a session for FastAPI dependencies."""
    async with AsyncSession(get_engine()) as session:
        yield session


@asynccontextmanager
async def scoped_session() -> AsyncIterator[AsyncSession]:
    """Context manager that provides a session for background tasks.

    Use ``scoped_session`` over ``session_generator`` when you need an explicit ``with`` block (e.g.: in Celery tasks).
    """

    async with AsyncSession(get_engine()) as session:
        yield session
