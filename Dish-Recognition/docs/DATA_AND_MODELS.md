# Data and Model Sharing

## Baseline checkpoint

The verified model is `best_checkpoint.pt`, a DINOv2 ViT-B/14 food classifier with 121 classes. Its required SHA-256 is:

```text
662b398c7e377cca59b984ede3c2d6460c70eef5d7c74beff3da57cda8c6c469
```

Place the checkpoint locally at:

```text
Dish-Recognition/models/best_checkpoint.pt
```

The checkpoint is excluded from Git because it is approximately 1 GB.

Before using it, run the VS Code task **Verify baseline checkpoint** or execute the following command from the repository root:

```bash
python Dish-Recognition/scripts/infer_final_food_v2_dinov2.py --checkpoint Dish-Recognition/models/best_checkpoint.pt --verify-only
```

## Dataset v2

The verified dataset contains:

| Split | Images | Classes |
| --- | ---: | ---: |
| train | 76,198 | 121 |
| val | 3,630 | 121 |
| test | 25,853 | 121 |

Expected local layout:

```text
Dish-Recognition/data/final_food_dataset_v2/
├── train/<class-name>/
├── val/<class-name>/
└── test/<class-name>/
```

The full dataset is stored outside Git. It should be shared through the team's approved private storage location.

Dataset evidence is stored in `Dish-Recognition/dataset_reports/`, including image counts, the dataset manifest, and duplicate/leakage reports.

## Large-file policy

Do not commit dataset images or model weights such as `.pt`, `.pth`, `.ckpt`, or `.safetensors` to Git.

If the team later chooses to use Git LFS, confirm its storage and download limits before enabling it. Until then, share large files through private storage and record their hashes in the repository.