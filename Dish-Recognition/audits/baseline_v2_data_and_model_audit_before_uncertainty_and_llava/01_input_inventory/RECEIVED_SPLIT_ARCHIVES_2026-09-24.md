# Received Split Archives — 2026-09-24

The three ZIP files open successfully and use the expected `train`, `val`, and `test` roots. They are incomplete because the cloud export replaced many images with text download-error placeholders.

| Archive | Images received | Expected images | Classes with images | Result |
| --- | ---: | ---: | ---: | --- |
| `train.zip` | 2,072 | 76,198 | 13 | Incomplete |
| `val.zip` | 1,198 | 3,630 | 41 | Incomplete |
| `test.zip` | 1,868 | 25,853 | 19 | Incomplete |

The dominant recorded failure is `TooManyRequestsMeTAException`, accompanied by a smaller number of `WebException` failures. These archives must not be used for training, calibration, or final evaluation.

Every received image decodes successfully, matches a manifest SHA-256, belongs to the correct split, and has the recorded dimensions. The images themselves are valid; the download is incomplete.

The archives are missing files beyond the explicit error placeholders:

- Train: 66,139 expected images have neither an image nor an error placeholder.
- Validation: 260 expected images have neither an image nor an error placeholder.
- Test: 15,837 expected images have neither an image nor an error placeholder.

This indicates both cloud rate limiting and a large-folder export limit or truncation. Repeating the same browser ZIP export is not a reliable recovery method.

The audit script validates every successfully downloaded image against the committed manifest without extracting or modifying the archive.
