"""Run OCR and allergen keyword screening for one label image."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from allergen_matcher import find_allergens
from ocr import extract_text


def analyze_label(image: Path) -> dict:
    text = extract_text(image)
    return {
        "image": str(image),
        "ocr_text": text,
        "allergen_matches": find_allergens(text),
        "decision": "review_required",
        "disclaimer": "Keyword screening is not a medical or regulatory safety determination.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze_label(args.image), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
