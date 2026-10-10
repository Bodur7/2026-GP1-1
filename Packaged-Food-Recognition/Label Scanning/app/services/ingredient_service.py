import logging
from typing import Optional
from app.config import MODEL_PATH

logger = logging.getLogger(__name__)

_ingredient_pipeline = None

def get_device():
    try:
        import torch
        if torch.cuda.is_available():
            return 0
        # For Mac Apple Silicon MPS acceleration: transformers pipeline supports device="mps" or torch.device("mps")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return -1

def load_ingredient_pipeline():
    global _ingredient_pipeline
    if _ingredient_pipeline is not None:
        return _ingredient_pipeline

    logger.info(f"Loading Open Food Facts ingredient detection model from: {MODEL_PATH}")
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
        
        device = get_device()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)

        _ingredient_pipeline = pipeline(
            "token-classification",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="first",
            stride=64,
            device=device
        )
        logger.info("Open Food Facts ingredient extraction model loaded successfully.")
        return _ingredient_pipeline
    except Exception as e:
        logger.error(f"Failed to load Open Food Facts model from {MODEL_PATH}: {e}")
        raise

def extract_ingredients(raw_ocr_text: str) -> str:
    """
    Isolates the ingredient list section from packaging text using the
    Open Food Facts sequence tagging AI model.
    """
    if not raw_ocr_text or not raw_ocr_text.strip():
        return ""

    pipe = load_ingredient_pipeline()
    try:
        entities = pipe(raw_ocr_text)
    except Exception as e:
        logger.warning(f"Ingredient extraction failed: {e}")
        return ""


    spans = []
    for ent in entities:
        group = ent.get("entity_group", ent.get("entity", ""))
        if "ING" in group:
            s = ent.get("start")
            e = ent.get("end")
            if s is not None and e is not None:
                spans.append((s, e))

    if spans:
        # Merge overlapping or adjacent spans (within 5 characters like punctuation/whitespace)
        merged = []
        for s, e in sorted(spans, key=lambda x: x[0]):
            if not merged:
                merged.append([s, e])
            else:
                prev_s, prev_e = merged[-1]
                if s <= prev_e + 5:
                    merged[-1][1] = max(prev_e, e)
                else:
                    merged.append([s, e])

        extracted_sections = [raw_ocr_text[s:e].strip() for s, e in merged]
        return "\n".join(extracted_sections)

    logger.info("No specific ingredient list span detected.")
    return ""

