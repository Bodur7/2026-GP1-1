# Test your own food photos

First follow [the installation and OneDrive checkpoint instructions](../README_NONLINEAR.md).
From the repository root with the environment activated:

```sh
python Dish-Recognition/manual_testing/test_nonlinear.py
```

Choose one or more photos (hold Command for multiple selection on macOS).
The existing local HTML interface opens after inference and saves full JSON.
Pass image paths to skip the chooser, use `--checkpoint` for a checkpoint stored
elsewhere, and `--no-open` to save results without opening a browser. Run `--help`
for options. No network service, API key, dataset or GPU is needed for inference.

Each photo shows DINOv2's three highest-ranked classes and their confidence,
including rejected photos. Confidence is softmax over all 121 supported classes;
the three displayed values are not rescaled to sum to 100%.
The interface separately displays Nonlinear supportedness and its exact frozen
threshold (`0.18922570362206778`; accept on equality).

Rejected images have `final_label=null`. The original DINOv2 guess remains
available for diagnosis; an accepted image keeps the original Top-1 label.
Neither confidence nor acceptance guarantees a correct classification.

Results are stored in a new ignored `manual_testing/results/` folder for each
run. HTML contains image previews and JSON includes local image paths; do not
commit or share these files unintentionally. JPEG, PNG, WebP, BMP, TIFF and GIF
are supported; GIF uses its first frame. Convert HEIC to JPEG/PNG first.

The original interface appearance and prediction calculations are retained.
Portability changes cover only runtime/checkpoint locations and browser opening.
macOS CPU is verified; other operating systems are not verified.
