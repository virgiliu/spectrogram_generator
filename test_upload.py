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
        (".mp3", b"ID3"),
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
