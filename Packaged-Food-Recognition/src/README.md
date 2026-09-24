# Source code

This folder contains the executable pipeline. `ocr.py` extracts Arabic and English label text, `text_preprocessing.py` normalizes OCR output, `allergen_matcher.py` matches against `Datasets/comprehensive_allergens_dataset.csv`, and `pipeline.py` combines the steps into one reviewable JSON result.
