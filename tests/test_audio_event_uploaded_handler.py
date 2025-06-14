from io import BytesIO
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_PENDING
from app.tasks.audio import handle_audio_uploaded


@pytest.fixture
def fake_audio() -> Audio:
    return Audio(
        id=1338,
        filename="test.wav",
        content_type="audio/wav",
        data=b"whatever",
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
def mock_open() -> Generator[MagicMock, None, None]:
    with patch("builtins.open", side_effect=lambda *a, **k: BytesIO()) as open_mock:
        yield open_mock


@pytest.fixture
def patch_generate_spectrogram() -> Generator[MagicMock, None, None]:
    with patch(
        "app.tasks.audio.generate_spectrogram", return_value=b"fake bytes"
    ) as patched:
        yield patched


def test_worker_handles_valid_audio(
    patch_generate_spectrogram: MagicMock,
    mock_repo: MagicMock,
    mock_open: MagicMock,
    fake_audio: Audio,
):
    handle_audio_uploaded(fake_audio.id)

    mock_repo.get_by_id.assert_awaited_once_with(fake_audio.id)

    patch_generate_spectrogram.assert_called_once_with(
        fake_audio.data, fake_audio.filename
    )

    mock_open.assert_called_once()

    mock_repo.mark_done.assert_awaited_once_with(fake_audio.id)


def test_worker_handles_missing_audio(
    patch_generate_spectrogram: MagicMock, mock_repo: MagicMock
):
    invalid_audio_id = -1
    mock_repo.get_by_id.return_value = None

    handle_audio_uploaded(invalid_audio_id)

    patch_generate_spectrogram.assert_not_called()
    mock_repo.get_by_id.assert_awaited_once_with(invalid_audio_id)
    mock_repo.mark_done.assert_not_called()


def test_worker_raises_if_mark_done_fails(
    patch_generate_spectrogram: MagicMock,
    mock_repo: MagicMock,
    mock_open: MagicMock,
    fake_audio: Audio,
):
    mock_repo.mark_done.side_effect = RuntimeError("DB fail")

    with pytest.raises(RuntimeError, match="DB fail"):
        handle_audio_uploaded(fake_audio.id)

    patch_generate_spectrogram.assert_called_once_with(
        fake_audio.data, fake_audio.filename
    )

    mock_open.assert_called_once()
    mock_repo.mark_done.assert_awaited_once_with(fake_audio.id)


def test_worker_raises_if_spectrogram_generation_fails(
    patch_generate_spectrogram: MagicMock,
    mock_repo: MagicMock,
    mock_open: MagicMock,
    fake_audio: Audio,
):
    patch_generate_spectrogram.side_effect = RuntimeError("OH NO")

    with pytest.raises(RuntimeError, match="OH NO"):
        handle_audio_uploaded(fake_audio.id)

    patch_generate_spectrogram.assert_called_once_with(
        fake_audio.data, fake_audio.filename
    )
    mock_open.assert_not_called()
    mock_repo.mark_done.assert_not_called()
