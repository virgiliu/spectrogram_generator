from io import BytesIO

import librosa
import matplotlib

from app.exceptions import SpectrogramGenerationError

# Switch the matplotlib backend to non-GUI. Must be before importing pyplot!
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import spectrogram


def generate_spectrogram(audio_bytes: bytes, filename: str) -> bytes:

    try:
        # Load audio data without resampling nor converting to mono
        audio_data, sample_rate = librosa.load(
            BytesIO(audio_bytes), sr=None, mono=False
        )
    except Exception as exc:
        raise SpectrogramGenerationError(f"Failed to read audio data: {exc}")

    # If mono audio, reshape the audio data to (1, n) for consistency, helps keep
    # the plotting code cleaner later on
    if audio_data.ndim == 1:
        audio_data = audio_data[np.newaxis, :]

    fig, axes = plt.subplots(
        audio_data.shape[0], 1, figsize=(10, 4 * audio_data.shape[0])
    )

    if audio_data.shape[0] == 1:
        axes = [axes]

    for ch, ax in enumerate(axes):
        # noinspection PyPep8Naming
        f, t, Sxx = spectrogram(audio_data[ch], sample_rate)
        ax.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading="gouraud")
        ax.set(
            ylabel="Frequency [Hz]",
            xlabel="Time [s]",
            title=f"Channel {ch + 1}",
        )

    fig.suptitle(filename, fontsize=16)

    buf = BytesIO()
    try:
        fig.tight_layout()
        fig.savefig(buf, format="png")
    finally:
        plt.close(fig)

    buf.seek(0)
    return buf.read()
