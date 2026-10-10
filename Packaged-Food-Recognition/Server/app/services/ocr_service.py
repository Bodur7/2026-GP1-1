import os
import logging
from typing import Tuple
from app.config import GOOGLE_CREDENTIALS_SET

logger = logging.getLogger(__name__)

# Cache instance for Google Vision client
_vision_client = None

def get_vision_client():
    global _vision_client
    if _vision_client is not None:
        return _vision_client

    if GOOGLE_CREDENTIALS_SET or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            from google.cloud import vision_v1 as vision
            _vision_client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision ImageAnnotatorClient initialized.")
            return _vision_client
        except Exception as e:
            logger.warning(f"Could not initialize Google Cloud Vision: {e}")
            return None
    return None

def perform_ocr(image_bytes: bytes) -> Tuple[str, str]:
    """
    Extracts text from image bytes using Google Cloud Vision.
    Returns: (extracted_text, engine_name)
    """
    client = get_vision_client()
    if client is None:
        raise RuntimeError(
            "Google Vision client could not be initialized. Please check GOOGLE_APPLICATION_CREDENTIALS."
        )

    last_error = None
    for attempt in range(2):
        try:
            from google.cloud import vision_v1 as vision
            image = vision.Image(content=image_bytes)
            response = client.document_text_detection(image=image)
            if response.error.message:
                error_msg = f"Google Vision API error: {response.error.message} (code: {response.error.code})"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            text = response.full_text_annotation.text
            if text:
                return text.strip(), "google_vision"
            else:
                return "", "google_vision"
        except Exception as e:
            last_error = e
            logger.error(f"Google Vision OCR attempt {attempt + 1} failed: {e}", exc_info=True)
            if attempt == 0:
                import time
                time.sleep(0.5)

    raise RuntimeError(f"Google Vision OCR failed: {last_error}") from last_error

