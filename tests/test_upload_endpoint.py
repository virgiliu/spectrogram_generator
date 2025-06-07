import mimetypes
from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.events import AUDIO_UPLOADED
from app.exceptions import InvalidAudioFile
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_send_task():
    with patch("app.main.celery_app.send_task") as mock_send:
        yield mock_send


@pytest.fixture
def mock_upload_service():
    with patch("app.main.AudioUploadService.handle_upload") as mock_upload:
        yield mock_upload


@pytest.fixture
def upload_fake_mp3():
    def upload(files=None):
        if files is None:
            files = {
                "audio_file": (
                    "test.mp3",
                    BytesIO(b"eeeehMACARENA"),
                    mimetypes.types_map[".mp3"],
                )
            }
        return client.post("/upload", files=files)

    return upload


def test_valid_audio_upload(mock_send_task, mock_upload_service, upload_fake_mp3):
    test_audio_id = 1337
    id_key = "audio_id"
    mock_upload_service.return_value = Mock(id=test_audio_id)

    response = upload_fake_mp3()

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {id_key: test_audio_id}
    mock_send_task.assert_called_once_with(
        AUDIO_UPLOADED, args=[response.json()[id_key]]
    )


def test_invalid_audio_upload(mock_send_task, mock_upload_service, upload_fake_mp3):
    mock_upload_service.side_effect = InvalidAudioFile
    response = upload_fake_mp3()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_send_task.assert_not_called()


def test_missing_audio_file_returns_422(mock_send_task, upload_fake_mp3):
    response = upload_fake_mp3(files={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    mock_send_task.assert_not_called()
