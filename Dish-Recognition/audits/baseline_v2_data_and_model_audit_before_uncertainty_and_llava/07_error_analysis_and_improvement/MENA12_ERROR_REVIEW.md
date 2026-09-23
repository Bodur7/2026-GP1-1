# MENA-12 Error Review

## Evidence

The reproduced 523-image test run contains 12 Top-1 errors. Eleven true labels are ranked second and one is ranked third. Top-3 therefore recovers every error in this subset.

Primary confusion patterns:

- `hininy` versus `aseeda` or `areeka`
- `saleeg` versus `Mandi`
- `hasa-adas` versus `lobster_bisque`
- `baba-ghanoush` versus `hummus`
- `arayes` versus visually similar filled or open bread dishes

## Visual review

- The `arayes` examples have high presentation variation: open meat-topped bread and rolled filled bread resemble different Food-101 categories.
- `areeka`, `hininy`, `aseeda`, and `masoub` can appear as low-texture brown mixtures with weak class-specific visual evidence.
- The misclassified `baba-ghanoush` image is a multi-dip plate with visually prominent hummus, making a single-image label ambiguous.
- The `hasa-adas` examples look like generic smooth orange soup and provide limited ingredient cues.
- The two `saleeg` examples resemble ordinary rice with chicken or meat more than a consistently creamy saleeg presentation.

## Confidence finding

Raw test confidence separates many errors but not all. Mean confidence is approximately 94.65% for correct predictions and 54.95% for errors. Eight errors are at or above 50% confidence; one visually ambiguous `baba-ghanoush`/`hummus` case reaches approximately 80%.

These test values are descriptive only. They must not select the production threshold.

## Improvement actions

1. Define visual inclusion rules for the overlapping regional classes.
2. Review training and validation images for the same presentation ambiguities.
3. Treat multi-dish images as ambiguous unless the target dish is dominant and consistently annotated.
4. Select calibration and abstention thresholds on validation only.
5. Add pair-aware evaluation for the confusion groups above.
6. Prefer up to three clarification candidates; five candidates add no measured value on this subset.
7. Fine-tune only after the data review establishes that remaining errors are learnable rather than label-policy conflicts.
