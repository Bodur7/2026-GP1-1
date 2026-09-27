# Full 121-Class Test Reproduction

## Purpose

The protected checkpoint was run once over all 25,853 test images to obtain the
per-image logits that the committed aggregate report does not contain. No model
weight, dataset image, class mapping, or preprocessing parameter was changed.
The large NPZ remains outside Git; the compact result is stored in
`audit_results/frozen_policy_test_results.json`.

## Export validation

- Samples: 25,853
- Logit matrix: 25,853 x 121
- Targets and relative paths: 25,853 each
- Classes: 121, in checkpoint order
- Non-finite logits: 0
- Loader: legacy orientation behavior (`exif_transpose=false`)
- Device and arithmetic: CPU, float32

## Reproduced metrics

| Metric | Committed CUDA/FP16 report | CPU/FP32 logit export | Difference |
|---|---:|---:|---:|
| Top-1 | 94.9870% (24,557/25,853) | 94.9986% (24,560/25,853) | +3 images |
| Top-3 | Not previously reported | 98.5998% | New evidence |
| Top-5 | 99.1490% (25,633/25,853) | 99.1452% (25,632/25,853) | -1 image |

The tiny Top-1/Top-5 differences are consistent with borderline predictions
changing under the original CUDA autocast FP16 evaluation versus the new CPU
FP32 export. The class mapping, preprocessing, checkpoint, sample count, and
largest confusion pairs agree. This is a numerical reproduction difference,
not evidence of a different model or dataset.

## Leakage sensitivity

The five visually confirmed same-photo train/test files were matched exactly
and excluded without changing any other sample. All five were correctly
classified. The remaining 25,848 images achieve:

- Top-1: 94.9977%
- Top-3: 98.5995%
- Top-5: 99.1450%

The leakage changes Top-1 by less than 0.001 percentage point. It does not
explain the baseline's strong aggregate score, but the files must remain
excluded from any corrected dataset and clean sensitivity result.

## Interpretation

The original aggregate report is substantially reproduced and remains the
historical baseline record. The new export adds per-image confidence, rank, and
policy evidence; it does not replace the historical report and must not be used
to retune the policy on test.
