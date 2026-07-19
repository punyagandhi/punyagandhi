"""
prep_photo.py

Turns a regular photo into a clean grayscale image, ready for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg

Writes:
    source-prepped.png   (same folder as the input, grayscale, white background)
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def remove_background(input_path: Path) -> Image.Image:
    """Return an RGBA PIL image with the background made transparent."""
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    with open("_tmp_nobg.png", "wb") as f:
        f.write(output_bytes)
    return Image.open("_tmp_nobg.png").convert("RGBA")


def boost_contrast(gray: np.ndarray) -> np.ndarray:
    """Apply CLAHE (contrast-limited adaptive histogram equalization).

    A flatly-lit face converts to a dark, unreadable blob without this —
    CLAHE gives it real highlights and shadows to work with.
    """
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def composite_on_white(rgba: Image.Image, gray: np.ndarray) -> Image.Image:
    """Paste the (now contrast-boosted) subject onto a pure white canvas.

    Pure white background maps to the blank end of the ASCII ramp later,
    so only the subject actually prints as characters.
    """
    alpha = np.array(rgba.split()[-1])  # transparency mask from rembg
    canvas = np.full_like(gray, 255)  # solid white
    alpha_f = alpha.astype(np.float32) / 255.0
    blended = (gray.astype(np.float32) * alpha_f + canvas.astype(np.float32) * (1 - alpha_f))
    return Image.fromarray(blended.astype(np.uint8), mode="L")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py source-photo.jpg")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    print("Removing background...")
    rgba = remove_background(input_path)

    print("Converting to grayscale...")
    gray = cv2.cvtColor(np.array(rgba.convert("RGB")), cv2.COLOR_RGB2GRAY)

    print("Boosting contrast (CLAHE)...")
    gray = boost_contrast(gray)

    print("Compositing onto white background...")
    result = composite_on_white(rgba, gray)

    out_path = input_path.with_name(input_path.stem + "-prepped.png")
    result.save(out_path)
    print(f"Done -> {out_path}")

    # cleanup temp file
    Path("_tmp_nobg.png").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
