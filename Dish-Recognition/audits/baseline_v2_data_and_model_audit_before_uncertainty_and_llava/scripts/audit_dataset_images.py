#!/usr/bin/env python3
"""Decode and validate every dataset image against the committed manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from PIL import Image, UnidentifiedImageError


AUDIT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUDIT_DIR.parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_image(row: dict[str, str], root: Path, verify_hashes: bool) -> dict:
    """Inspect one manifest row without mutating the source dataset."""
    relative = Path(row["split"]) / row["class_name"] / Path(row["final_image_path"]).name
    path = root / relative
    reference = str(relative)
    result = {
        "split": row["split"],
        "found": False,
        "format": None,
        "mode": None,
        "problems": [],
    }
    if not path.is_file():
        result["problems"].append(("missing", reference))
        return result
    result["found"] = True
    if verify_hashes:
        try:
            actual_hash = sha256(path)
        except OSError as error:
            result["problems"].append(
                ("read_error", {"file": reference, "error": str(error)})
            )
            return result
        if actual_hash != row["sha256"]:
            result["problems"].append(("hash_mismatch", reference))
    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            with warnings.catch_warnings(record=True) as metadata_warnings:
                warnings.simplefilter("always")
                exif_orientation = image.getexif().get(274)
            for warning in metadata_warnings:
                result["problems"].append((
                    "metadata_warning",
                    {"file": reference, "warning": str(warning.message)},
                ))
            result["format"] = str(image.format)
            result["mode"] = str(image.mode)
    except (OSError, ValueError, UnidentifiedImageError) as error:
        result["problems"].append(
            ("decode_error", {"file": reference, "error": str(error)})
        )
        return result
    expected_size = (int(row["width"]), int(row["height"]))
    if (width, height) != expected_size:
        if exif_orientation in (5, 6, 7, 8) and (height, width) == expected_size:
            result["problems"].append((
                "exif_orientation_dimension_match",
                {
                    "file": reference,
                    "manifest": expected_size,
                    "raw": [width, height],
                    "exif_orientation": exif_orientation,
                },
            ))
        else:
            result["problems"].append((
                "dimension_mismatch",
                {"file": reference, "manifest": expected_size, "actual": [width, height]},
            ))
    if min(width, height) < 32:
        result["problems"].append(("tiny_side_below_32", reference))
    if width < 336 or height < 336:
        result["problems"].append(("low_resolution", reference))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--verify-hashes", action="store_true")
    parser.add_argument(
        "--splits",
        nargs="+",
        choices=("train", "val", "test"),
        default=("train", "val", "test"),
        help="Dataset splits to audit. Defaults to all splits.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1000,
        help="Print progress after this many manifest rows (0 disables progress output).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Concurrent image readers. Use a small value for cloud-synced datasets.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=AUDIT_DIR / "audit_results/dataset_image_audit.json",
    )
    args = parser.parse_args()
    root = args.dataset.resolve()
    if not root.is_dir():
        parser.error(f"Dataset directory not found: {root}")
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    manifest_path = REPO_ROOT / "dataset_reports/final_dataset_manifest_v2.csv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["split"] in args.splits]

    problems = {
        "missing": [], "read_error": [], "decode_error": [], "hash_mismatch": [],
        "dimension_mismatch": [], "exif_orientation_dimension_match": [],
        "metadata_warning": [], "tiny_side_below_32": [], "low_resolution": [],
    }
    found = Counter()
    formats = Counter()
    modes = Counter()
    inspect = partial(inspect_image, root=root, verify_hashes=args.verify_hashes)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for index, inspected in enumerate(executor.map(inspect, rows), start=1):
            if inspected["found"]:
                found[inspected["split"]] += 1
            if inspected["format"] is not None:
                formats[inspected["format"]] += 1
            if inspected["mode"] is not None:
                modes[inspected["mode"]] += 1
            for problem_name, detail in inspected["problems"]:
                problems[problem_name].append(detail)
            if args.progress_every and (index == 1 or index % args.progress_every == 0):
                print(f"Completed {index:,}/{len(rows):,} rows", flush=True)

    summary = {key: len(value) for key, value in problems.items()}
    result = {
        "status": "complete" if not any(
            summary[key] for key in [
                "missing", "read_error", "decode_error", "hash_mismatch", "dimension_mismatch"
            ]
        ) else "failed",
        "dataset_reference": root.name,
        "requested_splits": list(args.splits),
        "manifest_rows": len(rows),
        "found_by_split": dict(found),
        "hash_verification_enabled": args.verify_hashes,
        "workers": args.workers,
        "formats": dict(formats),
        "color_modes": dict(modes),
        "problem_counts": summary,
        "problems": {key: value[:200] for key, value in problems.items()},
        "note": "Tiny and low-resolution flags require visual review; they do not automatically delete an image.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "problem_counts": summary}, indent=2))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
