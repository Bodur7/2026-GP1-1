import os
import json
import logging
import urllib.request
import urllib.error
from typing import List, Optional

from app.config import FIREBASE_PROJECT_ID

logger = logging.getLogger("allergen_scanner.db")

# Cache or initialize firebase_admin if credentials exist
_firestore_db = None
_firebase_initialized = False

def _init_firebase_admin():
    global _firestore_db, _firebase_initialized
    if _firebase_initialized:
        return _firestore_db

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        # Check if an app is already initialized
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_FILE") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path and os.path.isfile(cred_path):
                # Verify if it has project_id matching FIREBASE_PROJECT_ID or has firebase scope
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
            else:
                firebase_admin.initialize_app(options={"projectId": FIREBASE_PROJECT_ID})

        _firestore_db = firestore.client()
        _firebase_initialized = True
        logger.info("Firebase Admin Firestore client initialized successfully.")
        return _firestore_db
    except Exception as e:
        logger.debug(f"Firebase Admin SDK not initialized: {e}. Will use Firestore REST API.")
        _firebase_initialized = True
        return None


def fetch_user_allergens_from_db(
    user_id: str,
    auth_token: Optional[str] = None,
    project_id: Optional[str] = None
) -> List[str]:
    """
    Extracts the user's saved allergen list directly from the Cloud Firestore database
    under document collection 'users/{user_id}'.

    Supports:
    1. Firebase Admin SDK if configured on the server.
    2. Firestore REST API using the user's Firebase Auth ID token.
    """
    if not user_id or not user_id.strip():
        logger.warning("fetch_user_allergens_from_db called with empty user_id.")
        return []

    pid = project_id or FIREBASE_PROJECT_ID

    # 1. Try Firebase Admin SDK if available
    db = _init_firebase_admin()
    if db is not None:
        try:
            doc_ref = db.collection("users").document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict() or {}
                raw_allergies = data.get("allergies", [])
                if isinstance(raw_allergies, list):
                    allergens = [str(x) for x in raw_allergies if x]
                    logger.info(
                        f"[Firebase Admin] Successfully extracted {len(allergens)} allergens from DB for user '{user_id}': {allergens}"
                    )
                    return allergens
            else:
                logger.info(f"[Firebase Admin] User doc 'users/{user_id}' does not exist in DB.")
                return []
        except Exception as e:
            logger.warning(f"[Firebase Admin] Query failed for user '{user_id}': {e}. Falling back to REST API.")

    # 2. Query Cloud Firestore REST API
    url = f"https://firestore.googleapis.com/v1/projects/{pid}/databases/(default)/documents/users/{user_id}"
    headers = {
        "Accept": "application/json",
    }
    if auth_token and auth_token.strip():
        token = auth_token.strip()
        if not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
        headers["Authorization"] = token

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                doc_data = json.loads(body)
                fields = doc_data.get("fields", {})

                # Parse Firestore REST format for array 'allergies'
                allergies_field = fields.get("allergies", {})
                array_values = allergies_field.get("arrayValue", {}).get("values", [])
                allergens = []
                for val in array_values:
                    if "stringValue" in val:
                        allergens.append(val["stringValue"])

                logger.info(
                    f"[Firestore REST] Successfully extracted {len(allergens)} allergens from DB for user '{user_id}': {allergens}"
                )
                return allergens
            else:
                logger.warning(
                    f"[Firestore REST] Unexpected response {response.status} for user '{user_id}'"
                )
    except urllib.error.HTTPError as e:
        logger.warning(
            f"[Firestore REST] HTTP Error {e.code} while fetching allergens for user '{user_id}': {e.reason}"
        )
    except Exception as e:
        logger.warning(
            f"[Firestore REST] Error extracting allergens for user '{user_id}': {e}"
        )

    return []
