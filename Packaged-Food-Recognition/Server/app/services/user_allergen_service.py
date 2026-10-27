import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import urllib.request
import urllib.error

from app.constants import FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS
from app.auth import init_firebase_admin

logger = logging.getLogger("allergen_scanner.db")

class UserDocumentNotFoundError(Exception):
    """Raised when the user's Firestore document does not exist."""
    pass

class DatabaseUnavailableError(Exception):
    """Raised when Firestore is unavailable or connection fails."""
    pass

class InvalidAllergyDataError(Exception):
    """Raised when the 'allergies' field is missing or not a list."""
    pass

_firestore_client = None

def get_firestore_client():
    """
    Returns the Firestore client from firebase_admin, initializing if needed.
    """
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    app = init_firebase_admin()
    if app is not None:
        try:
            from firebase_admin import firestore
            _firestore_client = firestore.client()
            logger.info("Firestore client initialized successfully.")
            return _firestore_client
        except Exception as e:
            logger.error(f"Failed to get Firestore client from Firebase Admin: {e}")

    return None

def fetch_user_allergens_from_db(user_id: str) -> List[str]:
    """
    Extracts the user's saved allergen list directly from Cloud Firestore
    under document collection 'users/{user_id}'.
    Raises explicit exceptions on failure so callers never confuse failures with empty lists.
    """
    if not user_id or not user_id.strip():
        raise ValueError("fetch_user_allergens_from_db called with empty user_id.")

    db = get_firestore_client()
    if db is None:
        raise DatabaseUnavailableError("Firestore client is not available on server.")

    try:
        doc_ref = db.collection("users").document(user_id.strip())
        doc = doc_ref.get()
    except Exception as e:
        logger.error(f"Firestore query failed for user '{user_id}': {e}")
        raise DatabaseUnavailableError(f"Firestore query failed: {e}") from e

    if not doc.exists:
        logger.warning(f"User doc 'users/{user_id}' does not exist in DB.")
        raise UserDocumentNotFoundError(f"User profile document 'users/{user_id}' not found.")

    data = doc.to_dict() or {}
    if "allergies" not in data:
        raise InvalidAllergyDataError(f"User profile 'users/{user_id}' has no 'allergies' field.")

    raw_allergies = data.get("allergies")
    if not isinstance(raw_allergies, list):
        raise InvalidAllergyDataError(f"'allergies' field in 'users/{user_id}' is not a list: {type(raw_allergies)}")

    return [str(x) for x in raw_allergies if str(x).strip()]

def save_user_allergens_in_db(user_id: str, allergies: List[str]) -> bool:
    """
    Saves or updates the user's selected allergies in Firestore.
    """
    if not user_id or not user_id.strip():
        raise ValueError("save_user_allergens_in_db called with empty user_id.")

    db = get_firestore_client()
    if db is None:
        raise DatabaseUnavailableError("Firestore client is not available on server.")

    try:
        from firebase_admin import firestore
        doc_ref = db.collection("users").document(user_id.strip())
        doc_ref.set({
            "allergies": allergies,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }, merge=True)
        logger.info(f"Saved {len(allergies)} allergies for user '{user_id}'.")
        return True
    except Exception as e:
        logger.error(f"Failed to save allergies in Firestore for user '{user_id}': {e}")
        raise DatabaseUnavailableError(f"Failed to save allergies in Firestore: {e}") from e

def get_user_profile_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the user profile data (name, email, allergies) for the given user_id.
    """
    if not user_id or not user_id.strip():
        return None

    db = get_firestore_client()
    if db is not None:
        try:
            doc_ref = db.collection("users").document(user_id.strip())
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict() or {}
                return {
                    "uid": user_id.strip(),
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "allergies": [str(x) for x in data.get("allergies", []) if x]
                }
            return {
                "uid": user_id.strip(),
                "name": None,
                "email": None,
                "allergies": []
            }
        except Exception as e:
            logger.error(f"Error fetching user profile for '{user_id}': {e}")
            raise e

    raise RuntimeError("Firestore client is not available on server.")

def save_user_profile_in_db(user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> bool:
    """
    Creates or updates the user's profile document in Firestore.
    """
    if not user_id or not user_id.strip():
        return False

    db = get_firestore_client()
    if db is not None:
        try:
            from firebase_admin import firestore
            doc_ref = db.collection("users").document(user_id.strip())
            payload: Dict[str, Any] = {
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
            if name is not None:
                payload["name"] = name.strip()
            if email is not None:
                payload["email"] = email.strip()

            # If document doesn't exist yet, also set createdAt and empty allergies
            doc = doc_ref.get()
            if not doc.exists:
                payload["createdAt"] = firestore.SERVER_TIMESTAMP
                payload["allergies"] = []

            doc_ref.set(payload, merge=True)
            logger.info(f"Updated profile for user '{user_id}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to update profile for user '{user_id}': {e}")
            raise e

    raise RuntimeError("Firestore client is not available on server.")
