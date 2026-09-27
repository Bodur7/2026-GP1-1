# 06 — Baseline reproduction

Re-evaluates the checkpoint on the actual test split after input verification. No training occurs here, and the results are not used for model tuning. New results are compared with the preserved baseline reports.

`MENA12_TEST_REPRODUCTION.md` records the protected-checkpoint reproduction on
the available regional subset. `FULL_TEST_REPRODUCTION.md` records the one-time
25,853-image test logit export, its numerical comparison with the committed
CUDA/FP16 report, and the metric after excluding five confirmed leakage files.
