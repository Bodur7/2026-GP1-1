from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Credentials paths
CREDENTIALS_DIR = BASE_DIR / "credentials"
GOOGLE_VISION_CREDENTIALS = CREDENTIALS_DIR / "allergen-scanner-506512-6b749d009330.json"
FIREBASE_CREDENTIALS = CREDENTIALS_DIR / "misbar-ebea2-firebase-adminsdk-fbsvc-fb5b41e239.json"
SIGHTENGINE_CREDENTIALS = CREDENTIALS_DIR / "sightengine.json"

# Dataset path
ALLERGEN_DATASET_FILE = BASE_DIR / "allergen_matching_dataset_reviewed_rtl.csv"

# Model path (uses local folder if downloaded, otherwise uses Hugging Face hub)
LOCAL_MODEL_DIR = BASE_DIR / "ingredient-detection"
if LOCAL_MODEL_DIR.exists() and (LOCAL_MODEL_DIR / "config.json").exists():
    MODEL_PATH = str(LOCAL_MODEL_DIR)
else:
    MODEL_PATH = "openfoodfacts/ingredient-detection"

# Firebase project
FIREBASE_PROJECT_ID = "misbar-ebea2"

# Server configuration
HOST = "0.0.0.0"
PORT = 8000
