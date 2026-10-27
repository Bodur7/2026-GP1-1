import os
import logging
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status
import firebase_admin
from firebase_admin import auth, credentials
from app.constants import FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS

logger = logging.getLogger("allergen_scanner.auth")

_firebase_initialized = False

def init_firebase_admin():
    """
    Initializes Firebase Admin SDK with service account credentials from credentials/,
    or falls back to application default credentials / project ID.
    """
    global _firebase_initialized
    if _firebase_initialized or firebase_admin._apps:
        _firebase_initialized = True
        return firebase_admin.get_app()

    if FIREBASE_CREDENTIALS.exists():
        try:
            cred = credentials.Certificate(str(FIREBASE_CREDENTIALS))
            app = firebase_admin.initialize_app(cred, {"projectId": FIREBASE_PROJECT_ID})
            _firebase_initialized = True
            logger.info(f"Firebase Admin SDK initialized using service account: {FIREBASE_CREDENTIALS}")
            return app
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin with certificate {FIREBASE_CREDENTIALS}: {e}")

    try:
        app = firebase_admin.initialize_app(options={"projectId": FIREBASE_PROJECT_ID})
        _firebase_initialized = True
        logger.info(f"Firebase Admin SDK initialized with default options for project '{FIREBASE_PROJECT_ID}'.")
        return app
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}")
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Reusable FastAPI dependency to authenticate requests using Firebase ID tokens.
    Extracts and verifies the Bearer token from the 'Authorization' header.
    Returns the decoded token containing 'uid', 'email', etc.
    Rejects missing, expired, or invalid tokens with HTTP 401 Unauthorized.
    """
    if not authorization or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Please include 'Authorization: Bearer <firebase_id_token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Format must be 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    init_firebase_admin()

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing a valid user ID (uid).",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return decoded_token

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"Token expired\""},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token has been revoked.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"Token revoked\""},
        )
    except auth.InvalidIdTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase ID token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying Firebase ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate Firebase credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
