# Audit scripts

These read-only programs write only to `audit_results/` and never modify the dataset or checkpoint.

## Static report audit

Analyzes committed metrics, confusion pairs, class evidence, the manifest, and leakage metadata. It produces improvement-oriented findings without loading images.

```bash
python audits/baseline_v2_data_and_model_audit_before_uncertainty_and_llava/scripts/run_static_audit.py
```

## External asset verification

Verifies the checkpoint SHA-256 and checks a supplied dataset directory against every manifest path. The optional hash mode performs slower byte-level verification.

```bash
python audits/baseline_v2_data_and_model_audit_before_uncertainty_and_llava/scripts/verify_external_assets.py \
  --checkpoint /path/to/best_checkpoint.pt \
  --dataset /path/to/final_food_dataset_v2 \
  --verify-image-hashes
```

Never commit machine-specific external asset paths.

## Split ZIP audit

`audit_split_archives.py` opens external train/validation/test ZIP files without extracting them. It decodes and hashes every available image, verifies the manifest split and dimensions, counts cloud download-error placeholders, and reports completeness. Incomplete archives are never accepted for training or evaluation.

## Received partial MENA archive audit

`audit_received_mena_archives.py` decodes and hashes received MENA image collections, records download-error placeholders, and determines which images are present in the final manifest. It treats the collections as evidence only and never merges them into the baseline dataset.

## Image integrity audit

After the complete dataset is available, this script decodes every image, optionally verifies every SHA-256, compares actual and recorded dimensions, and flags tiny or low-resolution files for visual review.

```bash
python audits/baseline_v2_data_and_model_audit_before_uncertainty_and_llava/scripts/audit_dataset_images.py \
  --dataset /path/to/final_food_dataset_v2 \
  --verify-hashes
```

## Prediction export and uncertainty analysis

`export_predictions.py` runs the unchanged baseline and stores per-image logits outside Git. Export validation and test separately. It supports a subset of known classes using `--mode partial-in-domain` and a grouped OOD directory using `--mode ood`.

`analyze_uncertainty.py` fits temperature scaling and selects a confidence threshold using validation only. It then reports fixed-policy test accuracy/coverage and OOD rejection. Test and OOD data never select the threshold.

```bash
python audits/baseline_v2_data_and_model_audit_before_uncertainty_and_llava/scripts/export_predictions.py \
  --checkpoint /path/to/best_checkpoint.pt --images /dataset/val --output /local/val_logits.npz

python audits/baseline_v2_data_and_model_audit_before_uncertainty_and_llava/scripts/analyze_uncertainty.py \
  --validation /local/val_logits.npz --test /local/test_logits.npz --ood /local/ood_logits.npz
```
