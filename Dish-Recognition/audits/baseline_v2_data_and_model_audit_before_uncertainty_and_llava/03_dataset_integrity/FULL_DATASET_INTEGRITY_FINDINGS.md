# Full Dataset Integrity Findings

## Scope

This audit read the complete external `final_food_dataset_v2` without modifying it. Every manifest row was checked for file presence, byte-level SHA-256 equality, successful image decoding, and recorded dimensions.

The verified dataset contains 121 classes and 105,681 images:

| Split | Images | Classes | Status |
|---|---:|---:|---|
| train | 76,198 | 121 | Complete |
| val | 3,630 | 121 | Complete |
| test | 25,853 | 121 | Complete |

## Integrity result

Across all three splits:

- Missing images: 0
- Unreadable images: 0
- Decode failures: 0
- SHA-256 mismatches: 0
- True dimension mismatches: 0

The actual dataset therefore matches the committed manifest at the path, content-hash, and decodability levels.

## Quality flags requiring follow-up

These flags do not invalidate the dataset, and no image was deleted or changed.

| Flag | train | val | test | Total |
|---|---:|---:|---:|---:|
| Side below 32 pixels | 4 | 1 | 0 | 5 |
| Width or height below 336 pixels | 5,677 | 496 | 1,487 | 7,660 |
| EXIF-oriented dimension match | 2 | 0 | 1 | 3 |
| Truncated EXIF metadata warning | 1 | 0 | 2 | 3 |

The five images with a side below 32 pixels are all Kunafa images:

- `train/Kunafa/الكنافة (16).png`
- `train/Kunafa/الكنافة (17).png`
- `train/Kunafa/الكنافة (18).png`
- `train/Kunafa/الكنافة (20).png`
- `val/Kunafa/الكنافة (19).png`

Images whose manifest dimensions match only after applying EXIF orientation:

- `train/clam_chowder/1504756.jpg` — orientation 6
- `train/sushi/5900.jpg` — orientation 6
- `test/macaroni_and_cheese/289764.jpg` — orientation 8

Images that decode successfully but produce a truncated EXIF metadata warning:

- `train/frozen_yogurt/1907489.jpg`
- `test/apple_pie/1854241.jpg`
- `test/ice_cream/1854234.jpg`

## Interpretation and action

The dataset is valid for reproducible baseline evaluation. The next work is not to rebuild it blindly. Instead:

1. Confirm whether the training and inference loaders apply EXIF orientation consistently.
2. Visually review the five tiny Kunafa images and quantify their influence on Kunafa predictions.
3. Measure accuracy and confidence separately for the 7,660 low-resolution images versus the remaining images.
4. Continue exact and near-duplicate leakage analysis before model evaluation.

The per-split machine-readable reports are stored in `audit_results/dataset_image_audit_train.json`, `dataset_image_audit_val.json`, and `dataset_image_audit_test.json`.
