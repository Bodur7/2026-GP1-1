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
