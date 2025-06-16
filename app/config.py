from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",  # Assumes application is run from project root
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="SPGE_",  # SPGE = SPectrogram GEnerator
    )

    DATABASE_URL: str
    CELERY_BROKER_URL: str


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
