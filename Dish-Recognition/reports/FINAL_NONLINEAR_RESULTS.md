# Misbar — FINAL_NONLINEAR_FUSION final results

## Model and frozen decision

- Classifier: **DINOv2 ViT-B/14**, 121 supported dish classes, raw 768-dimensional embedding.
- Selected detector: **FINAL_NONLINEAR_FUSION**, freeze **v20261010_01**,
  frozen on 10 October 2026 at 12:08:12 (Asia/Riyadh).
- Accept when `nonlinear_score >= 0.18922570362206778`; reject otherwise.
- The detector preserves the original classifier's Top-1 prediction; rejected
  inputs have no accepted final label.

LR uses the original softmax confidence and Top-1/Top-2 margin with its saved
standardization and logistic parameters. OE is the frozen linear 121-class head
on the raw DINOv2 embedding, scored by maximum softmax. Nonlinear fusion applies
its saved scaler and logistic parameters to **[LR, OE, LR × OE]**.
No training, fitting or recalibration is part of inference.

## Held-out final evaluation — 10 October 2026

The supported split is **final_food_dataset_v2 / TEST**: **25,853 images in 121
classes**, comprising Food-101 and 20 Arabic/MENA dish classes. The unsupported
split is **Misbar OOD Final Test**: **1,600 images in 40 held-out dish classes**,
40 images per class, sourced from **FoodX-251 (828)** and **UEC FOOD 256 (772)**.
These OOD classes are separate from OOD Development. Total evaluated: **27,453**.
These are Misbar's held-out evaluation roles, not the original sources' native
train/test labels. Final-test data were not used to fit or recalibrate the detector.

| Metric | Verified final-test value | Count / denominator |
|---|---:|---:|
| ID acceptance / supported retention | 92.5076393455% | 23,916 / 25,853 |
| ID false rejection | 7.4923606545% | 1,937 / 25,853 |
| OOD rejection | 86.1875% | 1,379 / 1,600 |
| OOD false acceptance | 13.8125% | 221 / 1,600 |
| AUROC (supported = positive; higher score = supported) | 0.9620058601 | All 27,453 images |
| Selective Top-1 accuracy on accepted supported images | 97.7295534370% | 23,373 / 23,916 |
| Original DINOv2 Top-1 on all supported images in this run | 94.9986461919% | 24,560 / 25,853 |

Selective accuracy excludes rejected ID and all OOD images; it is not overall
decision accuracy. AUROC describes ranking across thresholds, not accuracy at
the frozen operating threshold.

## Classifier and calibration context

The separately saved earlier classifier-only independent TEST record reports
Top-1 **94.987042%** and Top-5 **99.149035%**
on 25,853 images. Those values belong to that earlier run; the DINOv2 value in
the table above is from the official 10 October OOD evaluation. They must not be
combined or treated as identical run outputs.

The frozen threshold's **calibration** record accepted **690/726 (95.041322%)**
reserved supported VAL images. That is calibration retention, not held-out
final-test performance. No development metric is substituted for a final-test
metric in this report. Publishing this report did not rerun final testing.

## Limitations

Some supported dishes are rejected and some unsupported dishes are accepted.
OOD acceptance does not guarantee that the Top-1 label is correct. The
supportedness score is different from classifier confidence and is not a
calibrated probability of label correctness.

High-confidence OOD remains a concrete limitation: at original confidence ≥0.90,
Nonlinear rejected only **1/57 (1.7544%)** unsupported images
in the saved final-test analysis. These results establish performance on
unsupported dishes, not general non-food, packaging or multi-dish detection.

## Frozen identity and source records

| Artifact | Identity |
|---|---|
| Detector | FINAL_NONLINEAR_FUSION |
| Freeze version | v20261010_01 |
| Threshold / comparison | 0.18922570362206778 / >= |
| Original freeze manifest SHA-256 | `29b2f15f0992aa1281cd82a742abdbbdee8db3d4d122dfd1b43b568506ba992c` |
| DINOv2 checkpoint SHA-256 | `662b398c7e377cca59b984ede3c2d6460c70eef5d7c74beff3da57cda8c6c469` |
| OE head SHA-256 | `131555d47e385b8dc546e08caaeaf1396922afa9bbebf99dee22d0f6f5ce3425` |

This concise report is transcribed from the preserved evaluation
`official_final_test_20261010`: `analysis/aggregate_metrics.json`,
`analysis/high_confidence_analysis.json`, `analysis/FINAL_ANALYSIS_VERIFICATION.json`
and `FINAL_VERIFICATION.json`, whose content hashes were checked against the
saved `FINAL_RESULT_MANIFEST.json`. The aggregate metrics source SHA-256 is
`de36503646ced1114a92968741d009f534f92ef4ebf4bffa97aade5adbf174e6`.
Earlier classifier-only results remain in
[baseline_121/final_test_metrics.json](baseline_121/final_test_metrics.json).
Raw prediction caches, per-image outputs, intermediate reports and datasets are
intentionally excluded from this deployment.
