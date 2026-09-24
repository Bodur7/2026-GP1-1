# Allergen keyword dataset

`comprehensive_allergens_dataset.csv` is the operational bilingual keyword dataset used by the matcher. It contains two columns:

- `Allergen_Category`: the user-facing allergen group.
- `Keyword`: an Arabic or English term that may appear in OCR-extracted label text.

`allergen_categories.csv` assigns a stable internal ID and bilingual display names to each dataset category. `source_mapping.csv` documents how each category relates to the SFDA, European Commission, and FDA sources.

Keyword matching is a screening step. New or ambiguous terms should be reviewed and covered by a regression test before they are added.
