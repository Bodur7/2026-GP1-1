# 10 — LLaVA readiness gate

LLaVA integration does not begin until classifier performance and the uncertainty policy are stable. LLaVA reviews ambiguous cases only; it must not conceal dataset weaknesses or provide allergy-safety guarantees.

The deployed interaction is automated: the user uploads an image but is not
asked to choose among classifier candidates. For approved review cases, LLaVA
receives a constrained Top-3, Top-5, or dynamic candidate set and must return one
supported candidate or Unknown. Candidate-set size must be selected by an
end-to-end benchmark; Top-k oracle inclusion alone is insufficient.
