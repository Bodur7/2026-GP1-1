"""Extract Arabic and English text from a packaged-food label image."""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageOps


def preprocess_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("L")
    image = ImageOps.autocontrast(image)
    return ImageEnhance.Sharpness(image).enhance(1.5)


def extract_text(path: Path, languages: str = "ara+eng") -> str:
    return pytesseract.image_to_string(preprocess_image(path), lang=languages)
