# Uncertainty and OOD Decision Protocol

## Purpose

The application must not present an unsupported food label as a fact. The baseline classifier always returns one of its 121 classes, so a separate decision layer must decide whether that prediction is safe to show.

## Evaluation order

1. Export logits from the unchanged baseline for validation and test.
2. Fit probability temperature on validation only.
3. Select decision thresholds on validation only.
4. Freeze the policy.
5. Evaluate it once on test and on a separately designed OOD set.
6. Approve LLaVA integration only after the classifier-only policy is documented.

The test set must never select temperature, thresholds, prompts, or hyperparameters.

## Proposed automated decisions

The final numeric boundaries will come from validation results; they are not hard-coded in advance.

- **Accept:** show the Top-1 food when calibrated confidence is above the validated acceptance threshold.
- **Review:** when evidence is intermediate, pass a constrained Top-k candidate set and classifier evidence to the later LLaVA stage. The application, not the user, resolves the case.
- **Abstain:** for low confidence, likely OOD, or severe image-quality failure, state that the food could not be identified reliably. Do not force one of the 121 labels.
- **LLaVA review:** later, LLaVA may select one classifier-supported candidate or return Unknown. It must not freely invent a different dish, silently override the decision boundary, or convert a rejected OOD case into a confident known label.

Top-3, Top-5, and dynamic Top-k must be compared on the same frozen review band. The final choice is based on end-to-end selection accuracy, error rate, latency, and Unknown behavior—not on oracle Top-k inclusion alone.

## Required OOD groups

- Non-food objects and scenes
- Foods outside the 121 supported classes
- Multiple dishes with no single dominant target
- Packaged food, menus, logos, and text-heavy images
- Cropped, blurred, dark, occluded, or extremely small images
- Visually similar unsupported regional dishes

Results must be reported separately for each group so a large easy non-food group cannot hide failures on unsupported foods.

## `other` class gate

Do not add a 122nd `other` class merely because softmax is overconfident. Train it only if all conditions hold:

1. Confidence calibration and abstention remain insufficient on a representative OOD set.
2. The proposed `other` data has a stable, documented sampling policy.
3. It does not contain mislabeled examples of the 121 known classes.
4. A separate 122-class experiment improves OOD behavior without materially reducing known-class performance.

Otherwise, keep 121 outputs and implement `unknown` as a decision-layer state rather than a visual class.

## Acceptance evidence

At minimum, report known-class coverage, selective accuracy, error-detection rate, calibration error, and OOD acceptance/rejection rates. Include confidence intervals and per-group OOD results before declaring the layer production-ready.
