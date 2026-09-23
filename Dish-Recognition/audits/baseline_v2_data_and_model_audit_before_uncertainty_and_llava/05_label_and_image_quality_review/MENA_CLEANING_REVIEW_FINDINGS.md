# MENA Cleaning Review Findings

## Scope

The received review collection contains 91 decodable images across ten non-empty class folders. None of their SHA-256 values appears in the final dataset manifest. They were evaluated as review evidence only and were not added to any dataset.

## Model agreement diagnostic

Agreement with the unverified source-folder label was 85.71% Top-1 and 97.80% Top-5. These values are not accuracy because the folder labels are not accepted ground truth.

Lowest source-label agreement:

- `shakshouka-egypt`: 3/6 (50%)
- `aseeda`: 9/15 (60%)
- `saleeg`: 5/6 (83.33%)

## Visual findings

The disagreement review exposes clear or likely label-quality failures:

- `shakshouka-egypt` contains sandwich-like and fried-food images with no visible shakshouka.
- A `saleeg` candidate shows grilled chicken pieces without the defining rice presentation.
- A `masoub` candidate resembles a white soup or dessert in a cup.
- Multiple `aseeda` candidates have banana, cereal, or bread-like presentations that strongly resemble `masoub`.
- An `areeka` candidate also strongly resembles `masoub`.

Several disagreements are high-confidence, which means a confidence threshold alone cannot repair incorrect or ambiguous source labels.

## Decision

- Keep all 91 images outside `final_food_dataset_v2`.
- Do not auto-merge them into a future training set.
- Reuse an image only after independent human relabeling with a documented visual class policy.
- Preserve these images as a label-quality challenge set, not as OOD ground truth.

This evidence supports the previous cleaning decision and shows that restoring rejected images would likely reduce class separation.
