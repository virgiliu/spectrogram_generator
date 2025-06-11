import os
import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageOps

from app.exceptions import SpectrogramGenerationError
from app.services.spectrogram import generate_spectrogram

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXPECTED_OUTPUTS_DIR = FIXTURES_DIR / "expected_outputs"


def make_red_overlay_diff(img_a: Image.Image, img_b: Image.Image) -> Image.Image:
    """Overlay red on differing pixels for human-friendly visual diff."""

    diff = ImageChops.difference(img_a, img_b).convert("L")
    diff = ImageOps.autocontrast(diff)

    overlay = img_a.convert("RGBA")

    red_mask = Image.new("RGBA", img_a.size, (255, 0, 0, 0))

    # Map diff intensity to alpha channel for red overlay
    for y in range(img_a.height):
        for x in range(img_a.width):
            alpha = diff.getpixel((x, y))

            # For mode "L" (greyscale), getpixel() should return int, not tuple, but let's just make sure anyway
            if isinstance(alpha, tuple):
                alpha = alpha[0]

            if alpha:
                # Amplify alpha for visibility, but clamp to 255
                red_mask.putpixel((x, y), (255, 0, 0, int(min(255, alpha * 2))))

    return Image.alpha_composite(overlay, red_mask).convert("RGB")


@pytest.mark.parametrize(
    "input_filename", ["mono.wav", "stereo.wav", "mono.mp3", "stereo.mp3"]
)
def test_generate_spectrogram_matches_expected(input_filename: str):
    audio_path = FIXTURES_DIR / input_filename
    expected_img_path = EXPECTED_OUTPUTS_DIR / f"{input_filename}_spectrogram.png"

    with audio_path.open("rb") as audio_file:
        audio_bytes = audio_file.read()

    output_bytes = generate_spectrogram(audio_bytes, input_filename)

    img_output = Image.open(BytesIO(output_bytes)).convert("RGB")
    img_expected = Image.open(expected_img_path).convert("RGB")

    diff = ImageChops.difference(img_output, img_expected)

    if diff.getbbox():
        debug_env = "SPECTROGRAM_DEBUG_DIFF"

        err_msg = (
            f"\nSpectrogram for {input_filename} does not match expected output.\n"
        )

        if os.environ.get(debug_env):
            overlay_img = make_red_overlay_diff(img_output, img_expected)

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                overlay_img.save(tmp, format="PNG")
                print(f"\n[DIFF IMAGE SAVED]: {tmp.name}")

            raise AssertionError(f"{err_msg}See diff image at: {tmp.name}")

        else:
            raise AssertionError(
                f"{err_msg}To debug visually, set the env var {debug_env}=1 to save diff images."
            )


@pytest.mark.parametrize(
    "bad_bytes",
    [
        b"",
        b"this is not audio",
        b"ID3",
        b"RIFF\x00\x00\x00\x00WAVE",
        b"\xff\xfb\xff\xf3\xff\xf2",
        None,
        -3,
        "Zeit, bitte bleib stehen, bleib stehen",
        {},
        object(),
    ],
)
def test_generate_spectrogram_invalid_input(bad_bytes):
    with pytest.raises(SpectrogramGenerationError):
        generate_spectrogram(bad_bytes, "fake.mp3")
