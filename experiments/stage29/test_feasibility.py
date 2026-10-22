"""Independent small-population checks of the local cost calculation."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_feasibility import local_cost_ratio, threshold, variance_terms


class FeasibilityTests(unittest.TestCase):
    def test_enumerated_randomized_query_variance(self):
        a = np.array([0., 0., 1., 1.])
        b = np.array([0., 1., 1., 0.])
        m = np.array([.25, .25, .75, .75])
        q = .75
        v, r = variance_terms(a, b, m)
        outcomes = np.concatenate([a - m, a - m - (b - m) / q])
        probabilities = np.concatenate([np.full(4, (1 - q) / 4), np.full(4, q / 4)])
        mean = np.dot(probabilities, outcomes)
        variance = np.dot(probabilities, (outcomes - mean) ** 2)
        self.assertAlmostEqual(mean, (a - b).mean())
        self.assertAlmostEqual(variance, v + (1 / q - 1) * r)
        self.assertAlmostEqual(local_cost_ratio(v, r, q, 1),
                               variance * (1 + q) / (2 * v))

    def test_amortization_changes_feasibility(self):
        q = .75
        self.assertAlmostEqual(threshold(q, 1), 3 / 7)
        self.assertGreater(threshold(q, 1 / 17), .92)
        self.assertGreater(local_cost_ratio(1, .6, q, 1), 1)
        self.assertLess(local_cost_ratio(1, .6, q, 1 / 17), 1)

    def test_zero_residual_and_zero_gap(self):
        a = np.array([0., 1., 0., 1.])
        b = 1 - a
        v, r = variance_terms(a, b, 1 - a)
        self.assertEqual(r, 0)
        self.assertLess(local_cost_ratio(v, r, .75, 1), 1)
        with self.assertRaises(ValueError):
            local_cost_ratio(0, r, .75, 1)


if __name__ == "__main__":
    unittest.main()
