from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Annotated

import librosa
import matplotlib

from app.repositories.audio import AudioRepository

# Switch the matplotlib backend to non-GUI. Must be before importing pyplot!
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from filetype import guess as guess_filetype
from filetype.types.audio import Mp3, Wav
from filetype.types.base import Type
from scipy.signal import spectrogram

from app.constants import FILE_HEADER_READ_SIZE
import app.db as db
from app.models.audio import Audio


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_audio(
    audio_file: Annotated[UploadFile, File(description="mp3 or wav file")],
):
    # Read just the start of the file so we can determine
    # if it's an expected audio type before reading the entire thing
    header = await audio_file.read(FILE_HEADER_READ_SIZE)

    audio_file.file.seek(0)

    guessed_type: Type | None = guess_filetype(header)

    # noinspection PyUnreachableCode
    match guessed_type:
        case Mp3() | Wav():
            mimetype = guessed_type.mime
        case _:
            raise HTTPException(status_code=400, detail="Unsupported audio file type")

    audio_bytes = await audio_file.read()
    img_path = await generate_spectrogram(audio_bytes, audio_file.filename)

    with db.get_session() as session:
        repo = AudioRepository(session)
        uploaded_file = repo.create(
            Audio(filename=audio_file.filename, content_type=mimetype, data=audio_bytes)
        )

    return {
        "filename": audio_file.filename,
        "mimetype": mimetype,
        "spectrogram_path": str(img_path),
        "upload_id": uploaded_file.id,
    }


async def generate_spectrogram(audio_bytes: bytes, filename: str) -> Path:
    try:
        # Load audio data without resampling nor converting to mono
        audio_data, sample_rate = librosa.load(
            BytesIO(audio_bytes), sr=None, mono=False
        )

        # If mono, reshape the audio data to (1, n) for consistency, helps keep
        # the plotting code cleaner later on
        if audio_data.ndim == 1:
            audio_data = audio_data[np.newaxis, :]

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read audio data: {exc}")

    output_dir = Path.cwd() / "output"
    output_dir.mkdir(exist_ok=True)

    img_path = output_dir / f"{Path(filename).stem}_spectrogram.png"
    fig, axes = plt.subplots(
        audio_data.shape[0], 1, figsize=(10, 4 * audio_data.shape[0])
    )

    if audio_data.shape[0] == 1:
        axes = [axes]

    for ch, ax in enumerate(axes):
        # noinspection PyPep8Naming
        f, t, Sxx = spectrogram(audio_data[ch], sample_rate)
        ax.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading="gouraud")
        ax.set_ylabel("Frequency [Hz]")
        ax.set_xlabel("Time [s]")
        ax.set_title(f"Channel {ch + 1}")

    fig.tight_layout()
    fig.savefig(img_path)
    plt.close(fig)

    return img_path
