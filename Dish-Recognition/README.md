# Dish Recognition — Misbar

This directory contains Misbar's dish-recognition component. It preserves the verified 121-class DINOv2 baseline, its dataset reports, evaluation results, and audit files.

## Directory structure

| Folder | Purpose |
| --- | --- |
| `audits/` | Data and model audit files, scripts, tests, and results. |
| `configs/` | Configuration for the final DINOv2 training run. |
| `data/` | Local dataset location. Dataset images are not committed to Git. |
| `dataset_reports/` | Dataset counts, manifest, and duplicate/leakage reports. |
| `docs/` | Dataset, model, and workflow documentation. |
| `models/` | Local checkpoint location. Model weights are not committed to Git. |
| `reports/baseline_121/` | Final evaluation metrics and confusion reports. |
| `scripts/` | Training, evaluation, and inference scripts. |

## Quick start

Run the following commands from the root of the `2026-GP1-1` repository.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Dish-Recognition/requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Dish-Recognition/requirements.txt
```

Ask a team member for the verified baseline checkpoint and place it at:

```text
Dish-Recognition/models/best_checkpoint.pt
```

Verify the checkpoint without running inference:

```bash
python Dish-Recognition/scripts/infer_final_food_v2_dinov2.py --checkpoint Dish-Recognition/models/best_checkpoint.pt --verify-only
```

The expected SHA-256 is recorded in `Dish-Recognition/model_registry.json`. Do not use a checkpoint whose hash differs from the registered value.

## Important boundaries

- The verified baseline contains 121 output classes.
- Any experiment that adds an `other` class must use a separate checkpoint and reports.
- Training and final-test evaluation require CUDA.
- Local inference supports Apple Silicon MPS when available and otherwise uses CPU.
- Dataset images and model weights such as `.pt`, `.pth`, `.ckpt`, and `.safetensors` must not be committed to Git.
- Never commit API keys, access tokens, or private data.

See `Dish-Recognition/docs/DATA_AND_MODELS.md` for dataset and model-sharing details.