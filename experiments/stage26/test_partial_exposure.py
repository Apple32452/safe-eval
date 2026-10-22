from itertools import product
import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from partial_exposure import exact_bounds, run_static
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage22"))
from run_stage22 import simulate_graph


class PartialExposureTests(unittest.TestCase):
    def test_static_matches_frozen_stage22_on_correct_path(self):
        scores = np.array([[1., 1., 1.], [0., 0., 0.], [1., 0., 0.]])
        pairs = np.array([[0, 1], [0, 2]], dtype=np.int16)
        paths = np.tile(np.arange(3), (2, 1))
        events = np.array([[2, 1, 1], [2, 2, 1]], dtype=np.int8)
        priority = np.arange(9).reshape(3, 3)
        reference = simulate_graph(scores, pairs, paths, events, priority,
                                   "star_pruned", fractions=(1.0,))
        observed = run_static(scores, pairs, paths, events, priority)
        self.assertEqual(observed["cost"], reference["completion_cost"])
        np.testing.assert_array_equal(observed["decision"], reference["decision"])

    def test_every_three_item_binary_matrix_and_every_mask(self):
        pair = np.array([[0, 1]])
        for values in product((0., 1.), repeat=6):
            scores = np.asarray(values).reshape(2, 3)
            truth = scores[0].sum() - scores[1].sum()
            for observed in product((False, True), repeat=6):
                seen = np.asarray(observed).reshape(2, 3)
                lower, upper = exact_bounds(scores, seen, pair)
                self.assertLessEqual(lower[0], truth)
                self.assertGreaterEqual(upper[0], truth)
                if lower[0] > 0:
                    self.assertGreater(truth, 0)
                if upper[0] < 0:
                    self.assertLess(truth, 0)
                if lower[0] == upper[0] == 0:
                    self.assertEqual(truth, 0)


if __name__ == "__main__":
    unittest.main()
