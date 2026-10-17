# Misbar: frozen DINOv2 + Nonlinear OOD inference

Selected detector: **FINAL_NONLINEAR_FUSION**, freeze **v20261010_01**.
Accept a prediction when `nonlinear_score >= 0.18922570362206778`.
The existing local photo tester shows accept/reject, supportedness, the threshold,
and DINOv2 Top-1/Top-3 guesses and their confidence, including rejected images.

## Install on macOS

Use Python **3.14.7**, the verified runtime, with Tcl/Tk if you want the file
chooser. From Terminal:

```sh
git clone --branch feature/ood-detection --single-branch https://github.com/Bodur7/2026-GP1-1.git
cd 2026-GP1-1
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r Dish-Recognition/requirements_nonlinear.txt
```

The frozen implementation uses `hashlib.file_digest` (Python 3.11+), but other
Python versions have not been verified for this deployment. CPU inference is
the verified execution path and requires no GPU. Windows and Linux have not
been verified. No training, datasets, feature caches, RunPod or API keys are needed.

## Get the original checkpoint from OneDrive

Download **best_checkpoint.pt** from the team's **existing shared OneDrive folder**.
No private share URL is published here. Use the original file without resaving it.
Its size is **1,040,301,749 bytes**. Suggested local destination:

```text
Dish-Recognition/models/best_checkpoint.pt
```

The checkpoint remains Git-ignored and is not included in this repository or
GitHub Releases. Verify it on macOS:

```sh
shasum -a 256 Dish-Recognition/models/best_checkpoint.pt
```

Expected SHA-256:

```text
662b398c7e377cca59b984ede3c2d6460c70eef5d7c74beff3da57cda8c6c469
```

Keep the checkpoint elsewhere if preferred; pass its path with `--checkpoint`.
The small final OE head is included at `nonlinear/shared/oe_head.pt` (376,357 bytes):

```text
131555d47e385b8dc546e08caaeaf1396922afa9bbebf99dee22d0f6f5ce3425
```

The tester checks both weights, the offline DINOv2 loader, the scorer, config,
class mapping, preprocessing, and fusion/LR artifacts before using them.
It fails if their expected hashes do not match. Do not bypass these checks.

## Test your photos

Open the existing file chooser and select one or more images:

```sh
python Dish-Recognition/manual_testing/test_nonlinear.py
```

Alternatively pass image paths (the file chooser is then not needed):

```sh
python Dish-Recognition/manual_testing/test_nonlinear.py /path/to/photo.jpg
```

For an external checkpoint:

```sh
python Dish-Recognition/manual_testing/test_nonlinear.py --checkpoint /path/to/best_checkpoint.pt /path/to/photo.jpg
```

Each run creates a new ignored folder under `Dish-Recognition/manual_testing/results/`
and opens its local `results.html`. `results.json` contains the numeric output.
Use `--no-open` to save without opening a browser, or `--output-dir /path/to/new/folder`.
Run the tester again for more photos. Results include previews and local image
paths; keep them private and outside Git.

JPEG, PNG, WebP, BMP, TIFF and GIF are supported (GIF uses its first frame).
Convert HEIC photos to JPEG or PNG first. If `tkinter` is unavailable, pass image
paths instead, or install Python with Tcl/Tk. If `Asia/Riyadh` timezone data is
unavailable on an unverified OS, install `tzdata` before running the tester.

## Interpret the result

- **Accepted:** `final_label` is the original DINOv2 Top-1 class.
- **Rejected:** `final_label` is `null`; the original guesses remain visible.
- Confidence is softmax over all **121** classes; Top-3 is not renormalized.
- Supportedness is the frozen OOD decision score, not a calibrated probability
  that the dish label is correct. Either decision can be wrong.

See the [official final results](reports/FINAL_NONLINEAR_RESULTS.md) and
[photo tester notes](manual_testing/README.md).

## Frozen implementation

`nonlinear/` contains only the required runtime subset. The scorer, LR/fusion
parameters, OE head, class mapping and preprocessing are unchanged from the
original freeze. In the deployment config only the two classifier **file-location
strings** use portable paths; the tester resolves them in memory and allows an
external checkpoint. Other config metadata records the original freeze time.
The 330-file development freeze, training/calibration code, intermediate models
and caches are not required and are not distributed with this runtime.
