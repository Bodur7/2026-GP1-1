# Misbar full pipeline — 29 October 2026

Current approach: `misbar-normalization-v3-short-top1-20261028`. This adds the full local
upload application to the existing frozen DINOv2 + Nonlinear OOD runtime.

1. Validate the image and record exact SHA-256/human-review provenance.
2. Sightengine quality gate: accept score >= 0.5.
3. Claude food-serving gate: only SINGLE_DISH passes; sides and sauces are allowed.
4. Frozen DINOv2 predicts Top-1 among 121 classes, with full-softmax confidence.
5. Frozen Nonlinear OOD accepts score >= 0.18922570362206778.
6. Retrieve ingredients and embedded allergen links from the configured data file.
7. Claude extracts visible/inferred ingredients, confidence and potential links.
8. Merge Dataset + Claude, grouping capitalization/whitespace differences.
9. Claude groups ingredient names by meaning using the concise prompt. The application
   validates every original id and rebuilds allergen unions and causes from the
   original evidence. Sources, original names and confidence remain available.

Rejection stops later stages. Provider failure is an error; requests are not
automatically retried. User-allergy profile matching remains disabled. Automated
outputs are not human-reviewed labels. Human label decisions are provenance only
and never replace the classifier's prediction.

The active normalization prompt is a single file:
`src/dish_identifier/assets/ingredient_normalization_prompt.txt`. It is the
223-word prompt approved on 28 October, including Cream + cream sauce and
Egg/eggs/whole egg/boiled egg/fried egg display grouping. Milk, Butter and Cream
remain separate. Allergen links retain their original member/source scope.
Future prompt edits update this file; prior text remains in Git history.

## English dish display names

The English presentation mapping and corrected local launcher integration were
approved by the user on 29 October 2026. Approved mapping SHA-256:
`c603cad610d284478a76604adacbeaf7e3d2cd6fb7a1a3fe8adc8e6e26064ddb`.
This approval covers presentation only; user-allergy matching remains pending.

`misbar_dish_name_mapping.json` is the single active dish-name mapping, selected
by `dish_display_mapping_file` in `configs/pipeline.json`. It contains the supplied
121 mappings. `dish_class_mapping_file` points to the existing frozen model class
catalog for exact coverage validation; no class catalog is copied or rewritten.
The application uses **`display_name_en` only**, looked up by the
exact `current_name`. The source Arabic column is retained but is not used or
returned as a display name. Edit the existing mapping file for future name changes.
Missing, duplicate, empty or unknown mappings fail explicitly; the application
does not generate names from underscores or use Arabic as a fallback.

The result contract keeps both purposes separate. For example:

```json
{
  "final_dish": "cup_cakes",
  "final_dish_display_name_en": "Cupcakes"
}
```

`final_dish` remains the original model identifier. Recipe retrieval, ingredient
data keys, Claude extraction/normalization context, Top-1 predictions and
confidence, OOD scores and human-review provenance keep their original values.
The new display field becomes available only after OOD accepts the prediction.
It stays `null` on earlier stops and OOD rejection. A later stage failure remains
an error even if dish recognition succeeded; clients must check `decision`.

The local tester uses the English field in its result heading and the additional
`display_name_en` field in its diagnostic classification card. Raw JSON retains
the original identifiers. It does not rewrite historical saved results. The
mapping SHA-256, source field and language are recorded in new results; changing
the file changes the runtime signature and requires restarting the tester.
The approved pipeline approach revision and frozen model remain unchanged.

For the later Flutter connection, show `final_dish_display_name_en` as the title
of an accepted result and keep `final_dish` for internal identity. This step
does not connect Firebase, user-allergy filtering or the Flutter preview backend.

## Setup

Run from `Dish-Recognition/Final_Model/`. Python 3.14.7 on macOS ARM64 is the verified runtime;
the existing `requirements_nonlinear.txt` pins its model libraries. Other
platforms have not been validated.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements_pipeline.txt
cp .env.example .env
chmod 600 .env
```

Edit `.env` locally to supply `SIGHTENGINE_API_USER`, `SIGHTENGINE_API_SECRET` and
`ANTHROPIC_API_KEY`. Alternatively supply private process environment variables.
Credentials stay server-side. Never commit the completed file. `configs/pipeline.json`
selects the Claude model and timeouts. Online analysis calls Sightengine and Claude.

**`best_checkpoint.pt` is already in the team's shared OneDrive folder. It is
deliberately excluded from GitHub because of its size (1,040,301,749 bytes).**
Download that original file and place it at `models/best_checkpoint.pt`, or point
`MISBAR_CHECKPOINT` to its existing local location. No new checkpoint is needed.
Expected SHA-256:

```text
662b398c7e377cca59b984ede3c2d6460c70eef5d7c74beff3da57cda8c6c469
```

```sh
python manual_testing/pipeline_app.py
# Optional external OneDrive checkpoint location:
MISBAR_CHECKPOINT=/path/to/best_checkpoint.pt python manual_testing/pipeline_app.py
```

On macOS, after setup, double-click `Test Full Pipeline.command`. The English
interface opens at http://127.0.0.1:8765. Keep the terminal open. Upload up to eight
JPEG/PNG/WebP photos (4 MB, 20 megapixels each). The Normalized tab is the final
result; source tabs retain intermediate evidence. Download per-photo JSON there.
Uploads and results stay in ignored `manual_testing/pipeline_results/` folders.
This is a loopback-only local tester, not a publicly deployed API.

## Data and provenance

The runtime reads `Misbar_Normlized_IngredientsXAllergen.json` directly, selected
in `configs/pipeline.json`, with no fallback or second active copy. This upload
contains the current source bytes: schema 2.0, dataVersion
`normalized_clean_20261028_v1`, 121 dishes and **6,049 ingredient records**, SHA-256
`143e5e7aab7abbc067d07bb91fecab0139bea00baeb135b85b4799dc166be11c`.
The earlier local approval recorded 6,056 records and a different data hash;
that historical approval is not claimed for these current bytes. Approach and
data identities remain separate. Results record the actual loaded bytes' hash
and metadata. Restart after changing data.

Prompts and schemas are checked against `src/dish_identifier/assets/manifest.json`.
The unchanged central registry/helper and active-reference receipt travel with
the runtime; missing/mismatched authority fails. Historical evaluation files
referenced by that receipt remain local and are not distributed or reused as
current metrics. This package computes no classification accuracy. Original approved snapshots and chronological review history remain intact in
the local project. They are omitted from this runtime-only upload.

The portable adapter uses the existing `manual_testing/test_nonlinear.py` loader,
verifies its hash and retains all existing checkpoint, scorer, mapping,
preprocessing, OE and fusion hash checks. Neither frozen scoring nor its threshold
changes. Full logits and embeddings still feed OOD; only the returned dish list
is reduced to Top-1. The standalone Nonlinear tester retains its original behavior.

## Validation before upload

The local preparation passed 78 Python tests, the UI rendering check and a real
DINOv2 + frozen OOD smoke check on a synthetic image with the original external
checkpoint. No paid requests, training or reserved OOD Final Test access was used.
Historical evaluation reports, example images, experiment archives and development
environments are deliberately omitted from this runtime-only upload.

The concise prompt update passed 51 Python checks and a full cached pipeline
replay. Two earlier text-only trials verified the cream-sauce case and the
approved egg forms, including allergen/evidence preservation. Publishing this
update sends no new service requests and adds no reports or experiment copies.

The English display mapping has focused offline checks in `tests/`:

```sh
python -m unittest discover -s tests -p 'test_dish_display.py' -v
node tests/test_dish_display_ui.cjs
```

These check all 121 identifiers, invalid mapping failures, English-only display,
the original classifier/recipe/Claude values, OOD rejection, human-reference
provenance and the rendered tester text. Service/model doubles and temporary
synthetic images avoid paid calls, model changes or historical-data rewrites.

## Final package location — 30 October 2026

This copy is prepared for `Dish-Recognition/Final_Model/` on `main`.
All runtime code, data, prompts and frozen components match source commit
`c22855b0c50c339d1c57566248d6c05021695b37` from `feature/pipeline-runtime`. Only documentation and
release metadata were added for packaging. Place the original external checkpoint
at `models/best_checkpoint.pt` relative to this folder. The frozen standalone
loader retains an older `Dish-Recognition/models/` hint; use this new location
or `MISBAR_CHECKPOINT`. The instruction above is authoritative for this package.

The ingredient file is the current runtime version, not a permanent final
dataset. Its hash and version are separate from the approach version. Future
Claude normalization outputs still require human review before being treated as
human evidence. User-allergy profile matching remains disabled.
