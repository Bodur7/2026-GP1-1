#!/usr/bin/env python3
"""Extract bounded, supported-class DINOv2 embeddings from a dataset split."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from infer_final_food_v2_dinov2 import choose_device, load_checkpoint, make_transform


IMAGE_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def collect_images(
    data_root: Path, split: str, classes: list[str], max_images_per_class: int,
    selected_classes: list[str] | None = None,
) -> list[tuple[Path, str, int]]:
    split_root = data_root / split
    if not split_root.is_dir():
        raise FileNotFoundError(f"Dataset split not found: {split_root}")

    class_to_idx = {name: index for index, name in enumerate(classes)}
    requested = None if selected_classes is None else set(selected_classes)
    if requested is not None:
        unknown_requested = sorted(requested.difference(class_to_idx))
        if unknown_requested:
            raise ValueError(f"Requested classes are not in the checkpoint: {unknown_requested}")
    unknown = sorted(
        directory.name for directory in split_root.iterdir()
        if directory.is_dir() and directory.name not in class_to_idx
    )
    if unknown:
        raise ValueError(f"Unsupported class directories in {split_root}: {unknown}")

    records = []
    for class_name, class_index in class_to_idx.items():
        if requested is not None and class_name not in requested:
            continue
        directory = split_root / class_name
        if not directory.is_dir():
            continue
        images = sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        records.extend(
            (path, class_name, class_index)
            for path in images[:max_images_per_class]
        )
    if not records:
        raise ValueError(f"No supported images found in {split_root}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "val"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="New .npz output file")
    parser.add_argument("--max-images-per-class", type=positive_int, required=True)
    parser.add_argument("--classes", nargs="+", metavar="CLASS", help="Supported class names to include")
    args = parser.parse_args()

    data_root = args.data_root.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if output.suffix.lower() != ".npz":
        parser.error("--output must end in .npz")
    if output.is_relative_to(data_root):
        parser.error("--output must be outside --data-root")
    if output.exists():
        parser.error(f"Output already exists: {output}")

    model, classes, preprocessing, _ = load_checkpoint(args.checkpoint.expanduser())
    records = collect_images(data_root, args.split, classes, args.max_images_per_class, args.classes)
    transform = make_transform(preprocessing)
    device = torch.device("cuda") if torch.cuda.is_available() else choose_device()
    model.to(device).eval()
    embeddings = np.empty((len(records), 768), dtype=np.float32)

    with torch.inference_mode():
        for row, (path, _, _) in enumerate(records):
            with Image.open(path) as source:
                image = transform(source.convert("RGB")).unsqueeze(0).to(device)
            _, embedding = model.forward_with_embedding(image)
            if tuple(embedding.shape) != (1, 768):
                raise RuntimeError(f"Unexpected embedding shape for {path}: {tuple(embedding.shape)}")
            embeddings[row] = embedding[0].to(device="cpu", dtype=torch.float32).numpy()

    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        image_paths=np.asarray([str(path.relative_to(data_root)) for path, _, _ in records]),
        class_names=np.asarray([name for _, name, _ in records]),
        class_indices=np.asarray([index for _, _, index in records], dtype=np.int32),
        embeddings=embeddings,
    )
    print(f"Saved {len(records)} supported-image embeddings to {output}")


if __name__ == "__main__":
    main()
