import mimetypes
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from app.exceptions import InvalidAudioFile
from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_PENDING
from app.repositories.audio import AudioRepository
from app.services.audio_upload import AudioUploadService
from app.services.constants import FILE_HEADER_READ_SIZE


@pytest.fixture
def mock_repo() -> AudioRepository:
    repo = MagicMock()
    repo.create.side_effect = lambda audio_obj: audio_obj
    return repo


@pytest.fixture(autouse=True)
def patch_audio_repository(mock_repo: MagicMock):
    with patch("app.services.audio_upload.AudioRepository", return_value=mock_repo):
        yield


@pytest.fixture
def service() -> AudioUploadService:
    session_factory = MagicMock()
    return AudioUploadService(session_factory)


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
    mock_repo.create.assert_called_once_with(audio)


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"whatever"),
        (".jpg", b"\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01"),
        (".aac", b"\xff\xf1\x5c\x80\x2e\x7f\xfc\x21"),
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
