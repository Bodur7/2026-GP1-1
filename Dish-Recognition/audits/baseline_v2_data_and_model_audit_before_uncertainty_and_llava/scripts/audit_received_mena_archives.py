#!/usr/bin/env python3
"""Audit partially downloaded MENA collections against the final manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError


AUDIT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUDIT_DIR.parents[1]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def error_reason(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    for marker in ("TooManyRequestsMeTAException", "WebException"):
        if marker in text:
            return marker
    return "other"


def audit_collection(
    root: Path, manifest_by_sha: dict[str, dict], leakage_by_name: dict[tuple[str, str], dict]
) -> dict:
    images = sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)
    errors = sorted(path for path in root.rglob("*.txt") if path.is_file())
    decode_errors = []
    dimension_mismatches = []
    matched_splits = Counter()
    matched_classes = Counter()
    unmatched_classes = Counter()
    unmatched_images = []
    error_reasons = Counter()
    hashes = defaultdict(list)
    for path in errors:
        error_reasons[error_reason(path)] += 1
    for path in images:
        relative = str(path.relative_to(root))
        digest = sha256(path)
        hashes[digest].append(relative)
        try:
            with Image.open(path) as image:
                image.load()
                size = image.size
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            decode_errors.append({"file": relative, "error": str(exc)})
            continue
        row = manifest_by_sha.get(digest)
        if row:
            matched_splits[row["split"]] += 1
            matched_classes[row["class_name"]] += 1
            expected = (int(row["width"]), int(row["height"]))
            if size != expected:
                dimension_mismatches.append({
                    "class_name": row["class_name"], "manifest": expected, "actual": size
                })
        else:
            unmatched_classes[path.parent.name] += 1
            leakage_row = leakage_by_name.get((path.parent.name, path.name))
            unmatched_images.append({
                "class_name": path.parent.name,
                "filename": path.name,
                "sha256": digest,
                "documented_exclusion": leakage_row["resolution"] if leakage_row else None,
            })
    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    return {
        "images": len(images),
        "download_error_files": len(errors),
        "download_error_reasons": dict(error_reasons),
        "decoded_successfully": len(images) - len(decode_errors),
        "decode_errors": decode_errors[:100],
        "matched_final_manifest": sum(matched_splits.values()),
        "not_in_final_manifest": len(images) - sum(matched_splits.values()),
        "matched_final_splits": dict(matched_splits),
        "matched_final_classes": dict(sorted(matched_classes.items())),
        "unmatched_source_classes": dict(sorted(unmatched_classes.items())),
        "unmatched_images": unmatched_images[:100],
        "unmatched_with_documented_exclusion": sum(
            item["documented_exclusion"] is not None for item in unmatched_images
        ),
        "dimension_mismatch_count": len(dimension_mismatches),
        "dimension_mismatch_examples": dimension_mismatches[:100],
        "exact_duplicate_groups_within_received_collection": len(duplicate_groups),
        "duplicate_examples": duplicate_groups[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument(
        "--manifest", type=Path,
        default=REPO_ROOT / "dataset_reports/final_dataset_manifest_v2.csv",
    )
    parser.add_argument(
        "--leakage-report", type=Path,
        default=REPO_ROOT / "dataset_reports/final_dataset_leakage_report_v2.csv",
    )
    parser.add_argument(
        "--output", type=Path,
        default=AUDIT_DIR / "audit_results/received_mena_archives_audit.json",
    )
    args = parser.parse_args()
    for root in (args.selected_root, args.review_root):
        if not root.is_dir():
            parser.error(f"Directory not found: {root}")
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    with args.leakage_report.open("r", encoding="utf-8-sig", newline="") as stream:
        leakage = list(csv.DictReader(stream))
    manifest_by_sha = {row["sha256"]: row for row in manifest}
    leakage_by_name = {
        (row["class_name"], Path(row["excluded_image_path"]).name): row for row in leakage
    }
    result = {
        "status": "informational_partial_archives",
        "warning": "These collections are audited as received evidence and must not replace final_food_dataset_v2.",
        "selected_cleaned": audit_collection(args.selected_root, manifest_by_sha, leakage_by_name),
        "cleaning_review": audit_collection(args.review_root, manifest_by_sha, leakage_by_name),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
