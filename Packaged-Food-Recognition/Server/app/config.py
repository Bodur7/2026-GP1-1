import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Open Food Facts Model configuration
MODEL_ID = os.getenv("OFF_MODEL_ID", "openfoodfacts/ingredient-detection")

# Check if local folder with model exists
LOCAL_MODEL_DIR = BASE_DIR / "ingredient-detection"
if LOCAL_MODEL_DIR.exists() and (LOCAL_MODEL_DIR / "config.json").exists():
    MODEL_PATH = str(LOCAL_MODEL_DIR)
else:
    MODEL_PATH = MODEL_ID

# Dataset path resolution
# Automatically prefers your original Colab dataset if you drop it in this folder!
DATASET_CANDIDATES = [
    os.getenv("ALLERGEN_DATASET_PATH", ""),
    str(BASE_DIR / "allergen_matching_dataset_reviewed_rtl.csv"),
    str(BASE_DIR / "comprehensive_allergens_dataset (1).csv"),
    str(BASE_DIR / "comprehensive_allergens_dataset.csv"),
    str(BASE_DIR / "allergens_dataset.csv"),
]

ALLERGEN_DATASET_FILE = None
for candidate in DATASET_CANDIDATES:
    if candidate and os.path.isfile(candidate):
        ALLERGEN_DATASET_FILE = candidate
        break

# Auto-detect Google Cloud Service Account JSON key
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    candidate_keys = [
        Path("/Users/joud/Downloads/allergen-scanner-506512-6b749d009330.json"),
        *BASE_DIR.glob("*.json")
    ]
    for json_file in candidate_keys:
        try:
            if json_file.exists():
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and (data.get("type") == "service_account" or "project_id" in data):
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(json_file)
                        break
        except Exception:
            continue

GOOGLE_CREDENTIALS_SET = bool(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and 
    os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
)

# Server binding
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Firebase Firestore Configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "misbar-ebea2")

