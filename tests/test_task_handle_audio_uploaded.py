from mimetypes import types_map
from typing import Generator, cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from botocore.exceptions import ClientError

from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_PENDING
from app.tasks.audio import _handle_audio_uploaded_async


@pytest.fixture
def fake_audio() -> Audio:
    return Audio(
        id=uuid4(),
        filename="test.wav",
        content_type="audio/wav",
        status=AUDIO_STATUS_PENDING,
    )


@pytest.fixture
def mock_repo(fake_audio: Audio) -> Generator[MagicMock, None, None]:
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=fake_audio)
    repo.mark_done = AsyncMock(return_value=None)
    with patch("app.tasks.audio.AudioRepository", return_value=repo):
        yield repo


@pytest.fixture
def patch_audio_and_spectrogram_store():
    expected_data = b"Ave fornicatio et sacrilegum"

    audio_store = MagicMock()
    audio_store.store = AsyncMock()
    audio_store.retrieve = AsyncMock(return_value=expected_data)
    audio_store._expected_data = expected_data

    spectrogram_store = MagicMock()
    spectrogram_store.store = AsyncMock()

    with (
        patch("app.tasks.audio.get_audio_store", return_value=audio_store),
        patch("app.tasks.audio.get_spectrogram_store", return_value=spectrogram_store),
    ):
        yield audio_store, spectrogram_store


@pytest.fixture
def patch_generate_spectrogram() -> Generator[MagicMock, None, None]:
    with patch(
        "app.tasks.audio.generate_spectrogram",
        return_value=b"Oremus per coitum, et patris Deum",
    ) as patched:
        yield patched


@pytest.mark.asyncio
async def test_worker_handles_valid_audio(
    patch_generate_spectrogram: MagicMock,
    patch_audio_and_spectrogram_store: MagicMock,
    mock_repo: MagicMock,
    fake_audio: Audio,
):
    await _handle_audio_uploaded_async(cast(UUID, fake_audio.id))
    audio_store, spectrogram_store = patch_audio_and_spectrogram_store

    mock_repo.get_by_id.assert_awaited_once_with(fake_audio.id)
    audio_store.retrieve.assert_awaited_once_with(fake_audio.id)

    patch_generate_spectrogram.assert_called_once_with(
        audio_store._expected_data, fake_audio.filename
    )

    spectrogram_store.store.assert_called_once_with(
        fake_audio.id, patch_generate_spectrogram.return_value, types_map[".png"]
    )
    mock_repo.mark_done.assert_awaited_once_with(fake_audio.id)


@pytest.mark.asyncio
async def test_worker_handles_missing_audio_from_db(
    patch_generate_spectrogram: MagicMock,
    patch_audio_and_spectrogram_store: MagicMock,
    mock_repo: MagicMock,
):
    audio_store, spectrogram_store = patch_audio_and_spectrogram_store

    inexistent_audio_id = uuid4()
    mock_repo.get_by_id.return_value = None

    await _handle_audio_uploaded_async(inexistent_audio_id)

    patch_generate_spectrogram.assert_not_called()
    audio_store.retrieve.assert_not_called()
    spectrogram_store.store.assert_not_called()
    mock_repo.get_by_id.assert_awaited_once_with(inexistent_audio_id)
    mock_repo.mark_done.assert_not_called()


@pytest.mark.asyncio
async def test_worker_doesnt_raise_on_audio_missing_from_store(
    patch_generate_spectrogram: MagicMock,
    patch_audio_and_spectrogram_store: MagicMock,
    mock_repo: MagicMock,
    fake_audio: Audio,
):

    audio_store, spectrogram_store = patch_audio_and_spectrogram_store

    audio_store.retrieve.return_value = None
    audio_store.retrieve.side_effect = ClientError(
        {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        "GetObject",
    )

    with pytest.raises(ClientError) as exc:
        await _handle_audio_uploaded_async(cast(UUID, fake_audio.id))

    assert (
        exc.value.response["Error"]["Code"]
        == audio_store.retrieve.side_effect.response["Error"]["Code"]
    )
    mock_repo.get_by_id.assert_awaited_once_with(fake_audio.id)
    patch_generate_spectrogram.assert_not_called()
    audio_store.retrieve.assert_called_once_with(fake_audio.id)
    spectrogram_store.store.assert_not_called()
    mock_repo.mark_done.assert_not_called()


@pytest.mark.asyncio
async def test_worker_raises_if_mark_done_fails(
    patch_generate_spectrogram: MagicMock,
    patch_audio_and_spectrogram_store: MagicMock,
    mock_repo: MagicMock,
    fake_audio: Audio,
):
    audio_store, spectrogram_store = patch_audio_and_spectrogram_store

    mock_repo.mark_done.side_effect = RuntimeError("DB fail")

    with pytest.raises(RuntimeError, match="DB fail"):
        await _handle_audio_uploaded_async(cast(UUID, fake_audio.id))

    patch_generate_spectrogram.assert_called_once_with(
        audio_store._expected_data, fake_audio.filename
    )
    spectrogram_store.store.assert_called_once_with(
        fake_audio.id, patch_generate_spectrogram.return_value, types_map[".png"]
    )

    mock_repo.mark_done.assert_awaited_once_with(fake_audio.id)


@pytest.mark.asyncio
async def test_worker_raises_if_spectrogram_generation_fails(
    patch_generate_spectrogram: MagicMock,
    patch_audio_and_spectrogram_store: MagicMock,
    mock_repo: MagicMock,
    fake_audio: Audio,
):
    audio_store, spectrogram_store = patch_audio_and_spectrogram_store

    patch_generate_spectrogram.side_effect = RuntimeError("OH NO")

    with pytest.raises(RuntimeError, match="OH NO"):
        await _handle_audio_uploaded_async(cast(UUID, fake_audio.id))

    patch_generate_spectrogram.assert_called_once_with(
        audio_store._expected_data, fake_audio.filename
    )
    spectrogram_store.store.assert_not_called()
    mock_repo.mark_done.assert_not_called()
