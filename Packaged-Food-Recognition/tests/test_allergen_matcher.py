from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allergen_matcher import find_allergens  # noqa: E402
from text_preprocessing import normalize_text  # noqa: E402


class AllergenMatcherTests(unittest.TestCase):
    def test_english_derived_ingredient(self) -> None:
        categories = {
            item["allergen_category"] for item in find_allergens("Ingredients: whey, sugar")
        }
        self.assertIn("Dairy allergy", categories)

    def test_arabic_direct_ingredient(self) -> None:
        categories = {
            item["allergen_category"] for item in find_allergens("المكونات: حليب وسكر")
        }
        self.assertIn("Dairy allergy", categories)

    def test_arabic_normalization(self) -> None:
        self.assertEqual(normalize_text("حَلِيب"), "حليب")

    def test_word_boundaries(self) -> None:
        self.assertEqual(find_allergens("milky flavor"), [])


if __name__ == "__main__":
    unittest.main()
