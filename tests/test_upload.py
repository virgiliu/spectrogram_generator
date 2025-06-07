import io
import mimetypes
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.constants import FILE_HEADER_READ_SIZE
from app.events import AUDIO_UPLOADED
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_send_task():
    with patch("app.main.celery_app.send_task") as mock_send:
        yield mock_send


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"ID3"),  # Modern mp3 header
        (".mp3", b"\xff\xfb\xff\xf3\xff\xf2"),  # Legacy mp3 header
        (".wav", b"RIFF\x00\x00\x00\x00WAVE"),
    ],
)
def test_valid_audio_upload(mock_send_task, ext, header):
    fake_audio = io.BytesIO(header + b"\x00" * FILE_HEADER_READ_SIZE)

    response = client.post(
        "/upload",
        files={"audio_file": (f"test{ext}", fake_audio, mimetypes.types_map[ext])},
    )

    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"
    mock_send_task.assert_called_once_with(
        AUDIO_UPLOADED, args=[response.json()["audio_id"]]
    )


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"whatever"),
        (".jpg", b"\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01"),
        (".aac", b"\xff\xf1\x5c\x80\x2e\x7f\xfc\x21"),
    ],
)
def test_invalid_audio_upload(mock_send_task, ext, header):
    invalid_file = io.BytesIO(header + b"\x00" * FILE_HEADER_READ_SIZE)
    response = client.post(
        "/upload",
        files={"audio_file": (f"test{ext}", invalid_file, mimetypes.types_map[ext])},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_send_task.assert_not_called()


def test_missing_audio_file_returns_422(mock_send_task):
    response = client.post("/upload", files={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    mock_send_task.assert_not_called()
