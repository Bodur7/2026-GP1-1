# Frozen Validation Policy on the Independent Test Split

## Frozen inputs

The policy was selected on validation and then applied to test without tuning:

- Temperature: `0.73`
- Direct-answer confidence threshold: `0.8599019576434779`
- Test images used to choose either value: none

Temperature scaling changes confidence values but not Top-k ordering or the
checkpoint weights. It makes confidence better aligned with observed
correctness, allowing a separate decision layer to decide whether a prediction
is safe to answer directly.

## Clean test policy result

These figures exclude the five confirmed same-photo train/test leaks:

| Metric | Result |
|---|---:|
| Test samples | 25,848 |
| Calibration error (ECE, 15 bins) | 0.6444% |
| Direct-answer coverage | 90.7382% (23,454 images) |
| Accuracy among direct answers | 98.4054% |
| Error-detection rate | 71.0750% |
| Sent to review/abstention | 9.2618% (2,394 images) |

The policy improves the reliability of direct answers relative to unconditional
Top-1, but it does **not** reach its 99% validation target on independent test.
There are 374 incorrect predictions inside the accepted set. It is therefore a
useful candidate policy, not a production-approved Unknown boundary.

## Group behavior

| Group | Samples | Coverage | Selective accuracy | Error detection |
|---|---:|---:|---:|---:|
| Arabic/MENA 20 | 603 | 93.3665% | 99.8224% | 91.6667% |
| Food-101 101 | 25,245 | 90.6754% | 98.3705% | 70.8821% |

The MENA group has small and uneven test counts, so its confidence interval is
wider and validation remains important. This result cannot justify relaxing a
threshold for regional dishes.

## Product meaning

For an in-domain image, this threshold can separate a high-confidence direct
answer from a harder review case. It cannot determine whether a non-food image
or an unsupported dish is Unknown because no grouped OOD set has been tested.
The intended later flow remains:

1. Validate that the upload is a usable food image.
2. Run DINOv2 and calibrate logits with `T=0.73`.
3. Directly return a class only when the final policy permits it.
4. Send the uncertain candidate set to constrained LLaVA review when approved.
5. Return Unknown when OOD evidence supports rejection; do not force a label.

The user is not asked to choose among Top-k candidates. LLaVA must output one
supported candidate or Unknown, and its performance must be evaluated separately.

## Remaining gate

Build a documented OOD set covering non-food, unsupported food, poor-quality,
multi-dish, and ambiguous inputs. Measure per-group false acceptance and tune
the final Known/Review/Unknown policy on validation/OOD development data only.
No 122nd `other` class or LLaVA integration is approved by this test alone.
