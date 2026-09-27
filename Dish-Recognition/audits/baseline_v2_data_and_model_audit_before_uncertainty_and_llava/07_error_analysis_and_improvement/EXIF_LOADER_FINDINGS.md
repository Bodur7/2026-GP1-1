# EXIF Orientation Loader Findings

## Finding

Three verified dataset images store their intended display orientation in EXIF metadata. Their manifest dimensions match the EXIF-corrected orientation rather than the raw pixel matrix.

Code inspection shows that the protected training, evaluation, and inference paths open images and call `convert("RGB")` without applying `PIL.ImageOps.exif_transpose`:

- `scripts/train_final_food_v2_dinov2_transfer.py` — `FolderDataset.__getitem__`
- `scripts/evaluate_final_food_v2_dinov2.py` — `MappedFolder.__getitem__`
- `scripts/infer_final_food_v2_dinov2.py` — single-image inference
- the audit prediction exporter uses torchvision `ImageFolder`, whose default PIL loader also does not explicitly transpose EXIF orientation

The historical baseline therefore sees the raw orientation for these files:

- `train/clam_chowder/1504756.jpg` — EXIF orientation 6
- `train/sushi/5900.jpg` — EXIF orientation 6
- `test/macaroni_and_cheese/289764.jpg` — EXIF orientation 8

## Impact

Only three baseline dataset images are affected, so this cannot explain aggregate model performance. The deployment risk is broader because phone-camera uploads commonly rely on EXIF orientation. A user image can otherwise reach the classifier rotated relative to its intended display.

## Decision

- Do not modify the protected baseline scripts or historical metric.
- The new audited inference/uncertainty pipeline must apply `ImageOps.exif_transpose(image).convert("RGB")` before resize/crop.
- A controlled evaluation must report predictions for the three affected images with legacy and corrected orientation.
- Future training/evaluation experiments must use one shared image loader and record EXIF handling in the experiment config.
