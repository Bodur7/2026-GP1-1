#!/usr/bin/env python3
"""Summarize an in-domain prediction export by class and confusion pair."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np


AUDIT_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path,
        default=AUDIT_DIR / "audit_results/partial_prediction_summary.json",
    )
    args = parser.parse_args()
    data = np.load(args.predictions, allow_pickle=False)
    logits = data["logits"]
    targets = data["targets"]
    classes = data["checkpoint_classes"].tolist()
    relative_paths = data["relative_paths"].tolist()
    predicted = logits.argmax(axis=1)
    order = np.argsort(-logits, axis=1)
    top5 = order[:, :5]
    stable = logits.astype(np.float64) - logits.max(axis=1, keepdims=True)
    probabilities = np.exp(stable)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    confidence = probabilities.max(axis=1)
    correct_mask = predicted == targets
    ece = 0.0
    edges = np.linspace(0, 1, 16)
    for low, high in zip(edges[:-1], edges[1:]):
        selected = (confidence > low) & (confidence <= high)
        if selected.any():
            ece += float(selected.mean() * abs(correct_mask[selected].mean() - confidence[selected].mean()))
    per_class = []
    for index in sorted(set(targets.tolist())):
        selected = targets == index
        correct = int((predicted[selected] == index).sum())
        per_class.append({
            "class_name": classes[index],
            "images": int(selected.sum()),
            "correct": correct,
            "top1_accuracy": correct / int(selected.sum()),
            "top5_accuracy": float((top5[selected] == index).any(axis=1).mean()),
        })
    confusion = Counter(
        (classes[truth], classes[guess])
        for truth, guess in zip(targets.tolist(), predicted.tolist()) if truth != guess
    )
    misclassified = []
    for row_index in np.flatnonzero(predicted != targets):
        misclassified.append({
            "file": relative_paths[row_index],
            "true_class": classes[targets[row_index]],
            "predicted_class": classes[predicted[row_index]],
            "predicted_confidence": float(probabilities[row_index, predicted[row_index]]),
            "true_class_confidence": float(probabilities[row_index, targets[row_index]]),
            "true_class_rank": int(np.flatnonzero(order[row_index] == targets[row_index])[0] + 1),
            "top5": [
                {"class_name": classes[index], "confidence": float(probabilities[row_index, index])}
                for index in top5[row_index]
            ],
        })
    result = {
        "samples": len(targets),
        "top1_accuracy": float((predicted == targets).mean()),
        "top5_accuracy": float((top5 == targets[:, None]).any(axis=1).mean()),
        "topk_accuracy": {
            str(k): float((order[:, :k] == targets[:, None]).any(axis=1).mean())
            for k in range(1, 6)
        },
        "confidence_diagnostics": {
            "usage": "descriptive_test_only_do_not_select_thresholds_from_these_values",
            "raw_ece_15_bins": ece,
            "mean_confidence_all": float(confidence.mean()),
            "mean_confidence_correct": float(confidence[correct_mask].mean()),
            "mean_confidence_errors": float(confidence[~correct_mask].mean()),
            "errors_at_or_above_0_5": int((confidence[~correct_mask] >= 0.5).sum()),
            "errors_at_or_above_0_7": int((confidence[~correct_mask] >= 0.7).sum()),
            "errors_at_or_above_0_8": int((confidence[~correct_mask] >= 0.8).sum()),
        },
        "per_class": per_class,
        "confusion_pairs": [
            {"true_class": pair[0], "predicted_class": pair[1], "count": count}
            for pair, count in confusion.most_common(30)
        ],
        "misclassified": misclassified,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
