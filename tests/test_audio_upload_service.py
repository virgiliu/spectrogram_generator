import mimetypes
from io import BytesIO
from typing import Generator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from app.exceptions import InvalidAudioFile
from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_PENDING
from app.services.audio_upload import AudioUploadService
from app.services.constants import FILE_HEADER_READ_SIZE


@pytest.fixture
def mock_repo() -> Generator[MagicMock, None, None]:
    repo = MagicMock()
    repo.create = AsyncMock(side_effect=lambda audio_obj: audio_obj)
    with patch("app.services.audio_upload.AudioRepository", return_value=repo):
        yield repo


@pytest.fixture
def mock_audio_store() -> MagicMock:
    store = MagicMock()
    store.store = AsyncMock()
    return store


@pytest.fixture
def service(mock_repo, mock_audio_store) -> AudioUploadService:
    return AudioUploadService(mock_repo, mock_audio_store)


def make_fake_audio_bytes(header: bytes) -> bytes:
    return header + b"\x00" * FILE_HEADER_READ_SIZE


def make_upload_file(ext: str, fake_audio_bytes: bytes) -> UploadFile:
    return UploadFile(filename=f"test{ext}", file=BytesIO(fake_audio_bytes))


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"ID3"),
        (".mp3", b"\xff\xfb\xff\xf3\xff\xf2"),
        (".wav", b"RIFF\x00\x00\x00\x00WAVE"),
    ],
)
@pytest.mark.asyncio
async def test_accepts_supported_audio_formats(
    service: AudioUploadService,
    mock_repo: MagicMock,
    ext: str,
    header: bytes,
):
    fake_audio_bytes = make_fake_audio_bytes(header)

    upload_file = make_upload_file(ext, fake_audio_bytes)

    audio: Audio = await service.handle_upload(upload_file)

    assert isinstance(audio, Audio)
    assert audio.filename == f"test{ext}"
    assert audio.content_type == mimetypes.types_map[ext]
    assert audio.status == AUDIO_STATUS_PENDING
    mock_repo.create.assert_awaited_once_with(audio)


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"whatever"),
        (".jpg", b"\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01"),
        (".aac", b"\xff\xf1\x5c\x80\x2e\x7f\xfc\x21"),
        (".empty", b""),
    ],
)
@pytest.mark.asyncio
async def test_rejects_unsupported_audio_formats(
    service: AudioUploadService,
    mock_repo: MagicMock,
    ext: str,
    header: bytes,
):
    fake_audio_bytes = make_fake_audio_bytes(header)
    upload_file = make_upload_file(ext, fake_audio_bytes)

    with pytest.raises(InvalidAudioFile):
        await service.handle_upload(upload_file)

    mock_repo.create.assert_not_called()


@pytest.mark.parametrize("filename", [None, ""])
@pytest.mark.asyncio
async def test_rejects_audio_without_filename(
    filename: Optional[str], service: AudioUploadService, mock_repo: MagicMock
):
    upload_file = UploadFile(filename=filename, file=BytesIO(b""))

    with pytest.raises(InvalidAudioFile) as exc_info:
        await service.handle_upload(upload_file)

    assert "must have a filename" in str(exc_info.value)
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_filenames_are_sanitized(
    service: AudioUploadService, mock_repo: MagicMock
):
    fake_audio_bytes = make_fake_audio_bytes(b"ID3")
    audio_filename = "h4x0rz.mp3"
    upload_file = UploadFile(
        filename=f"../path/to/{audio_filename}", file=BytesIO(fake_audio_bytes)
    )

    audio: Audio = await service.handle_upload(upload_file)

    assert audio.filename == audio_filename
    mock_repo.create.assert_awaited_once_with(audio)
