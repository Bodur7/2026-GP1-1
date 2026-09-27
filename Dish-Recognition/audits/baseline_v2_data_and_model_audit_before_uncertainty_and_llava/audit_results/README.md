# Audit results

Generated reports belong here and never replace `reports/baseline_121/`.

- `STATIC_AUDIT_FINDINGS.md`: readable interim findings and actions from committed artifacts.
- `static_audit.json`: machine-readable checks, confidence intervals, error priorities, and next runs.
- `external_asset_verification.json`: sanitized checkpoint verification result; no machine-specific path is stored.
- `received_mena_archives_audit.json`: image integrity and final-manifest matching for the received partial MENA archives.
- `mena12_test_reproduction.json`: per-class, Top-k, confusion, and confidence results for the reproduced 523-image MENA-12 test subset.
- `mena_review_model_agreement.json`: diagnostic agreement with unverified labels in the 91-image cleaning-review collection.
- `received_split_archives_audit.json`: integrity, completeness, and manifest matching for separately downloaded train/validation/test ZIP files.
- `dataset_image_audit_train.json`: complete train split decode, SHA-256, dimension, EXIF, and resolution audit.
- `dataset_image_audit_val.json`: complete validation split decode, SHA-256, dimension, EXIF, and resolution audit.
- `dataset_image_audit_test.json`: complete test split decode, SHA-256, dimension, EXIF, and resolution audit.
- `near_duplicate_leakage_audit.json`: complete cross-split pHash candidate search through Hamming distance 4.
- `near_duplicate_visual_review.json`: visual decisions for all six automated near-duplicate candidates.
- `validation_prediction_summary.json`: complete validation Top-k, per-class, confusion, confidence, and per-error summary.
- `validation_uncertainty_target_097.json`, `098.json`, `0985.json`, `099.json`, and `0995.json`: validation-only temperature and acceptance-policy comparisons.
- `frozen_policy_test_results.json`: validated full-test export shape, validation-frozen policy results, de-leaked sensitivity metrics, MENA/Food-101 metrics, review-band Top-3/Top-5 evidence, and confusion pairs.

Image integrity, validation calibration, and frozen-policy test analysis are complete. Grouped OOD analysis remains pending. Large per-image prediction files remain outside Git.
