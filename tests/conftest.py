import pytest

from app import db
from app.config import Settings, get_settings
from app.main import app


@pytest.fixture(autouse=True, scope="function")
def setup_in_memory_db():
    test_settings = Settings(database_url="sqlite:///:memory:")

    app.dependency_overrides[get_settings] = lambda: test_settings

    db.destroy_engine()
    db.init(test_settings)

    yield

    app.dependency_overrides.clear()
    db.destroy_engine()
