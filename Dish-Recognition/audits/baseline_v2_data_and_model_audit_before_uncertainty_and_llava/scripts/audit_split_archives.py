#!/usr/bin/env python3
"""Audit externally stored train/validation/test ZIP files without extracting them."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image, UnidentifiedImageError


AUDIT_DIR = Path(__file__).resolve().parents[1]
DISH_ROOT = AUDIT_DIR.parents[1]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
EXPECTED_COUNTS = {"train": 76198, "val": 3630, "test": 25853}


def classify_download_error(text: str) -> str:
    if "TooManyRequestsMeTAException" in text:
        return "TooManyRequestsMeTAException"
    if "WebException" in text:
        return "WebException"
    return "other"


def audit_zip(path: Path, expected_split: str, manifest_by_sha: dict[str, dict]) -> dict:
    error_reasons = Counter()
    class_counts = Counter()
    matched_splits = Counter()
    matched_classes = Counter()
    hashes = defaultdict(int)
    decode_errors = 0
    dimension_mismatches = 0
    unmatched_hashes = []
    wrong_split_hashes = []
    image_count = 0
    with zipfile.ZipFile(path) as archive:
        entries = [item for item in archive.infolist() if not item.is_dir()]
        for entry in entries:
            suffix = PurePosixPath(entry.filename).suffix.lower()
            if suffix == ".txt":
                error_reasons[classify_download_error(archive.read(entry).decode("utf-8", errors="replace"))] += 1
                continue
            if suffix not in IMAGE_SUFFIXES:
                continue
            image_count += 1
            parts = PurePosixPath(entry.filename).parts
            if len(parts) >= 3 and parts[0] == expected_split:
                class_counts[parts[1]] += 1
            raw = archive.read(entry)
            digest = hashlib.sha256(raw).hexdigest()
            hashes[digest] += 1
            row = manifest_by_sha.get(digest)
            if row is None:
                if len(unmatched_hashes) < 100:
                    unmatched_hashes.append(digest)
            else:
                matched_splits[row["split"]] += 1
                matched_classes[row["class_name"]] += 1
                if row["split"] != expected_split and len(wrong_split_hashes) < 100:
                    wrong_split_hashes.append(digest)
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    image.load()
                    if row and image.size != (int(row["width"]), int(row["height"])):
                        dimension_mismatches += 1
            except (OSError, ValueError, UnidentifiedImageError):
                decode_errors += 1
    duplicate_groups = sum(count > 1 for count in hashes.values())
    download_error_files = sum(error_reasons.values())
    accounted_entries = image_count + download_error_files
    return {
        "filename": path.name,
        "zip_valid": True,
        "expected_split": expected_split,
        "expected_images": EXPECTED_COUNTS[expected_split],
        "images_received": image_count,
        "images_missing": EXPECTED_COUNTS[expected_split] - image_count,
        "completion_rate": image_count / EXPECTED_COUNTS[expected_split],
        "classes_with_images": len(class_counts),
        "class_counts": dict(sorted(class_counts.items())),
        "download_error_files": download_error_files,
        "download_error_reasons": dict(error_reasons),
        "images_plus_error_placeholders": accounted_entries,
        "missing_without_error_placeholder": max(
            EXPECTED_COUNTS[expected_split] - accounted_entries, 0
        ),
        "decoded_successfully": image_count - decode_errors,
        "decode_errors": decode_errors,
        "matched_final_manifest": sum(matched_splits.values()),
        "matched_manifest_splits": dict(matched_splits),
        "matched_classes": dict(sorted(matched_classes.items())),
        "unmatched_hash_count": image_count - sum(matched_splits.values()),
        "unmatched_hash_examples": unmatched_hashes,
        "wrong_manifest_split_count": sum(
            count for split, count in matched_splits.items() if split != expected_split
        ),
        "wrong_split_hash_examples": wrong_split_hashes,
        "dimension_mismatches": dimension_mismatches,
        "exact_duplicate_groups_inside_archive": duplicate_groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--val", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DISH_ROOT / "dataset_reports/final_dataset_manifest_v2.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=AUDIT_DIR / "audit_results/received_split_archives_audit.json",
    )
    args = parser.parse_args()
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    manifest_by_sha = {row["sha256"]: row for row in manifest}
    reports = {}
    for split in ("train", "val", "test"):
        archive_path = getattr(args, split)
        if not archive_path.is_file():
            parser.error(f"Archive not found: {archive_path}")
        reports[split] = audit_zip(archive_path, split, manifest_by_sha)
    result = {
        "status": "complete" if all(
            report["images_received"] == report["expected_images"]
            and report["decode_errors"] == 0
            and report["unmatched_hash_count"] == 0
            for report in reports.values()
        ) else "incomplete_download",
        "warning": "Incomplete archives must not be used for final evaluation, calibration, or training.",
        "splits": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
