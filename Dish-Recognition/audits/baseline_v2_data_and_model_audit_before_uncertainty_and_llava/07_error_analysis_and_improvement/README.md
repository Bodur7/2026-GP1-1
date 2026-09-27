# 07 — Error analysis and improvement

`EXIF_LOADER_FINDINGS.md` documents that the protected loaders do not apply EXIF orientation. The effect is limited to three baseline images but is deployment-relevant for phone uploads, so the new inference/uncertainty pipeline must normalize EXIF without altering the historical baseline.

Converts errors into an improvement plan: dataset cleaning, targeted samples, preprocessing changes, limited fine-tuning, or uncertainty handling. Every remedy must have a metric and acceptance test.

`VALIDATION_ERROR_ANALYSIS.md` documents the full 121-class validation result, weakest classes, the measured MENA/Food-101 gap, and the ordered improvement experiments.
