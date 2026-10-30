# Misbar: permanent authority of the user's human label reviews

## Approved product pipeline and pending ingredient-data replacement

For pipeline, ingredient-data integration or normalization work, read
`docs/PIPELINE_APPROACH_AR.md`. The approved pre-normalization baseline is pinned
by `approved_pipeline/CURRENT.json`; preserve its immutable snapshot and evidence.
The ingredient dataset is awaiting the teammate's revision and may embed allergen
mapping. Do not treat the current recipe file as the permanent final data version.
Keep dataset versions separate from approach versions; preserve ingredient/allergen
sources and causes. Claude is the only visible/inferred ingredient extractor.
Normalization is experimental until the user reviews and approves its results.

These instructions implement the user's explicit request that their completed
label corrections must be respected permanently, across chats and experiments.

## Required for ANY work involving dish labels, dataset copies, training,
## evaluation, validation, saved predictions, sampling, galleries or reports

1. Read `data_governance/README_AR.md` and use
   `src/dish_identifier/human_labels.py` with the required central registry
   `data_governance/human_label_registry.json` BEFORE deriving ground truth or
   judging whether a prediction is correct. This applies to Food-101 AND copied
   images in combined datasets. Never assume folder names are authoritative.
2. User decisions outrank model suggestions, folder labels, inherited manifests
   and older reports. Match images by exact SHA-256, never filename alone. Apply
   RELABEL to the reference target only; never rewrite a model prediction to make
   it agree. KEEP must override automated relabel proposals. UNSURE is unresolved,
   not a definite original label. EXCLUDE_UNUSABLE is ineligible for supervised
   targets/metrics. Preserve all raw evidence and decision history.
3. New user corrections must be persisted with `scripts/record_human_label.py`
   and their actual statement/source, then rebuild affected derived reports and
   verify that original predictions and source files remain unchanged. A note in
   a chat or one experiment alone is insufficient. Do not ask the user to redo a
   completed review already present in this registry or its source records.
4. Never silently fall back if the registry is missing, a reviewed label is not
   supported, image hashes disagree, or human decisions conflict. Stop the
   affected operation with a clear error; resolve the recorded human evidence.
   A later explicit user revision may supersede an older decision, with history.
5. Include the registry SHA-256/revision, reference basis, original labels,
   reviewed labels, excluded/unresolved counts and source evidence in new
   evaluation artifacts. Use `data_governance/active_references.json` for the
   current reviewed copies; require status=ready and the current registry SHA.
   Preserve immutable historical scores separately; they
   must not be presented as using current reviewed labels. Cached predictions
   remain valid as predictions; cached target labels/metrics must be reconciled
   or rejected before reuse. Do not re-run paid inference just to fix labels.
6. When adding or discovering a data reader/evaluator outside the integrated
   paths, wire it to the same resolver BEFORE running it. For remote execution,
   copy the registry and helper with the project; absence must fail, not bypass.
7. Keep source images, original manifests/datasets, checkpoints and production
   inference unchanged unless the human explicitly requests those changes.
   This policy is an offline reference/label policy, not a classifier override.
   Never open reserved OOD Final Test without separate explicit authorization.

## Verification

Run `python -m unittest discover -s tests -p 'test_human_labels.py'` and
`python scripts/audit_human_labels.py` for changes to this policy/registry/helper.
Use `scripts/reconcile_human_labels.py` to create reviewed copies of saved image
manifests or prediction tables; retain all original columns and predictions.
Tests must use temporary output directories and must never rebuild historical manifests in-place.

When human labels change, classification accuracy must also be refreshed from
saved per-image predictions using `scripts/report_reviewed_accuracy.py` (included
in the automatic refresh command). Distinguish full validation, conditional OOD
acceptance subsets, the error-enriched 200 sample, and historical test scores.
Never relabel a historical test score as reviewed without per-image evidence.
