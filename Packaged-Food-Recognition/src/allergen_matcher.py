"""Match normalized OCR text against the curated allergen lexicon."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from text_preprocessing import normalize_text

LEXICON = (
    Path(__file__).resolve().parents[1]
    / "Datasets"
    / "comprehensive_allergens_dataset.csv"
)


def load_keywords(path: Path = LEXICON) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def find_allergens(text: str, path: Path = LEXICON) -> list[dict[str, str]]:
    normalized = normalize_text(text)
    matches: dict[tuple[str, str], dict[str, str]] = {}
    for row in load_keywords(path):
        keyword = normalize_text(row["Keyword"])
        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
        if re.search(pattern, normalized, flags=re.UNICODE):
            key = (row["Allergen_Category"], keyword)
            matches[key] = {
                "allergen_category": row["Allergen_Category"],
                "matched_keyword": row["Keyword"],
            }
    return sorted(
        matches.values(),
        key=lambda item: (item["allergen_category"], item["matched_keyword"]),
    )
