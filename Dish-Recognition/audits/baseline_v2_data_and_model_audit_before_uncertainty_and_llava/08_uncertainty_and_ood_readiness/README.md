# 08 — Uncertainty and OOD readiness

Defines the data needed to calibrate confidence and evaluate images outside the 121 supported classes. The intended result is a measured `Known / Ask User / Unknown / Invalid Image` policy rather than an arbitrary threshold.

`VALIDATION_CALIBRATION_FINDINGS.md` contains the complete validation reproduction, temperature calibration, five acceptance-policy comparisons, Top-k decision evidence, and the interim user-facing recommendation. Test and grouped OOD evaluation remain required before freezing the policy.
