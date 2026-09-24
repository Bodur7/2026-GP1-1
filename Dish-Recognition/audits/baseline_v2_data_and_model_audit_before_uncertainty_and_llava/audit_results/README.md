# Audit results

Generated reports belong here and never replace `reports/baseline_121/`.

- `STATIC_AUDIT_FINDINGS.md`: readable interim findings and actions from committed artifacts.
- `static_audit.json`: machine-readable checks, confidence intervals, error priorities, and next runs.
- `external_asset_verification.json`: sanitized checkpoint verification result; no machine-specific path is stored.
- `received_mena_archives_audit.json`: image integrity and final-manifest matching for the received partial MENA archives.
- `mena12_test_reproduction.json`: per-class, Top-k, confusion, and confidence results for the reproduced 523-image MENA-12 test subset.
- `mena_review_model_agreement.json`: diagnostic agreement with unverified labels in the 91-image cleaning-review collection.
- `received_split_archives_audit.json`: integrity, completeness, and manifest matching for separately downloaded train/validation/test ZIP files.

Image integrity, prediction, calibration, and OOD reports will be generated after the complete external datasets are available. Large per-image prediction files remain outside Git.
