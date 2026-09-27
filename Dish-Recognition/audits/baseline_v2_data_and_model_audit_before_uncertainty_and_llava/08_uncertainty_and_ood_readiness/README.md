# 08 — Uncertainty and OOD readiness

Defines the data needed to calibrate confidence and evaluate images outside the 121 supported classes. The intended result is a measured automated `Known / Review / Unknown / Invalid Image` policy rather than an arbitrary threshold. The user is not asked to select a Top-k class.

`VALIDATION_CALIBRATION_FINDINGS.md` contains the complete validation reproduction, temperature calibration, five acceptance-policy comparisons, Top-k decision evidence, and the interim user-facing recommendation. Test and grouped OOD evaluation remain required before freezing the policy.

`FROZEN_POLICY_TEST_FINDINGS.md` applies the validation-only temperature and
threshold to the independent test split, reports coverage/selective accuracy,
and explains why grouped OOD evidence is still required before production use.
