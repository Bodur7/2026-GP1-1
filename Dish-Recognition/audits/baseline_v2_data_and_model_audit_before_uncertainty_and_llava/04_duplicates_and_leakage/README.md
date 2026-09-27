# 04 — Duplicates and leakage

Rechecks SHA-256, perceptual hashes, near-duplicates, and leakage across train, validation, and test, including cropped or recompressed copies when images are available.

The complete audit found no exact duplicate groups and six pHash candidates at Hamming distance 4. Visual review confirmed five same-class train/test duplicate pairs and rejected one cross-class false positive. See `NEAR_DUPLICATE_LEAKAGE_FINDINGS.md`.
