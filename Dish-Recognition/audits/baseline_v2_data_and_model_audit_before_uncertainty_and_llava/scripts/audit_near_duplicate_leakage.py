#!/usr/bin/env python3
"""Find cross-split near-duplicate candidates from verified 64-bit pHashes."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


AUDIT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUDIT_DIR.parents[1]
SPLIT_PAIRS = (("train", "val"), ("train", "test"), ("val", "test"))


def relative_path(row: dict[str, str]) -> str:
    return str(Path(row["split"]) / row["class_name"] / Path(row["final_image_path"]).name)


def segment_layout(bit_count: int, segment_count: int) -> list[tuple[int, int]]:
    """Return (shift, mask) segments covering every bit exactly once."""
    base, remainder = divmod(bit_count, segment_count)
    layout = []
    shift = 0
    for segment in range(segment_count):
        width = base + (1 if segment < remainder else 0)
        layout.append((shift, (1 << width) - 1))
        shift += width
    return layout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, default=4)
    parser.add_argument("--max-examples", type=int, default=500)
    parser.add_argument(
        "--output",
        type=Path,
        default=AUDIT_DIR / "audit_results/near_duplicate_leakage_audit.json",
    )
    args = parser.parse_args()
    if not 0 <= args.threshold < 16:
        parser.error("--threshold must be between 0 and 15")

    manifest_path = REPO_ROOT / "dataset_reports/final_dataset_manifest_v2.csv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    records = [
        {
            "split": row["split"],
            "class_name": row["class_name"],
            "path": relative_path(row),
            "phash": int(row["phash"], 16),
        }
        for row in rows
    ]

    # If two 64-bit hashes differ in at most t bits, at least one of t+1
    # disjoint segments must match exactly. This produces a complete candidate
    # set without an O(n^2) all-pairs scan.
    layout = segment_layout(64, args.threshold + 1)
    buckets: dict[tuple[int, int], dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for index, record in enumerate(records):
        for segment, (shift, mask) in enumerate(layout):
            value = (record["phash"] >> shift) & mask
            buckets[(segment, value)][record["split"]].append(index)

    matches: dict[tuple[int, int], int] = {}
    comparisons = 0
    for split_groups in buckets.values():
        for left_split, right_split in SPLIT_PAIRS:
            for left in split_groups.get(left_split, ()):
                left_hash = records[left]["phash"]
                for right in split_groups.get(right_split, ()):
                    comparisons += 1
                    pair = (left, right) if left < right else (right, left)
                    if pair in matches:
                        continue
                    distance = (left_hash ^ records[right]["phash"]).bit_count()
                    if distance <= args.threshold:
                        matches[pair] = distance

    candidates = []
    for (left, right), distance in matches.items():
        first, second = records[left], records[right]
        candidates.append({
            "distance": distance,
            "same_class": first["class_name"] == second["class_name"],
            "first": {
                "split": first["split"],
                "class_name": first["class_name"],
                "path": first["path"],
            },
            "second": {
                "split": second["split"],
                "class_name": second["class_name"],
                "path": second["path"],
            },
        })
    candidates.sort(key=lambda item: (
        item["distance"], not item["same_class"], item["first"]["path"], item["second"]["path"]
    ))

    distance_counts = Counter(item["distance"] for item in candidates)
    split_pair_counts = Counter(
        "-".join(sorted((item["first"]["split"], item["second"]["split"])))
        for item in candidates
    )
    result = {
        "status": "review_required" if candidates else "complete_no_candidates",
        "manifest_rows": len(records),
        "phash_bits": 64,
        "maximum_hamming_distance": args.threshold,
        "candidate_comparisons_including_segment_repeats": comparisons,
        "cross_split_candidate_pairs": len(candidates),
        "same_class_pairs": sum(item["same_class"] for item in candidates),
        "cross_class_pairs": sum(not item["same_class"] for item in candidates),
        "counts_by_distance": dict(sorted(distance_counts.items())),
        "counts_by_split_pair": dict(sorted(split_pair_counts.items())),
        "candidate_examples": candidates[: args.max_examples],
        "examples_truncated": len(candidates) > args.max_examples,
        "interpretation": (
            "pHash candidates require visual review. A small Hamming distance is evidence of visual "
            "similarity, not automatic proof that two labeled food images are duplicates."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "status", "cross_split_candidate_pairs", "same_class_pairs", "cross_class_pairs",
        "counts_by_distance", "counts_by_split_pair",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
