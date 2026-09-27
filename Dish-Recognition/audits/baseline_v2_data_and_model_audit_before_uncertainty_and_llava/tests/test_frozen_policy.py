"""Unit tests for frozen test-policy helpers."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "evaluate_frozen_test_policy", SCRIPTS / "evaluate_frozen_test_policy.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class FrozenPolicyTests(unittest.TestCase):
    def test_normalized_path_accepts_windows_and_test_prefix(self):
        windows = MODULE.normalized_path(r"Caprese_Salad\87213.JPG")
        requested = MODULE.normalized_path("test/caprese_salad/87213.jpg".removeprefix("test/"))
        self.assertEqual(windows, requested)

    def test_review_band_separates_top3_and_top5_recovery(self):
        logits = np.asarray([
            [5.0, 4.0, 3.0, 2.0, 1.0],
            [2.0, 1.9, 1.8, 1.7, 1.6],
        ])
        targets = np.asarray([0, 4])
        result = MODULE.review_band(logits, targets, temperature=1.0, threshold=0.99)
        self.assertEqual(result["samples"], 2)
        self.assertEqual(result["top1_errors"], 1)
        self.assertEqual(result["top1_errors_with_truth_in_top3"], 0)
        self.assertEqual(result["top1_errors_with_truth_only_at_rank4_or5"], 1)


if __name__ == "__main__":
    unittest.main()
