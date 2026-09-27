# Tiny Kunafa Image Findings

## Finding

The full integrity audit flagged five Arabic Food-101 Kunafa images with a side below 32 pixels. Visual review confirms that they are extremely thin image strips rather than useful small dish photographs.

| Split | File | Dimensions |
|---|---|---:|
| train | `train/Kunafa/الكنافة (16).png` | 286 × 16 |
| train | `train/Kunafa/الكنافة (17).png` | 240 × 18 |
| train | `train/Kunafa/الكنافة (18).png` | 294 × 14 |
| train | `train/Kunafa/الكنافة (20).png` | 300 × 12 |
| val | `val/Kunafa/الكنافة (19).png` | 290 × 15 |

The images decode and match the committed SHA-256 values, so this is not corruption introduced by transfer. It is a source-image quality defect preserved in the baseline dataset.

## Risk

The baseline preprocessing resizes inputs to a square 336-pixel model input. Resizing a 12–18-pixel-high strip to this geometry creates extreme distortion and provides little reliable Kunafa evidence. The validation image can also distort class-level validation confidence and uncertainty threshold selection.

## Decision

- Preserve the five files in `final_food_dataset_v2` so the historical baseline remains reproducible.
- Exclude the validation strip from threshold selection in a documented sensitivity run.
- Create a corrected dataset version that removes or replaces all five files; never edit the baseline in place.
- Re-evaluate Kunafa accuracy and confidence with and without these files before deciding whether fine-tuning is necessary.
