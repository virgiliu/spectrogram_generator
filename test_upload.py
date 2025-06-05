import io
import mimetypes

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from constants import FILE_HEADER_READ_SIZE
from main import app

client = TestClient(app)


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"ID3"),  # Modern mp3 header
        (".mp3", b"\xff\xfb\xff\xf3\xff\xf2"),  # Legacy mp3 header
        (".wav", b"RIFF\x00\x00\x00\x00WAVE"),
    ],
)
def test_valid_audio_upload(ext, header):
    fake_audio = io.BytesIO(header + b"\x00" * FILE_HEADER_READ_SIZE)

    response = client.post(
        "/upload/",
        files={"audio_file": (f"test{ext}", fake_audio, mimetypes.types_map[ext])},
    )
    assert response.status_code == status.HTTP_200_OK, f"Response: {response.text}"


@pytest.mark.parametrize(
    "ext,header",
    [
        (".mp3", b"whatever"),
        (".jpg", b"\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01"),
        (".aac", b"\xff\xf1\x5c\x80\x2e\x7f\xfc\x21"),
    ],
)
def test_invalid_audio_upload(ext, header):
    invalid_file = io.BytesIO(header + b"\x00" * FILE_HEADER_READ_SIZE)
    response = client.post(
        "/upload/",
        files={"audio_file": (f"test{ext}", invalid_file, mimetypes.types_map[ext])},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
