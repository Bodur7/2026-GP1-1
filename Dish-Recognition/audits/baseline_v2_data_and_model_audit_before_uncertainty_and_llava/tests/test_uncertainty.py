"""Unit tests for validation-only uncertainty calculations."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze_uncertainty.py"
SPEC = importlib.util.spec_from_file_location("analyze_uncertainty", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class UncertaintyTests(unittest.TestCase):
    def test_softmax_rows_sum_to_one(self):
        probabilities = MODULE.softmax(np.asarray([[2.0, 1.0], [0.0, 0.0]]))
        np.testing.assert_allclose(probabilities.sum(axis=1), np.ones(2))

    def test_temperature_reduces_overconfidence(self):
        logits = np.asarray([[5.0, 0.0]])
        self.assertLess(MODULE.softmax(logits, 2.0).max(), MODULE.softmax(logits, 1.0).max())

    def test_selected_threshold_meets_target_including_ties(self):
        logits = np.asarray([[4.0, 0.0], [3.0, 0.0], [0.0, 3.0], [2.0, 0.0]])
        targets = np.asarray([0, 0, 1, 1])
        target_accuracy = 0.75
        threshold = MODULE.choose_threshold(logits, targets, 1.0, target_accuracy)
        result = MODULE.metrics(logits, targets, 1.0, threshold)
        self.assertGreaterEqual(result["selective_accuracy"], target_accuracy)

    def test_wilson_interval_contains_observed_rate(self):
        low, high = MODULE.wilson_interval(80, 100)
        self.assertLessEqual(low, 0.8)
        self.assertGreaterEqual(high, 0.8)

    def test_metrics_report_top3(self):
        logits = np.asarray([[3.0, 2.0, 1.0, 0.0]])
        result = MODULE.metrics(logits, np.asarray([2]), 1.0)
        self.assertEqual(result["top1_accuracy"], 0.0)
        self.assertEqual(result["top3_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
