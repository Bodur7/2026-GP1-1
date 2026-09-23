# Received Assets — 2026-09-23

## `final_food_dataset_v2 (1).zip`

- Received size: 508,718,801 bytes.
- ZIP integrity check failed because the End of Central Directory record is missing.
- The file is incomplete or corrupted and is not used for dataset verification, evaluation, or training.
- A complete replacement archive or extracted directory is required.

## `MENA_selected_cleaned (1).zip`

- The archive opens successfully.
- It contains 1,339 JPG images and 1,621 text download-error placeholders.
- Recorded failures include rate-limit and web download exceptions.
- The collection is incomplete and must not replace the baseline dataset.
- Available images are audited against the final manifest as supporting evidence only.

## `MENA_cleaning_review (1).zip`

- The archive opens successfully.
- It contains 91 review images from 10 classes.
- These are review candidates, not automatically approved training images.

## `dataset_v2_reports.zip`

- The archive opens successfully and contains five reports.
- `build_summary_v2.json` is byte-identical to the repository copy.
- The manifest, leakage report, and dataset summary are equal to the repository versions when parsed row by row; their byte hashes differ only at file-representation level.
- `image_fingerprints_v2.csv` contains 105,681 rows and matches the manifest on class, split, SHA-256, pHash, width, and height.
- Existing repository reports remain authoritative and are not replaced.
