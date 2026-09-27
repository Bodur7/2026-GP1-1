# Audit Status

## Completed

- Protected work is isolated on `audit/dish-recognition-baseline-v2`.
- Registry, metric, manifest, split-count, and preprocessing consistency checks pass.
- The available checkpoint SHA-256, architecture, 121-class mapping, preprocessing metadata, classifier-head shape, and strict state-dict load are verified.
- Static analysis identifies class-level evidence limits, weakest classes, primary confusion pairs, and manifest quality flags.
- Read-only tools for full image decoding/hash verification and per-image prediction export are implemented.
- Validation-only temperature scaling and confidence-threshold selection are implemented and unit-tested.
- The user-facing Accept / Clarify / Abstain protocol and the decision gate for an `other` experiment are documented.
- All 523 available MENA-12 test images were reproduced with the protected checkpoint: 97.7055% Top-1 and 100% Top-3/Top-5. Per-class correct counts match the committed report.
- The received partial MENA collections were decoded and matched against the final manifest without modifying the dataset.
- The complete 105,681-image dataset was audited read-only: all paths exist, all images decode, every SHA-256 matches the committed manifest, and there are no true dimension mismatches.
- Three EXIF-orientation cases, three truncated EXIF metadata warnings, five tiny Kunafa images, and 7,660 images below the 336-pixel input size on at least one side were identified for targeted analysis.
- A complete cross-split pHash search through Hamming distance 4 found six candidates. Visual review confirmed five same-class train/test near-duplicate pairs (0.0193% of test) and rejected one cross-class false positive.
- Visual review confirmed that the five sub-32-pixel Kunafa files are unusably thin source-image strips. They remain in the protected baseline but must be excluded or replaced in a corrected dataset version and sensitivity analysis.
- Low-resolution images are strongly source/class concentrated: eight Arabic/MENA classes have 88.8%–93.5% of images below the 336-pixel input size. Performance and calibration must be stratified by resolution and source group before approving retraining or thresholds.
- The protected training, evaluation, inference, and prediction-export loading paths do not apply EXIF orientation. Only three baseline images are affected, but the new user-upload pipeline must normalize EXIF before preprocessing.
- Full validation inference reproduces 96.9972% Top-1, with 99.0909% Top-3 and 99.3939% Top-5.
- Validation-selected temperature scaling (`T=0.73`) improves ECE from 6.1250% to 0.4983% and NLL from 0.18146 to 0.13582.
- The leading validation-only 99% accepted-accuracy candidate gives 94.19% direct-answer coverage, 99.01% selective accuracy, and detects 68.81% of validation errors. It is not frozen until test and OOD evaluation.
- Arabic/MENA validation Top-1 is 89.833%, versus 98.416% for Food-101. Resolution-controlled results show that low resolution alone does not explain this gap.
- Full test logits are complete and structurally validated for all 25,853 images and 121 classes.
- CPU/FP32 full-test reproduction is 94.9986% Top-1, 98.5998% Top-3, and 99.1452% Top-5. It differs from the committed CUDA/FP16 report by only three Top-1 and one Top-5 decisions.
- Excluding the five confirmed leakage files leaves 25,848 images at 94.9977% Top-1, 98.5995% Top-3, and 99.1450% Top-5.
- The validation-frozen policy reaches 90.7382% clean-test coverage, 98.4054% selective accuracy, and 71.0750% error detection. It does not preserve the 99% validation target and is not production-approved.
- The clean-test review band contains 2,394 images. Top-3 contains the truth for 89.39% and Top-5 for 93.94%; constrained LLaVA selection remains unevaluated.

## Interim findings requiring action

- Nine classes have fewer than 30 test images; eleven more have fewer than 100.
- Five Kunafa images have a recorded side shorter than 32 pixels, including one validation image.
- The largest reported directional confusion is `steak` to `filet_mignon` with 34 errors.
- Validation and test logits are available locally; grouped OOD logits are still pending.
- No representative OOD set is available, so neither an unknown threshold nor a 122nd `other` class is approved.
- The inference script has a Windows CP1252 console-print portability issue; UTF-8 mode works and the model itself is valid.
- The earlier browser-exported full-dataset ZIP remains incomplete or corrupt, but it has been superseded by the fully synchronized OneDrive dataset.
- The received MENA selected archive contains 1,339 images but also 1,621 download-error placeholders, so it is not a complete training source.
- The separately received train/validation/test ZIP files are valid archives but contain only 2,072/76,198, 1,198/3,630, and 1,868/25,853 images. All received images match the manifest; cloud rate limiting and export truncation caused the missing data.

## Waiting for external assets

- A documented external/OOD evaluation set grouped by failure type

## Next execution

1. Complete pair-aware visual review of the weakest MENA validation classes.
2. Build or receive a grouped external/OOD set and measure unknown rejection.
3. Decide among no model change, targeted data cleanup plus limited fine-tuning, or a separate 122-class experiment.
4. Apply the LLaVA readiness gate only after the classifier decision layer passes.

No retraining has been run and no protected baseline file has been changed.
