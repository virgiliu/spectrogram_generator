import asyncio

import pytest
import pytest_asyncio
from sqlmodel import SQLModel

from app import db
from app.config import Settings, get_settings
from app.db import scoped_session
from app.main import app


@pytest.fixture(autouse=True, scope="function")
def setup_in_memory_db():
    test_settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")

    app.dependency_overrides[get_settings] = lambda: test_settings

    # Use asyncio.run() instead of making the fixture async and awaiting because
    # several tests are synchronous and then they would have to be executed in an event loop.
    # This way, nothing forces sync tests to be wrapped in `pytest.mark.asyncio`.
    asyncio.run(db.destroy_engine())
    db.init(test_settings)

    # Create schema from models directly instead of relying on alembic.
    engine = db.get_engine()

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.run(_create_tables())

    yield

    app.dependency_overrides.clear()
    asyncio.run(db.destroy_engine())


@pytest_asyncio.fixture
async def session():
    async with scoped_session() as session:
        yield session
