# Misbar final model runtime

Final runtime package from `feature/pipeline-runtime`, prepared for `main` at
`Dish-Recognition/Final_Model/` on 30 October 2026.

Includes the frozen 121-class DINOv2 inference implementation, Nonlinear OOD
components, nine-stage pipeline, English dish display mapping, local upload UI,
current ingredient/allergen data, prompts, human-label authority and offline tests.

Start with [README_PIPELINE.md](README_PIPELINE.md) for setup and operation.
From the repository root:

```sh
cd "Dish-Recognition/Final_Model"
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements_pipeline.txt
cp .env.example .env
# Fill .env locally with the provider credentials.
python manual_testing/pipeline_app.py
```

Download the existing `best_checkpoint.pt` from the team's OneDrive share and
place it in this folder's `models/` directory before running inference, or select
it with `MISBAR_CHECKPOINT`. Its expected SHA-256 is
`662b398c7e377cca59b984ede3c2d6460c70eef5d7c74beff3da57cda8c6c469`.
The 1,040,301,749-byte checkpoint is external to this Git package. The small
verified OOD head is included unchanged.

“Final” identifies the delivered runtime revision. Ingredient data can be
replaced independently; automated normalization results are not human reviews.
User-allergy profile matching remains disabled. No new accuracy evaluation is
claimed; historical reports and datasets remain in their existing locations.
`release_manifest.json` identifies source commit, frozen components, actual
runtime data and exact delivered file hashes.

Offline package checks:

```sh
python -m unittest discover -s tests -p 'test_dish_display.py' -v
node tests/test_dish_display_ui.cjs
```
