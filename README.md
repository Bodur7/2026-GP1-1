# Misbar — 2026 Graduation Project

Misbar is a bilingual food-safety system that uses artificial intelligence to help users understand food items and make safer, more informed food choices.

The AI part of the project is divided into two main components:

1. Dish recognition
2. Packaged-food recognition

## System components

### 1. Dish Recognition

The `Dish-Recognition/` component identifies a dish from an image captured with a mobile camera or uploaded by the user.

The component includes:

- A verified DINOv2 ViT-B/14 baseline.
- 121 supported food classes.
- Training, evaluation, and inference scripts.
- Dataset manifests and integrity reports.
- Model evaluation results.
- Data and model audit files.
- Local checkpoint verification.

For detailed setup and usage instructions, see:

```text
Dish-Recognition/README.md
```

### 2. Packaged Food Recognition

The `Packaged-Food-Recognition/` component processes images of packaged-food labels.

Its planned pipeline includes:

```text
Food-label image
        ↓
Text extraction using OCR
        ↓
Ingredient and allergen analysis
        ↓
Allergy-related result
```

This component will contain its own code, configuration, documentation, reports, model files, and dependencies.

For more information, see:

```text
Packaged-Food-Recognition/README.md
```

## Repository structure

```text
2026-GP1-1/
├── .vscode/                         # Shared VS Code settings and tasks
│
├── Dish-Recognition/                # Dish-classification component
│   ├── audits/                      # Data and model audits
│   ├── configs/                     # Training configuration
│   ├── data/                        # Local dataset location
│   ├── dataset_reports/             # Dataset manifests and integrity reports
│   ├── docs/                        # Component documentation
│   ├── models/                      # Local model checkpoints
│   ├── reports/                     # Evaluation results
│   ├── scripts/                     # Training, evaluation, and inference
│   ├── model_registry.json
│   ├── requirements.txt
│   └── README.md
│
├── Packaged-Food-Recognition/       # OCR and allergen-analysis component
│   └── README.md
│
├── .gitattributes                   # Cross-platform text-file settings
├── .gitignore                       # Files excluded from Git
└── README.md                        # Main project documentation
```

## Current status

| Component | Status |
| --- | --- |
| Dish Recognition | Verified 121-class baseline available |
| Packaged Food Recognition | Structure created; implementation will be added |

## Development environment

The project uses Python 3.10 or later.

Each component maintains its own `requirements.txt` file because the models may require different dependencies.

The shared `.vscode/` directory contains development settings and tasks used from the repository root.

## Data and model files

Datasets and trained model weights are not stored in Git because they are large and may contain controlled project assets.

The following file types must not be committed:

```text
.pt
.pth
.ckpt
.safetensors
```

Datasets and model checkpoints should be shared through the team's approved private storage location. Their versions and hashes should be documented in the relevant component.

## Security and privacy

Do not commit:

- API keys
- Access tokens
- Private credentials
- Personal data
- Local environment files
- Unapproved datasets
- Large model checkpoints

Use environment variables or local `.env` files for private configuration. These files are excluded through `.gitignore`.