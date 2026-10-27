import re
import csv
import logging
from typing import List, Tuple, Optional, Dict
from app.constants import ALLERGEN_DATASET_FILE
from app.models import AllergenDetection

logger = logging.getLogger(__name__)

_allergen_rules: List[Tuple[str, str, re.Pattern]] = []
_all_categories: List[str] = []
_dataset_loaded = False

def load_allergen_dataset():
    global _allergen_rules, _all_categories, _dataset_loaded
    if _dataset_loaded:
        return

    if not ALLERGEN_DATASET_FILE:
        logger.error("No allergen dataset file found! Allergen detection will return empty.")
        return

    logger.info(f"Loading allergen dataset from: {ALLERGEN_DATASET_FILE}")
    try:
        categories_set = set()
        rules = []

        with open(ALLERGEN_DATASET_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            # Determine column positions
            cat_idx = 0
            kw_idx = 1
            if header:
                for idx, col_name in enumerate(header):
                    col_lower = col_name.lower().strip()
                    if "category" in col_lower:
                        cat_idx = idx
                    elif "keyword" in col_lower or "ingredient" in col_lower:
                        kw_idx = idx

            for row in reader:
                if len(row) <= max(cat_idx, kw_idx):
                    continue
                category = row[cat_idx].strip()
                keyword = row[kw_idx].strip().lower()

                if not keyword or not category:
                    continue

                categories_set.add(category)
                # Word-boundary regex matching
                pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
                rules.append((category, keyword, pattern))

        _allergen_rules = rules
        _all_categories = sorted(list(categories_set))
        _dataset_loaded = True
        logger.info(f"Loaded {len(_allergen_rules)} allergen keywords across {len(_all_categories)} categories.")
    except Exception as e:
        logger.error(f"Failed to load allergen dataset: {e}")
        raise

def get_available_categories() -> List[str]:
    load_allergen_dataset()
    return _all_categories

def get_keywords_count() -> int:
    load_allergen_dataset()
    return len(_allergen_rules)

# Mapping of common user terms / synonyms to the dataset's official categories
ALLERGEN_ALIASES: Dict[str, List[str]] = {
    "dairy": ["milk"],
    "milk": ["milk"],
    "wheat": ["cereals containing gluten"],
    "gluten": ["cereals containing gluten"],
    "cereals containing gluten": ["cereals containing gluten"],
    "soy": ["soybean"],
    "soya": ["soybean"],
    "soybean": ["soybean"],
    "peanut": ["peanut"],
    "peanuts": ["peanut"],
    "tree nut": ["tree nuts"],
    "tree nuts": ["tree nuts"],
    "nuts": ["tree nuts", "peanut"],
    "egg": ["egg"],
    "eggs": ["egg"],
    "fish": ["fish"],
    "crustaceans": ["crustaceans"],
    "molluscs": ["molluscs"],
    "shellfish": ["crustaceans", "molluscs"],
    "sesame": ["sesame"],
    "mustard": ["mustard"],
    "celery": ["celery"],
    "lupin": ["lupin"],
    "sulphites": ["sulphur dioxide and sulphites"],
    "sulfites": ["sulphur dioxide and sulphites"],
}

def detect_allergens(
    ingredient_text: str,
    user_allergens: Optional[List[str]] = None
) -> Tuple[List[AllergenDetection], bool]:
    """
    Cross-references ingredient text against the allergen dataset.
    Returns: (list_of_detections, is_safe)
    """
    load_allergen_dataset()
    if not ingredient_text or not _allergen_rules:
        return [], True

    # Normalize text for matching
    normalized_text = re.sub(r"\s+", " ", ingredient_text.lower())

    # Map: category -> set of matched keywords
    matched_by_cat: Dict[str, List[str]] = {}

    for category, keyword, pattern in _allergen_rules:
        if pattern.search(normalized_text):
            if category not in matched_by_cat:
                matched_by_cat[category] = []
            if keyword not in matched_by_cat[category]:
                matched_by_cat[category].append(keyword)

    # Normalize user allergies list and expand synonyms/aliases
    target_categories = set()
    if user_allergens:
        for raw_item in user_allergens:
            if not raw_item:
                continue
            item = raw_item.lower().replace("allergy", "").replace("حساسية", "").strip()
            if item in ALLERGEN_ALIASES:
                for mapped in ALLERGEN_ALIASES[item]:
                    target_categories.add(mapped.lower())
            else:
                target_categories.add(item)

    detections: List[AllergenDetection] = []
    has_user_allergy_conflict = False

    for category, keywords in matched_by_cat.items():
        cat_lower = category.lower()
        is_user_allergen = False

        if target_categories:
            if any(tc == cat_lower or tc in cat_lower or cat_lower in tc for tc in target_categories):
                is_user_allergen = True
                has_user_allergy_conflict = True

        detections.append(
            AllergenDetection(
                allergen=category,
                matched_ingredients=keywords,
                is_user_allergen=is_user_allergen
            )
        )

    # If user provided personal allergies, is_safe is False only if a personal allergy matches.
    # Otherwise, is_safe is False if any allergen was found.
    if user_allergens is not None:
        is_safe = not has_user_allergy_conflict
    else:
        is_safe = len(detections) == 0

    return detections, is_safe
