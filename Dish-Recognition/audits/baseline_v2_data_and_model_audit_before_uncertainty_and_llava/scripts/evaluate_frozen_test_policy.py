#!/usr/bin/env python3
"""Evaluate a validation-frozen confidence policy on an exported test NPZ.

This script never selects a temperature or threshold from test data. It also
reports a sensitivity result after excluding explicitly named leakage files.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path, PurePosixPath

import numpy as np

from analyze_uncertainty import metrics, softmax


AUDIT_DIR = Path(__file__).resolve().parents[1]


def normalized_path(value: str) -> str:
    return str(PurePosixPath(value.replace("\\", "/"))).lower()


def group_metrics(logits: np.ndarray, targets: np.ndarray, mask: np.ndarray,
                  temperature: float, threshold: float) -> dict:
    if not mask.any():
        return {"samples": 0}
    return metrics(logits[mask], targets[mask], temperature, threshold)


def load_mena_classes(summary_path: Path) -> set[str]:
    with summary_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        return {
            row["class_name"]
            for row in rows
            if row["source_dataset"].strip() != "Food-101"
        }


def review_band(logits: np.ndarray, targets: np.ndarray, temperature: float,
                threshold: float) -> dict:
    probabilities = softmax(logits, temperature)
    confidence = probabilities.max(axis=1)
    order = np.argsort(-probabilities, axis=1)
    prediction = order[:, 0]
    correct = prediction == targets
    review = confidence < threshold
    review_errors = review & ~correct
    in_top3 = (order[:, :3] == targets[:, None]).any(axis=1)
    in_top5 = (order[:, :5] == targets[:, None]).any(axis=1)
    rank4_or_5 = in_top5 & ~in_top3
    return {
        "definition": "Samples below the validation-selected direct-answer threshold.",
        "samples": int(review.sum()),
        "fraction_of_test": float(review.mean()),
        "top1_accuracy": float(correct[review].mean()) if review.any() else None,
        "top3_accuracy": float(in_top3[review].mean()) if review.any() else None,
        "top5_accuracy": float(in_top5[review].mean()) if review.any() else None,
        "top1_errors": int(review_errors.sum()),
        "top1_errors_with_truth_in_top3": int((review_errors & in_top3).sum()),
        "top1_errors_with_truth_only_at_rank4_or5": int((review_errors & rank4_or_5).sum()),
        "top1_errors_not_in_top5": int((review_errors & ~in_top5).sum()),
        "interpretation": (
            "Top-k inclusion is diagnostic evidence only. It does not measure whether "
            "LLaVA can select the correct candidate."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--dataset-summary", type=Path, required=True)
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument(
        "--output", type=Path,
        default=AUDIT_DIR / "audit_results/frozen_policy_test_results.json",
    )
    args = parser.parse_args()

    with np.load(args.predictions, allow_pickle=False) as data:
        required = {"logits", "targets", "relative_paths", "checkpoint_classes"}
        missing = sorted(required.difference(data.files))
        if missing:
            raise ValueError(f"Prediction export is missing arrays: {missing}")
        logits = data["logits"]
        targets = data["targets"]
        paths = data["relative_paths"]
        classes = data["checkpoint_classes"]
        metadata = json.loads(data["metadata"].item()) if "metadata" in data.files else None

    if logits.shape != (len(targets), len(classes)):
        raise ValueError(f"Inconsistent shapes: logits={logits.shape}, targets={targets.shape}, classes={classes.shape}")
    if len(paths) != len(targets):
        raise ValueError("Path count does not match target count")
    if not np.isfinite(logits).all():
        raise ValueError("Logits contain non-finite values")
    if targets.min() < 0 or targets.max() >= len(classes):
        raise ValueError("Targets contain an invalid class index")

    normalized = np.asarray([normalized_path(value) for value in paths])
    exclusions = {normalized_path(value.removeprefix("test/")) for value in args.exclude}
    exclusion_mask = np.isin(normalized, sorted(exclusions))
    found = sorted(normalized[exclusion_mask].tolist())
    missing_exclusions = sorted(exclusions.difference(found))
    if missing_exclusions:
        raise ValueError(f"Requested exclusions were not found: {missing_exclusions}")
    clean = ~exclusion_mask

    mena_classes = load_mena_classes(args.dataset_summary)
    unknown_mena = sorted(mena_classes.difference(classes.tolist()))
    if unknown_mena:
        raise ValueError(f"Dataset summary classes absent from checkpoint: {unknown_mena}")
    target_names = classes[targets]
    mena = np.isin(target_names, sorted(mena_classes))

    probabilities = softmax(logits, args.temperature)
    predicted_names = classes[probabilities.argmax(axis=1)]
    confusion = Counter(
        (truth, guess)
        for truth, guess in zip(target_names[clean].tolist(), predicted_names[clean].tolist())
        if truth != guess
    )

    result = {
        "status": "test_complete_ood_pending",
        "policy_provenance": {
            "selection_split": "validation_only",
            "temperature": args.temperature,
            "confidence_threshold": args.threshold,
            "test_tuning_performed": False,
        },
        "export_validation": {
            "samples": int(len(targets)),
            "logits_shape": list(logits.shape),
            "class_count": int(len(classes)),
            "all_logits_finite": True,
            "metadata": metadata,
        },
        "historical_test_split": metrics(logits, targets, args.temperature, args.threshold),
        "de_leaked_test_split": metrics(logits[clean], targets[clean], args.temperature, args.threshold),
        "leakage_sensitivity": {
            "requested_exclusions": sorted(exclusions),
            "matched_exclusions": found,
            "excluded_samples": int(exclusion_mask.sum()),
        },
        "groups_on_de_leaked_test": {
            "mena_20": group_metrics(logits, targets, clean & mena, args.temperature, args.threshold),
            "food101_101": group_metrics(logits, targets, clean & ~mena, args.temperature, args.threshold),
        },
        "review_band_on_de_leaked_test": review_band(
            logits[clean], targets[clean], args.temperature, args.threshold
        ),
        "largest_de_leaked_confusion_pairs": [
            {"true_class": pair[0], "predicted_class": pair[1], "count": count}
            for pair, count in confusion.most_common(20)
        ],
        "limitations": [
            "This in-domain test does not establish OOD or Unknown rejection performance.",
            "The threshold remains a candidate policy until grouped OOD evaluation is complete.",
            "Top-3/Top-5 oracle inclusion does not establish LLaVA candidate-selection accuracy.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
