import os
import json
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.constants import (
    MODEL_PATH,
    ALLERGEN_DATASET_FILE,
    HOST,
    PORT,
)
from app.models import (
    ScanResponse,
    ScanTextRequest,
    HealthResponse,
    AllergensListResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserAllergiesResponse,
    UserAllergiesUpdateRequest,
)
from app.auth import get_current_user, init_firebase_admin
from app.services.ocr_service import perform_ocr, get_vision_client
from app.services.ingredient_service import extract_ingredients, load_ingredient_pipeline
from app.services.allergen_service import (
    detect_allergens,
    get_available_categories,
    get_keywords_count,
    load_allergen_dataset
)
from app.services.user_allergen_service import (
    fetch_user_allergens_from_db,
    save_user_allergens_in_db,
    get_user_profile_from_db,
    save_user_profile_in_db,
    UserDocumentNotFoundError,
    DatabaseUnavailableError,
    InvalidAllergyDataError,
)
from app.services.quality_service import check_image_quality, QualityServiceError

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("allergen_scanner")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Allergen Scanner FastAPI Server...")
    # Initialize Firebase Admin SDK
    init_firebase_admin()

    # Pre-load allergen dataset on startup
    load_allergen_dataset()
    logger.info("Allergen dataset pre-loaded.")

    # Model loading can be deferred to first request or warmed up here
    try:
        logger.info("Warming up Open Food Facts ingredient detection model...")
        load_ingredient_pipeline()
    except Exception as e:
        logger.warning(f"Model warm-up deferred: {e}. Will attempt on first request.")

    yield
    logger.info("Shutting down Allergen Scanner Server...")

app = FastAPI(
    title="Open Food Facts Allergen Scanner API",
    description="Backend API for Flutter mobile app to extract ingredient lists, detect allergens, and manage user preferences with Firebase Auth & Firestore verification.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for Flutter web / mobile / emulators
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Info"])
def root():
    return {
        "message": "Open Food Facts Allergen Scanner API is running.",
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "scan_image": "POST /scan/image (requires Authorization: Bearer <token>)",
            "scan_text": "POST /scan/text (requires Authorization: Bearer <token>)",
            "list_allergens": "GET /allergens",
            "user_profile": "GET /users/me, POST /users/profile",
            "user_allergies": "GET /users/me/allergies, PUT /users/me/allergies"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    ocr_name = "none"
    if get_vision_client() is not None:
        ocr_name = "google_vision"

    model_ready = False
    try:
        from app.services.ingredient_service import _ingredient_pipeline
        model_ready = _ingredient_pipeline is not None
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        model_loaded=model_ready,
        model_path=MODEL_PATH,
        ocr_engine_available=ocr_name != "none",
        ocr_engine_name=ocr_name,
        allergen_keywords_count=get_keywords_count(),
        dataset_file=str(ALLERGEN_DATASET_FILE) if ALLERGEN_DATASET_FILE else None
    )

@app.get("/allergens", response_model=AllergensListResponse, tags=["Allergens"])
def list_allergens():
    """
    Returns all supported allergen categories and total keyword count.
    Used by the Flutter app to populate selection chips/checkboxes.
    """
    categories = get_available_categories()
    return AllergensListResponse(
        categories=categories,
        total_categories=len(categories),
        total_keywords=get_keywords_count()
    )

# ============================================================================
# User & Allergies Protected Database Endpoints
# ============================================================================

@app.get("/users/me", response_model=UserProfileResponse, tags=["Users"])
def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieves the current authenticated user's profile and saved allergies from Firestore.
    Verified Firebase UID is derived strictly from the Bearer token.
    """
    uid = current_user["uid"]
    profile = get_user_profile_from_db(user_id=uid) or {}
    return UserProfileResponse(
        uid=uid,
        email=profile.get("email") or current_user.get("email"),
        name=profile.get("name") or current_user.get("name"),
        allergies=profile.get("allergies", [])
    )

@app.post("/users/profile", response_model=UserProfileResponse, tags=["Users"])
def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Creates or updates the user profile record in Firestore for the authenticated user.
    Called when a user signs up or updates their profile in Flutter.
    """
    uid = current_user["uid"]
    name = request.name if request.name is not None else current_user.get("name")
    email = request.email if request.email is not None else current_user.get("email")

    save_user_profile_in_db(user_id=uid, name=name, email=email)
    profile = get_user_profile_from_db(uid) or {}
    return UserProfileResponse(
        uid=uid,
        email=profile.get("email") or email,
        name=profile.get("name") or name,
        allergies=profile.get("allergies", [])
    )

@app.get("/users/me/allergies", response_model=UserAllergiesResponse, tags=["Users"])
def get_my_allergies(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Fetches the saved allergen preferences for the authenticated user from Firestore.
    """
    uid = current_user["uid"]
    try:
        allergies = fetch_user_allergens_from_db(user_id=uid)
    except UserDocumentNotFoundError:
        allergies = []
    except DatabaseUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except InvalidAllergyDataError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return UserAllergiesResponse(allergies=allergies)

@app.put("/users/me/allergies", response_model=UserAllergiesResponse, tags=["Users"])
def update_my_allergies(
    request: UserAllergiesUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates the saved allergen preferences for the authenticated user in Firestore.
    Returns success response only after Firestore write completes successfully.
    """
    uid = current_user["uid"]
    try:
        save_user_allergens_in_db(user_id=uid, allergies=request.allergies)
    except DatabaseUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Error persisting allergies for user '{uid}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save allergies in database."
        )
    return UserAllergiesResponse(allergies=request.allergies)

# ============================================================================
# Scanning Protected Endpoints
# ============================================================================

@app.post("/scan/image", response_model=ScanResponse, tags=["Scanner"])
async def scan_image(
    file: UploadFile = File(..., description="Image file of the product label (JPEG, PNG, WEBP)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload an image of a food product packaging label.
    Requires a valid Firebase ID token in the 'Authorization: Bearer <token>' header.
    1. Derives authenticated user UID from verified token.
    2. Checks image quality before OCR or ingredient analysis.
    3. Runs OCR (Google Cloud Vision or EasyOCR).
    4. Uses Open Food Facts model to extract the ingredient list.
    5. Retrieves user allergies strictly from Firestore for verified UID.
    6. Cross-references against allergen dataset and returns structured results.
    """
    uid = current_user["uid"]
    logger.info(f"Authenticated scan request for user UID: '{uid}'")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file must be an image, received: {file.content_type}"
        )

    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

        # Do not run OCR when the image fails quality checking.
        try:
            quality = await asyncio.to_thread(check_image_quality, image_bytes)
        except QualityServiceError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from None

        if not quality["accepted"]:
            return ScanResponse(
                success=False,
                status="low_quality",
                error_title="Image Not Clear / الصورة غير واضحة",
                is_safe=False,
                extracted_ocr_text="",
                ingredient_list="",
                allergens_detected=[],
                total_allergens_count=0,
                ocr_engine="not_run",
                message=(
                    "Please retake the label photo in good lighting and keep the camera steady. / "
                    "يرجى إعادة تصوير الملصق بإضاءة جيدة مع تثبيت الكاميرا."
                ),
            )

        # 1. OCR Extraction
        ocr_text, ocr_engine = perform_ocr(image_bytes)
        if not ocr_text or not ocr_text.strip():
            return ScanResponse(
                success=False,
                status="no_text",
                error_title="No Text Detected / لم يتم العثور على نص",
                is_safe=False,
                extracted_ocr_text="",
                ingredient_list="",
                allergens_detected=[],
                total_allergens_count=0,
                ocr_engine=ocr_engine,
                message="The image does not contain readable text. Please ensure the product label is clear, well-lit, and in focus. / الصورة لا تحتوي على نص واضح. يرجى التأكد من وضوح الملصق وإضاءته الجيدة."
            )

        # 2. Extract Ingredient List with Open Food Facts model
        ingredient_list = extract_ingredients(ocr_text)
        if not ingredient_list or not ingredient_list.strip():
            return ScanResponse(
                success=False,
                status="no_ingredients",
                error_title="No Ingredients Found / لم يتم العثور على قائمة المكونات",
                is_safe=False,
                extracted_ocr_text=ocr_text,
                ingredient_list="",
                allergens_detected=[],
                total_allergens_count=0,
                ocr_engine=ocr_engine,
                message="Text was detected, but no food ingredients list was found. Please photograph the 'Ingredients' ('المكونات') section. / تم العثور على نص ولكن لم يتم التعرف على قائمة مكونات غذائية. يرجى تصوير قسم 'المكونات' على المنتج."
            )

        # 3. Retrieve User Allergens strictly from Firestore using verified UID
        try:
            effective_allergens = fetch_user_allergens_from_db(user_id=uid)
            logger.info(f"Retrieved {len(effective_allergens)} allergies from Firestore for UID '{uid}': {effective_allergens}")
        except UserDocumentNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile or allergy preferences not found. Please save your allergies before scanning."
            )
        except DatabaseUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database service unavailable. Cannot retrieve user allergies: {e}"
            )
        except InvalidAllergyDataError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid allergy data in database: {e}"
            )

        # 4. Detect Allergens (Comparison)
        detections, is_safe = detect_allergens(
            ingredient_text=ingredient_list,
            user_allergens=effective_allergens
        )

        return ScanResponse(
            success=True,
            status="completed",
            is_safe=is_safe,
            extracted_ocr_text=ocr_text,
            ingredient_list=ingredient_list,
            allergens_detected=detections,
            total_allergens_count=len(detections),
            ocr_engine=ocr_engine,
            message="Analysis completed successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing image scan:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/scan/text", response_model=ScanResponse, tags=["Scanner"])
def scan_text(
    request: ScanTextRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Directly analyze packaging text.
    Requires a valid Firebase ID token in the 'Authorization: Bearer <token>' header.
    1. Uses Open Food Facts model to isolate the ingredient list.
    2. Extracts user allergies directly from Firestore using verified UID.
    3. Cross-references against the allergen dataset.
    """
    uid = current_user["uid"]
    raw_text = request.text
    if not raw_text or not raw_text.strip():
        return ScanResponse(
            success=False,
            status="no_text",
            error_title="No Text Provided / لم يتم توفير أي نص",
            is_safe=False,
            extracted_ocr_text="",
            ingredient_list="",
            allergens_detected=[],
            total_allergens_count=0,
            ocr_engine="provided_text",
            message="No text was provided. Please provide text to analyze. / لم يتم توفير أي نص للتحليل."
        )

    try:
        # 1. Extract ingredients using Open Food Facts model
        ingredient_list = extract_ingredients(raw_text)
        if not ingredient_list or not ingredient_list.strip():
            return ScanResponse(
                success=False,
                status="no_ingredients",
                error_title="No Ingredients Found / لم يتم العثور على قائمة المكونات",
                is_safe=False,
                extracted_ocr_text=raw_text,
                ingredient_list="",
                allergens_detected=[],
                total_allergens_count=0,
                ocr_engine="provided_text",
                message="Text was provided, but no food ingredients list could be identified. / تم توفير النص ولكن لم يتم التعرف على قائمة مكونات غذائية."
            )

        # 2. Retrieve User Allergens strictly from Firestore using verified UID
        try:
            effective_allergens = fetch_user_allergens_from_db(user_id=uid)
            logger.info(f"Retrieved {len(effective_allergens)} allergies from Firestore for UID '{uid}': {effective_allergens}")
        except UserDocumentNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile or allergy preferences not found. Please save your allergies before scanning."
            )
        except DatabaseUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database service unavailable. Cannot retrieve user allergies: {e}"
            )
        except InvalidAllergyDataError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid allergy data in database: {e}"
            )

        # 3. Detect allergens (Comparison)
        detections, is_safe = detect_allergens(
            ingredient_text=ingredient_list,
            user_allergens=effective_allergens
        )

        return ScanResponse(
            success=True,
            status="completed",
            is_safe=is_safe,
            extracted_ocr_text=raw_text,
            ingredient_list=ingredient_list,
            allergens_detected=detections,
            total_allergens_count=len(detections),
            ocr_engine="provided_text",
            message="Analysis completed successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing text scan:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
