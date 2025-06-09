import mimetypes
from datetime import datetime
from typing import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_DONE, AUDIO_STATUS_PENDING
from app.repositories.audio import AudioRepository


@pytest.fixture
def sqlite_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(sqlite_engine: Engine) -> Generator[Session, None, None]:
    with Session(sqlite_engine) as session:
        yield session


@pytest.fixture
def repo(session: Session) -> AudioRepository:
    return AudioRepository(session)


@pytest.fixture
def created_audio(repo: AudioRepository) -> Audio:
    return repo.create(
        Audio(
            filename="test.wav",
            content_type=mimetypes.types_map[".wav"],
            data=b"Hand in Hand, nie mehr allein",
            status=AUDIO_STATUS_PENDING,
        )
    )


def ensure_id(audio: Audio) -> int:
    """Assert and return the id of an Audio instance.

    The model defines ID as Optional[int] and mypy doesn't know that after INSERT an ID is assigned and it is no longer None.

    Use this to guarantee an int for type checking and to stop mypy from crying.
    """
    assert audio.id is not None
    return audio.id


def test_create_adds_audio_and_assigns_id(repo: AudioRepository, created_audio: Audio):
    saved = repo.create(created_audio)

    exclude_fields = {"id", "created_at"}

    expected = created_audio.model_dump(exclude=exclude_fields)
    actual = saved.model_dump(exclude=exclude_fields)

    assert actual == expected
    assert saved.id is not None
    assert isinstance(saved.created_at, datetime)


def test_get_by_id_returns_audio(repo: AudioRepository, created_audio: Audio):
    fetched = repo.get_by_id(ensure_id(created_audio))

    assert fetched is not None
    assert fetched.model_dump() == created_audio.model_dump()  # type: ignore[union-attr]


def test_get_by_id_returns_none_if_missing(repo: AudioRepository):
    assert repo.get_by_id(1) is None


def test_mark_done_sets_status_to_done(repo: AudioRepository, created_audio: Audio):
    created_audio_id = ensure_id(created_audio)

    repo.mark_done(created_audio_id)

    updated = repo.get_by_id(created_audio_id)
    assert updated is not None
    assert updated.status == AUDIO_STATUS_DONE


def test_mark_done_noop_if_missing(repo: AudioRepository):
    repo.mark_done(1)

    assert repo.get_by_id(1) is None


def test_mark_done_idempotent(repo: AudioRepository, created_audio: Audio):
    created_audio_id = ensure_id(created_audio)

    repo.mark_done(created_audio_id)
    # Call 2nd time intentionally to test for side effects that might break idempotency
    repo.mark_done(created_audio_id)

    updated = repo.get_by_id(created_audio_id)

    assert updated is not None
    assert updated.status == AUDIO_STATUS_DONE
    assert created_audio.model_dump(exclude={"status"}) == updated.model_dump(
        exclude={"status"}
    )
