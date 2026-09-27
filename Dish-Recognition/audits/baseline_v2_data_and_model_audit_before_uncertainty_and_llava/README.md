# Baseline V2 Data and Model Audit Before Uncertainty and LLaVA

This directory is an isolated workspace for auditing Dataset V2 and the 121-class checkpoint, then identifying evidence-based improvements before uncertainty handling or LLaVA integration.

The audit is not limited to confirming reported numbers. Every discovered issue must be connected to evidence, impact, a proposed remedy, and a measurable acceptance test.

## Single-directory work boundary

All code, compact results, findings, decisions, tests, and documentation produced by this audit belong inside this directory and its existing subdirectories:

```text
Dish-Recognition/audits/
└── baseline_v2_data_and_model_audit_before_uncertainty_and_llava/
```

No separate directory is created for the Git branch. `audit/dish-recognition-baseline-v2` is only the Git branch used to isolate and review this directory's changes; it is not a storage location. The protected repository files outside this audit directory and the `main` branch remain unchanged.

Large inputs and generated artifacts are deliberately not copied into Git:

- Dataset images remain in controlled external storage.
- The verified checkpoint remains outside the repository's ordinary Git history.
- Per-image `.npz` logits remain local because they are generated, potentially large, and reproducible.
- Compact JSON summaries, Markdown findings, reproducible scripts, configurations, and tests are stored here.

## Directory map

```text
baseline_v2_data_and_model_audit_before_uncertainty_and_llava/
├── 00_scope_and_rules/                 # Scope, safety rules, and protected baseline boundaries
├── 01_input_inventory/                 # Received dataset, archive, checkpoint, and report inventory
├── 02_checkpoint_verification/         # Checkpoint SHA, architecture, class order, and load verification
├── 03_dataset_integrity/               # Full image decode, hash, dimension, format, and EXIF findings
├── 04_duplicates_and_leakage/          # Exact/near-duplicate and split-leakage findings
├── 05_label_and_image_quality_review/  # Tiny, low-resolution, and label-review evidence
├── 06_baseline_reproduction/           # Reproduced baseline evaluations
├── 07_error_analysis_and_improvement/  # Error groups and evidence-based improvement proposals
├── 08_uncertainty_and_ood_readiness/   # Calibration, thresholds, OOD protocol, and policy comparisons
├── 09_other_class_decision/            # Gate for any future 122-class Other experiment
├── 10_llava_readiness_gate/             # Requirements before LLaVA is introduced
├── 11_final_decision/                   # Final recommendation after test and OOD evidence is complete
├── audit_results/                       # Compact machine-readable JSON summaries
├── configs/                             # Audit configuration without machine-specific secrets or paths
├── scripts/                             # Reproducible audit, export, and analysis programs
├── tests/                               # Tests for audit and uncertainty calculations
├── working_copies/                      # Isolated experimental copies when protected code must not change
├── FILE_INDEX.md                        # File-by-file purpose index
└── STATUS.md                            # Verified, pending, and next work
```

Each numbered directory has its own README or findings documents. `audit_results/README.md` explains every generated compact result. `scripts/README.md` explains what each program does and how it is used without committing local asset paths.

## Work completed so far

- Verified the protected checkpoint SHA-256, DINOv2 ViT-B/14 architecture, 121-class order, preprocessing metadata, and strict load compatibility.
- Verified all 105,681 dataset images read-only against the committed manifest: no missing files, decode failures, hash mismatches, or true dimension mismatches.
- Identified five unusably thin Kunafa images, three EXIF-orientation cases, three metadata warnings, and 7,660 images below the 336-pixel input size on at least one side.
- Completed a full cross-split pHash search and visual review: five same-photo train/test leaks are confirmed and one automated cross-class candidate is rejected as a false positive.
- Reproduced the available 523-image MENA-12 test subset at 97.7055% Top-1 and 100% Top-3/Top-5.
- Reproduced all 3,630 validation images at 96.9972% Top-1, 99.0909% Top-3, and 99.3939% Top-5.
- Selected validation-only temperature `0.73`, improving 15-bin ECE from 6.1250% to 0.4983% and NLL from 0.18146 to 0.13582.
- Compared five validation-only acceptance policies. The leading provisional candidate uses threshold `0.8599`, gives 94.19% direct-answer coverage, 99.01% selective accuracy, and detects 68.81% of validation errors.
- Measured a validation Top-1 gap between the 20 Arabic/MENA classes (89.833%) and the 101 Food-101 classes (98.416%). Resolution-controlled results show that low resolution alone does not explain this gap.
- Started the one-time full test logit export required to evaluate the frozen calibration/threshold, exclude the five leaked test files in a clean metric, and define the later automated LLaVA review band. This does not retrain or alter the checkpoint.
- Completed and validated the 25,853-image full test export. CPU/FP32 reproduction is 94.9986% Top-1, 98.5998% Top-3, and 99.1452% Top-5; the tiny difference from the committed CUDA/FP16 report is three Top-1 decisions and one Top-5 decision.
- Applied validation-frozen `T=0.73` and threshold `0.8599` without test tuning. After excluding five confirmed leaks, coverage is 90.7382%, selective accuracy is 98.4054%, and error detection is 71.0750%.
- Measured Top-3/Top-5 only as candidate-recall evidence in the 2,394-image review band: 89.39% versus 93.94%. LLaVA selection accuracy and OOD rejection are still unmeasured.

## Current and next work

1. Build and evaluate a grouped OOD set before setting an Unknown threshold or approving an `Other` experiment.
2. Correct confirmed leaks and unusable Kunafa strips only in a new dataset version and measure a targeted sensitivity experiment.
3. Compare Top-3, Top-5, and dynamic Top-k only inside the automated LLaVA review band; the user is not asked to choose a class.
4. Run a separate targeted data/fine-tuning experiment only if the evidence shows it is necessary.

## Protection boundaries

- Do not edit the baseline files in `scripts/`, `configs/`, or `reports/baseline_121/`.
- Do not modify `final_food_dataset_v2` or `best_checkpoint.pt`.
- Copy code that needs experimental changes into `working_copies/` under a new name.
- Give every cleaned dataset a new version, such as `final_food_dataset_v3_clean_121`.
- Give every new checkpoint a new name, SHA-256, and independent reports.
- Keep dataset images and large weights outside ordinary Git and supply their locations through arguments or local configuration.
- Never use the test split to tune hyperparameters or decision thresholds.

## Workflow

1. Inventory the available assets.
2. Verify checkpoint identity, preprocessing, and class order.
3. Validate image integrity and reconcile the dataset with its manifest.
4. Check duplicates and split leakage.
5. Review suspicious labels and low-quality images.
6. Reproduce the baseline evaluation when the test images are available.
7. Convert errors into measurable improvement proposals.
8. Assess readiness for calibration, uncertainty, and OOD detection.
9. Decide whether a separate 122-class `Other` experiment is justified.
10. Apply a readiness gate before LLaVA integration.

See `FILE_INDEX.md` for the purpose of every file and directory.
