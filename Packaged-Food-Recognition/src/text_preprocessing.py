"""Normalize bilingual OCR text before allergen matching."""

from __future__ import annotations

import re
import unicodedata

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()
