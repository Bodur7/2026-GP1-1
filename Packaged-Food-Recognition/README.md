# Packaged Food Recognition - Misbar

This folder currently contains the allergen keyword dataset and the regulatory references supplied for the packaged-food component. OCR implementation, model code, tests, and evaluation files have not been added yet.

## Current structure

```text
Packaged-Food-Recognition/
├── Datasets/
│   └── comprehensive_allergens_dataset.csv
├── references/
│   ├── Food_Allergens_Control.pdf
│   └── SOURCES.md
└── README.md
```

## Allergen keyword dataset

The allergen dataset was developed as a curated keyword dataset based primarily on allergen-labeling requirements published by the Saudi Food and Drug Authority (SFDA), supplemented by the European Commission's list of 14 food allergens and the U.S. Food and Drug Administration's major food allergen guidance.

Each allergen category was expanded with common ingredient names, food-derived ingredients, and Arabic terminology to improve keyword-based matching of OCR-extracted ingredient labels.

The supplied dataset is stored at:

```text
Datasets/comprehensive_allergens_dataset.csv
```

It contains the following columns:

- `Allergen_Category`
- `Keyword`

## References

The supplied SFDA document is stored in `references/Food_Allergens_Control.pdf`. The SFDA, European Commission, and FDA citations and links are listed in `references/SOURCES.md`.

## Current scope

This folder currently documents the provided dataset and its sources only. The OCR method, matching implementation, model selection, tests, and evaluation structure should be added after the team approves the technical approach.
