# Validation Calibration and Selective-Prediction Findings

## Scope

The protected checkpoint was run with the legacy baseline preprocessing on all 3,630 validation images. Per-image logits are retained outside Git. Thresholds and temperature in this report were selected from validation only; they are not yet approved for production until the frozen policy is evaluated on test and OOD data.

## Reproduction and Top-k results

| Metric | Result | Correct images |
| --- | ---: | ---: |
| Top-1 | 96.9972% | 3,521 / 3,630 |
| Top-2 | 98.5950% | 3,579 / 3,630 |
| Top-3 | 99.0909% | 3,597 / 3,630 |
| Top-4 | 99.3113% | 3,605 / 3,630 |
| Top-5 | 99.3939% | 3,608 / 3,630 |

Top-3 recovers 76 of the 109 Top-1 errors. Ranks four and five recover 11 additional images. Review of those 11 cases shows that the true-class raw probability is generally very small (0.28% to 8.07%) while an incorrect Top-1 can be much stronger. Consequently, ranks four and five remain useful as internal diagnostic or LLaVA context, but the evidence does not support routinely showing five choices to a user.

## Calibration

Validation-selected temperature scaling found `T = 0.73`.

| Metric | Raw | Temperature-scaled |
| --- | ---: | ---: |
| Negative log-likelihood | 0.18146 | 0.13582 |
| ECE, 15 bins | 6.1250% | 0.4983% |
| Mean confidence | 90.8723% | 96.8861% |

The raw model is under-confident on average, despite some individual errors being highly confident. Temperature scaling materially improves aggregate calibration but cannot identify every error or reject OOD by itself.

## Validation-only policy comparison

| Target accepted accuracy | Calibrated threshold | Direct-answer coverage | Observed accepted accuracy | Validation errors detected |
| ---: | ---: | ---: | ---: | ---: |
| 97.0% | 0.1739 | 99.97% | 97.02% | 0.92% |
| 98.0% | 0.5528 | 98.18% | 98.01% | 34.86% |
| 98.5% | 0.7103 | 96.58% | 98.52% | 52.29% |
| 99.0% | 0.8599 | 94.19% | 99.01% | 68.81% |
| 99.5% | 0.9845 | 79.20% | 99.51% | 87.16% |

The 99% target is the leading validation-only candidate: it gives a direct answer for 94.19% of validation images, routes 5.81% to clarification, and catches 68.81% of Top-1 errors. This is not frozen until test and OOD evaluation.

For the 211 images routed to clarification by the 99% candidate, Top-1 accuracy is 64.45%, Top-2 coverage of the truth is 83.41%, Top-3 is 88.15%, and Top-5 is 92.42%. The proposed product behavior is therefore dynamic: show one answer for accepted cases and at most three materially plausible choices for clarification. Preserve Top-5 internally for review rather than exposing five weak guesses.

## Stratified findings

- The 20 Arabic/MENA classes achieve 89.833% Top-1 on validation (539/600).
- The 101 Food-101 classes achieve 98.416% Top-1 (2,982/3,030).
- All low-resolution images achieve 92.540%, versus 97.703% for the remaining images.
- This resolution comparison is confounded by source and class. Within MENA, low-resolution images achieve 90.544% and other images 88.845%. Within Food-101, the corresponding values are 97.279% and 98.474%.

Low resolution alone is therefore not the primary cause of the MENA gap and must not be used as a blanket deletion rule. Class definition, visual overlap, sample diversity, and source imbalance require targeted review.

The weakest validation classes are `aseeda` and `hininy` (76.67%), followed by `Kibbeh` (80.00%), then `Shishabark`, `baba-ghanoush`, and `saleeg` (83.33%). Frequent interpretable confusions include `areeka`/`hininy`/`aseeda`, `hininy`/`masoub`, `saleeg` with other rice or mixed dishes, and `steak`/`filet_mignon`.

The unusably thin Kunafa validation strip happens to be classified correctly. That does not make it a valid sample; it must still be excluded in sensitivity analysis and replaced or removed from a corrected dataset version.

## Interim product recommendation

1. Keep the protected 121-class checkpoint unchanged.
2. Keep Top-5 internally, but use dynamic user-facing Top-k capped at three.
3. Carry the 99% validation candidate into frozen test evaluation, alongside the full comparison table.
4. Do not label low confidence as `other` yet. Use a decision-layer `Clarify` or `Unknown` state.
5. Do not approve an unknown/OOD threshold until a grouped OOD set is evaluated.
6. Prioritize MENA class-policy and targeted data review before any fine-tuning experiment.

