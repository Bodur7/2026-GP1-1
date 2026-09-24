# Misbar - 2026 Graduation Project

## Introduction

Misbar is a bilingual food-safety project that uses artificial intelligence to help users understand food items and make safer, more informed food choices.

The project currently contains two AI components:

1. **Dish Recognition:** identifies a dish from an uploaded or captured image.
2. **Packaged Food Recognition:** contains the curated allergen keyword dataset and its regulatory references for future analysis of OCR-extracted food-label text.

## Project goal

Misbar aims to provide clear food information by combining visual dish recognition with packaged-food allergen information. The system is intended to support user awareness; it does not replace product labels, manufacturer guidance, or professional medical advice.

## Repository structure

```text
2026-GP1-1/
├── Dish-Recognition/                  # Dish-classification model and evidence
├── Packaged-Food-Recognition/         # Allergen keyword dataset and references
├── Sprint-1/                          # Sprint 1 planning and deliverables
├── .vscode/                           # Shared VS Code settings and tasks
├── .gitattributes
├── .gitignore
├── AUTHORS
└── README.md
```

### Dish Recognition

`Dish-Recognition/` preserves the verified DINOv2 ViT-B/14 baseline for 121 food classes. It includes training, evaluation, inference, reports, configuration, and audit files.

See `Dish-Recognition/README.md` for component details.

### Packaged Food Recognition

`Packaged-Food-Recognition/` currently contains:

- `Datasets/comprehensive_allergens_dataset.csv`
- `references/Food_Allergens_Control.pdf`
- `references/SOURCES.md`

No OCR or matching implementation has been committed yet.

See `Packaged-Food-Recognition/README.md` for component details.

## Technologies used

Technologies currently confirmed in the repository:

- Python 3.10 or later
- PyTorch
- Torchvision
- Pillow
- DINOv2 ViT-B/14
- Git and GitHub
- Visual Studio Code

Additional application, OCR, backend, and mobile technologies should be added after the team confirms the final implementation.

## Launch instructions

### 1. Clone the repository

```bash
git clone https://github.com/Bodur7/2026-GP1-1.git
cd 2026-GP1-1
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dish-recognition dependencies

```bash
pip install -r Dish-Recognition/requirements.txt
```

### 4. Add and verify the dish-recognition checkpoint

Place the verified checkpoint at:

```text
Dish-Recognition/models/best_checkpoint.pt
```

Then run:

```bash
python Dish-Recognition/scripts/infer_final_food_v2_dinov2.py --checkpoint Dish-Recognition/models/best_checkpoint.pt --verify-only
```

The packaged-food component currently contains data and references only, so it does not yet have a launch command.

## Large-file and security policy

Do not commit datasets, model weights, API keys, access tokens, credentials, or private data. Large assets must be shared through the team's approved private storage location.
