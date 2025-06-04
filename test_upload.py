import io
import mimetypes

from fastapi import status
from fastapi.testclient import TestClient

from constants import FILE_HEADER_READ_SIZE
from main import app

client = TestClient(app)


def test_valid_mp3_upload():
    # Fake an mp3 header to pass mimetype detection

    fake_mp3 = io.BytesIO(b"ID3" + b"\x00" * FILE_HEADER_READ_SIZE)

    response = client.post(
        "/upload/",
        files={"audio_file": ("test.mp3", fake_mp3, mimetypes.types_map[".mp3"])},
    )
    assert response.status_code == status.HTTP_200_OK
