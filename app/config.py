from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///db.sqlite3"
    celery_broker_url: str = "redis://localhost:6379/0"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
