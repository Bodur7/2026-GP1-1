# File and directory index

| Path | Purpose |
| --- | --- |
| `README.md` | Overall objective and baseline protection rules. |
| `00_scope_and_rules/` | Audit scope, allowed actions, and prohibited actions. |
| `01_input_inventory/` | Inventory of datasets, checkpoints, code, and hashes. |
| `02_checkpoint_verification/` | Checkpoint SHA-256, architecture, classes, and preprocessing verification. |
| `03_dataset_integrity/` | Image decoding, counts, dimensions, and manifest reconciliation. |
| `04_duplicates_and_leakage/` | Exact duplicates, near-duplicates, and split leakage checks. |
| `05_label_and_image_quality_review/` | Review of suspicious labels and low-quality images. |
| `06_baseline_reproduction/` | Baseline evaluation reproduction without training. |
| `07_error_analysis_and_improvement/` | Error diagnosis, remedies, and measurable acceptance tests. |
| `08_uncertainty_and_ood_readiness/` | Requirements for calibration, OOD detection, and Unknown decisions. |
| `09_other_class_decision/` | Comparison plan for 121+OOD versus a 122-class Other experiment. |
| `10_llava_readiness_gate/` | Conditions and boundaries for LLaVA integration. |
| `11_final_decision/` | Final findings and recommended next action. |
| `configs/` | Audit-only configuration that does not change the baseline. |
| `scripts/` | Tested read-only programs for static analysis, external asset verification, image integrity, prediction export, and uncertainty analysis. |
| `tests/` | Unit tests for audit calculations. |
| `working_copies/` | Isolated copies of baseline code when experimental edits are required. |
| `audit_results/` | Generated audit results that do not replace baseline reports. |
| `.gitignore` | Prevents local logits, checkpoints, and visual review sheets from entering Git. |

The `train`, `val`, and `test` images and `.pt` weights remain outside GitHub. Their locations and hashes will be recorded in the input inventory.

## Detailed numbered-directory contents

### `00_scope_and_rules/`

| File | Purpose |
| --- | --- |
| `README.md` | Defines the audit scope, permitted read-only operations, baseline protection rules, and completion criteria. |

### `01_input_inventory/`

| File | Purpose |
| --- | --- |
| `README.md` | Explains how external datasets, checkpoints, archives, reports, and code are inventoried. |
| `RECEIVED_ASSETS_2026-09-23.md` | Documents the received checkpoint/results, incomplete full-dataset export, partial MENA selected archive, and cleaning-review archive. |
| `RECEIVED_SPLIT_ARCHIVES_2026-09-24.md` | Documents the valid but incomplete train/validation/test ZIP files and their manifest matches. |

### `02_checkpoint_verification/`

| File | Purpose |
| --- | --- |
| `README.md` | Lists the required checkpoint identity and compatibility checks. |
| `VERIFICATION_RESULT.md` | Records the verified SHA-256, DINOv2 ViT-B/14 architecture, 121-class mapping, preprocessing metadata, and strict state-dict load. |

### `03_dataset_integrity/`

| File | Purpose |
| --- | --- |
| `README.md` | Describes full-dataset decode, hash, dimension, format, color-mode, EXIF, and resolution checks. |
| `FULL_DATASET_INTEGRITY_FINDINGS.md` | Summarizes the read-only audit of all 105,681 images and the identified quality flags. |

### `04_duplicates_and_leakage/`

| File | Purpose |
| --- | --- |
| `README.md` | Describes exact and perceptual cross-split duplicate checks. |
| `NEAR_DUPLICATE_LEAKAGE_FINDINGS.md` | Documents six pHash candidates, five confirmed same-photo train/test leaks, one rejected false positive, impact, and remediation. |

### `05_label_and_image_quality_review/`

| File | Purpose |
| --- | --- |
| `README.md` | Routes label, image-quality, tiny-image, and low-resolution evidence. |
| `MENA_CLEANING_REVIEW_FINDINGS.md` | Explains why 91 cleaning-review images are evidence only and must not be auto-merged without independent relabeling. |
| `TINY_KUNAFA_FINDINGS.md` | Records and interprets the five unusably thin Kunafa source-image strips. |
| `LOW_RESOLUTION_PROFILE.md` | Quantifies images below the 336-pixel input size and explains their concentration in Arabic/MENA sources. |

### `06_baseline_reproduction/`

| File | Purpose |
| --- | --- |
| `README.md` | Defines baseline reproduction without training or parameter changes. |
| `MENA12_TEST_REPRODUCTION.md` | Reproduces the 523-image MENA-12 subset with Top-1/2/3/5 and per-class results. |
| `FULL_TEST_REPRODUCTION.md` | Reproduces the full test split, compares CPU/FP32 with the preserved CUDA/FP16 report, and reports de-leaked sensitivity. |

### `07_error_analysis_and_improvement/`

| File | Purpose |
| --- | --- |
| `README.md` | Explains how observed errors become measurable remediation proposals. |
| `EXIF_LOADER_FINDINGS.md` | Documents missing EXIF transpose in protected loaders and the corrected deployment requirement. |
| `MENA12_ERROR_REVIEW.md` | Reviews MENA-subset errors, confusion patterns, confidence behavior, and targeted actions. |
| `VALIDATION_ERROR_ANALYSIS.md` | Summarizes full validation errors, weakest classes, the MENA/Food-101 gap, and ordered improvement experiments. |
| `FULL_TEST_ERROR_ANALYSIS.md` | Summarizes full-test groups and confusions and quantifies Top-3 versus Top-5 in the review band. |

### `08_uncertainty_and_ood_readiness/`

| File | Purpose |
| --- | --- |
| `README.md` | Entry point for calibration, selective prediction, OOD, and Unknown readiness. |
| `DECISION_PROTOCOL.md` | Defines validation-only selection and automated `Accept / Review / Unknown / Invalid Image` behavior. |
| `VALIDATION_CALIBRATION_FINDINGS.md` | Documents Top-k, temperature `0.73`, calibration improvement, threshold comparisons, and the provisional `0.8599` acceptance threshold. |
| `FROZEN_POLICY_TEST_FINDINGS.md` | Applies the validation-frozen policy to independent test and states the remaining OOD gate. |

### `09_other_class_decision/`

| File | Purpose |
| --- | --- |
| `README.md` | Defines the evidence gate for 121 classes plus Unknown versus a separate 122-class `Other` experiment. |

### `10_llava_readiness_gate/`

| File | Purpose |
| --- | --- |
| `README.md` | Defines prerequisites and safety boundaries before LLaVA reviews uncertain classifier outputs. |

### `11_final_decision/`

| File | Purpose |
| --- | --- |
| `README.md` | Defines the final recommendation contents after test and grouped OOD evidence are complete. |

## Configuration, scripts, and tests

### `configs/`

| File | Purpose |
| --- | --- |
| `README.md` | Explains audit-only configuration and the prohibition on committing local machine paths. |
| `audit_config.json` | Stores expected architecture, class count, dataset counts, input size, checkpoint SHA, and repository-relative report references. |

### `scripts/`

| File | Purpose |
| --- | --- |
| `README.md` | Documents usage, outputs, and safety boundaries for every audit program. |
| `run_static_audit.py` | Cross-checks committed registry, metric, manifest, configuration, split-count, and preprocessing evidence. |
| `verify_external_assets.py` | Verifies a supplied checkpoint and optional dataset without committing private paths. |
| `audit_split_archives.py` | Audits received split ZIPs for validity, completeness, decoding, and manifest membership. |
| `audit_received_mena_archives.py` | Audits partial MENA archives, download-error placeholders, decoding, hashes, and manifest membership. |
| `audit_dataset_images.py` | Performs concurrent read-only decode, SHA-256, dimension, EXIF, format, color-mode, tiny-image, and low-resolution checks. |
| `audit_near_duplicate_leakage.py` | Searches all cross-split perceptual hashes through the configured Hamming-distance limit. |
| `export_predictions.py` | Runs the protected checkpoint and saves per-image logits, targets, relative paths, classes, loader mode, and timing outside Git. |
| `summarize_prediction_export.py` | Converts local logits into compact Top-k, per-class, confusion, confidence, and per-error JSON. |
| `analyze_uncertainty.py` | Fits validation-only temperature scaling and evaluates thresholds, coverage, selective accuracy, error detection, OOD acceptance, and confidence intervals. |
| `evaluate_frozen_test_policy.py` | Validates test logits and applies fixed validation-selected values with leakage, subgroup, and review-band analysis. |

### `tests/`

| File | Purpose |
| --- | --- |
| `test_uncertainty.py` | Tests softmax, temperature effects, tied-threshold selection, Wilson intervals, and Top-3 reporting. |
| `test_frozen_policy.py` | Tests cross-platform leakage-path matching and Top-3/Top-5 review-band accounting. |

### `working_copies/`

| File | Purpose |
| --- | --- |
| `README.md` | Defines where renamed experimental copies may be placed when protected baseline code must not be edited. |

## Generated compact results

All files below are inside `audit_results/`. They are reproducible summaries and do not replace `reports/baseline_121/`.

| File | Purpose |
| --- | --- |
| `README.md` | Result inventory and explanation of what remains local versus committed. |
| `STATIC_AUDIT_FINDINGS.md` | Human-readable findings derived from committed baseline metadata and reports. |
| `static_audit.json` | Machine-readable static checks, confidence intervals, priorities, and next runs. |
| `external_asset_verification.json` | Sanitized checkpoint identity and compatibility verification. |
| `received_mena_archives_audit.json` | Partial MENA archive integrity and final-manifest comparison. |
| `received_split_archives_audit.json` | Train/validation/test ZIP completeness and manifest comparison. |
| `mena_review_model_agreement.json` | Diagnostic agreement with unverified cleaning-review labels; it is not an accuracy claim. |
| `mena12_test_reproduction.json` | Machine-readable reproduction of the 523-image MENA-12 subset. |
| `dataset_image_audit_train.json` | Full train split integrity summary and bounded issue examples. |
| `dataset_image_audit_val.json` | Full validation split integrity summary and bounded issue examples. |
| `dataset_image_audit_test.json` | Full test split integrity summary and bounded issue examples. |
| `near_duplicate_leakage_audit.json` | Automated cross-split pHash candidates and search metadata. |
| `near_duplicate_visual_review.json` | Human decisions for every near-duplicate candidate. |
| `validation_prediction_summary.json` | Full validation Top-k, per-class, confusion, confidence, and per-error summary. |
| `validation_uncertainty_target_097.json` | Validation-only policy targeting 97.0% accepted accuracy. |
| `validation_uncertainty_target_098.json` | Validation-only policy targeting 98.0% accepted accuracy. |
| `validation_uncertainty_target_0985.json` | Validation-only policy targeting 98.5% accepted accuracy. |
| `validation_uncertainty_target_099.json` | Validation-only policy targeting 99.0% accepted accuracy; the current leading validation candidate. |
| `validation_uncertainty_target_0995.json` | Validation-only policy targeting 99.5% accepted accuracy. |
| `frozen_policy_test_results.json` | Full and de-leaked test metrics, fixed-policy behavior, subgroup results, review-band Top-k evidence, and confusions. |

## External artifacts intentionally not committed

| Artifact | Reason |
| --- | --- |
| `final_food_dataset_v2/` | The 105,681 controlled images are too large for ordinary Git and the protected dataset remains immutable. |
| `best_checkpoint.pt` | The verified model is approximately 1 GB and is identified by SHA-256 instead of being copied here. |
| Validation/test `.npz` logits | Generated per-image outputs remain local; compact JSON summaries are committed. |
| Temporary visual-review image copies | Local review aids are not project artifacts. |
