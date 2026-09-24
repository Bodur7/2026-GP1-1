# Packaged Food Recognition - Misbar

This component analyzes packaged-food labels in Arabic and English. It extracts label text with OCR, normalizes the text, and matches ingredient terms against a curated allergen lexicon.

## Pipeline

```text
Label image -> OCR -> text normalization -> allergen keyword matching -> reviewable result
```

The current matcher returns evidence-based candidate matches. It does not declare a product medically safe and must not replace the product label, manufacturer guidance, or professional medical advice.

## Structure

```text
Packaged-Food-Recognition/
├── Datasets/
│   ├── comprehensive_allergens_dataset.csv
│   ├── allergen_categories.csv
│   ├── source_mapping.csv
│   └── README.md
├── data/
│   └── README.md
├── models/
│   └── README.md
├── references/
│   ├── Food_Allergens_Control.pdf
│   ├── SOURCES.md
│   └── README.md
├── reports/
│   └── README.md
├── src/
│   ├── ocr.py
│   ├── text_preprocessing.py
│   ├── allergen_matcher.py
│   ├── pipeline.py
│   └── README.md
├── tests/
│   ├── test_allergen_matcher.py
│   └── README.md
├── requirements.txt
└── README.md
```

### Folder responsibilities

| Path | Purpose |
| --- | --- |
| `Datasets/` | Bilingual allergen keywords, canonical categories, and source mapping. |
| `data/` | Local-only product-label images and OCR datasets. |
| `models/` | Local-only OCR/model files. |
| `references/` | Regulatory source document and source register. |
| `src/` | OCR, normalization, matching, and pipeline code. |
| `tests/` | Automated tests for normalization and matching. |
| `reports/` | Evaluation reports for OCR and allergen matching. |

## Setup

Run from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Packaged-Food-Recognition/requirements.txt
```

Tesseract OCR must also be installed on the machine with Arabic and English language data (`ara` and `eng`).

## Example

```powershell
python Packaged-Food-Recognition/src/pipeline.py path\to\label.jpg
```

## Data policy

Do not commit product images, private datasets, credentials, or model weights. Commit the small curated lexicon and its source metadata so changes can be reviewed and reproduced.
