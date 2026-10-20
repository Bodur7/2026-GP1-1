import os
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import (
    MODEL_PATH,
    ALLERGEN_DATASET_FILE,
    HOST,
    PORT,
    GOOGLE_CREDENTIALS_SET,
    FIREBASE_PROJECT_ID
)
from app.models import (
    ScanResponse,
    ScanTextRequest,
    HealthResponse,
    AllergensListResponse
)
from app.services.ocr_service import perform_ocr, get_vision_client
from app.services.ingredient_service import extract_ingredients, load_ingredient_pipeline
from app.services.allergen_service import (
    detect_allergens,
    get_available_categories,
    get_keywords_count,
    load_allergen_dataset
)
from app.services.user_allergen_service import fetch_user_allergens_from_db

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("allergen_scanner")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Allergen Scanner FastAPI Server...")
    # Pre-load allergen dataset on startup
    load_allergen_dataset()
    logger.info("Allergen dataset pre-loaded.")

    # Note: Model loading can be deferred to first request or warmed up here
    try:
        logger.info("Warming up Open Food Facts ingredient detection model...")
        load_ingredient_pipeline()
    except Exception as e:
        logger.warning(f"Model warm-up deferred: {e}. Will attempt on first request.")

    yield
    logger.info("Shutting down Allergen Scanner Server...")

app = FastAPI(
    title="Open Food Facts Allergen Scanner API",
    description="Backend API for Flutter mobile app to extract ingredient lists and detect allergens using Open Food Facts AI.",
    version="1.0.0",
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
            "scan_image": "POST /scan/image (multipart/form-data with 'file')",
            "scan_text": "POST /scan/text (JSON with 'text')",
            "list_allergens": "GET /allergens"
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
        dataset_file=ALLERGEN_DATASET_FILE
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

@app.post("/scan/image", response_model=ScanResponse, tags=["Scanner"])
async def scan_image(
    file: UploadFile = File(..., description="Image file of the product label (JPEG, PNG, WEBP)"),
    user_id: Optional[str] = Form(
        None,
        description="Firebase User UID to extract allergens directly from database before comparing"
    ),
    auth_token: Optional[str] = Form(
        None,
        description="Optional Firebase ID token for database authorization"
    ),
    user_allergens: Optional[str] = Form(
        None,
        description="Optional fallback comma-separated list or JSON array of allergen categories"
    ),
    authorization: Optional[str] = Header(None)
):
    """
    Upload an image of a food product packaging label.
    1. Runs OCR (Google Cloud Vision or EasyOCR).
    2. Uses Open Food Facts sequence tagging model to extract the ingredient list.
    3. Extracts user allergens directly from the database (Firestore) just before comparing.
    4. Cross-references against the allergen dataset and returns structured results.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file must be an image, received: {file.content_type}"
        )

    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

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

        # 3. Extract User Allergens from Database JUST BEFORE COMPARING
        effective_allergens: Optional[List[str]] = None
        effective_token = auth_token or (authorization.replace("Bearer ", "").strip() if authorization else None)

        if user_id and user_id.strip():
            logger.info(f"Extracting allergens from database for user UID: '{user_id.strip()}' just before comparing...")
            db_allergens = fetch_user_allergens_from_db(
                user_id=user_id.strip(),
                auth_token=effective_token
            )
            if db_allergens:
                effective_allergens = db_allergens
                logger.info(f"Successfully extracted {len(effective_allergens)} allergens from database: {effective_allergens}")
            else:
                logger.info(f"No allergens found in database for user '{user_id}'. Checking fallback.")

        # If user_id wasn't passed or DB returned empty, fallback to client-supplied allergens if available
        if not effective_allergens and user_allergens:
            try:
                parsed = json.loads(user_allergens)
                if isinstance(parsed, list):
                    effective_allergens = [str(x) for x in parsed]
            except Exception:
                effective_allergens = [x.strip() for x in user_allergens.split(",") if x.strip()]

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

    except Exception as e:
        logger.exception("Error processing image scan:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/scan/text", response_model=ScanResponse, tags=["Scanner"])
def scan_text(request: ScanTextRequest):
    """
    Directly analyze packaging text (e.g. from on-device Flutter Google ML Kit OCR).
    1. Uses Open Food Facts model to isolate the ingredient list.
    2. Cross-references against the allergen dataset.
    """
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

        # 2. Extract User Allergens from Database JUST BEFORE COMPARING
        effective_allergens = None
        if request.user_id and request.user_id.strip():
            logger.info(f"Extracting allergens from database for user UID: '{request.user_id.strip()}' just before comparing...")
            db_allergens = fetch_user_allergens_from_db(
                user_id=request.user_id.strip(),
                auth_token=request.auth_token
            )
            if db_allergens:
                effective_allergens = db_allergens
                logger.info(f"Successfully extracted {len(effective_allergens)} allergens from database: {effective_allergens}")

        if not effective_allergens:
            effective_allergens = request.user_allergens

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


    except Exception as e:
        logger.exception("Error processing text scan:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
