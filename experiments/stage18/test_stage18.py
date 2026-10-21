import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "stage17"))
from continuous_engine import make_paths
from run_stage17 import simulate_uniform
from run_stage18 import common_design


class CommonTestSetInvariants(unittest.TestCase):
    def test_design_is_nested_by_item_with_unique_labels(self):
        item_order, priority = common_design(4, 7, "x-y", 3)
        self.assertEqual(sorted(item_order.tolist()), list(range(7)))
        self.assertEqual(sorted(priority.ravel().tolist()), list(range(28)))
        for block, item in enumerate(item_order):
            observed = sorted(priority[:, item].tolist())
            self.assertEqual(observed, list(range(4 * block, 4 * (block + 1))))

    def test_design_is_deterministic_and_repeat_specific(self):
        first = common_design(5, 11, "x-y", 0)
        replay = common_design(5, 11, "x-y", 0)
        other = common_design(5, 11, "x-y", 1)
        np.testing.assert_array_equal(first[0], replay[0])
        np.testing.assert_array_equal(first[1], replay[1])
        self.assertFalse(np.array_equal(first[1], other[1]))

    def test_every_pair_uses_the_same_uniform_item_path(self):
        order, _ = common_design(4, 9, "x-y", 0)
        paths = np.broadcast_to(order, (6, 1, 9)).copy()
        for pair_path in paths[:, 0]:
            np.testing.assert_array_equal(pair_path, order)
            self.assertEqual(sorted(pair_path.tolist()), list(range(9)))

    def test_full_budget_has_exact_truth_and_unique_cost(self):
        scores = np.array(
            [[.9, .8, .1, .7], [.2, .3, .8, .1], [.7, .4, .6, .8]]
        )
        pairs = np.array([[0, 1], [0, 2], [1, 2]], dtype=np.int16)
        order, priority = common_design(3, 4, "x-y", 0)
        paths = np.broadcast_to(order, (3, 1, 4)).copy()
        events, _ = make_paths(scores, pairs, paths, threshold=120)
        snapshots, acquired, _, decision = simulate_uniform(
            scores, pairs, paths[:, 0], events[:, 0], priority, fractions=(1.0,)
        )
        truth = np.sign(
            scores[pairs[:, 0]].sum(axis=1) - scores[pairs[:, 1]].sum(axis=1)
        )
        self.assertEqual(len(acquired), scores.size)
        self.assertEqual(len(acquired), len(set(acquired)))
        self.assertEqual(snapshots[0]["wrong"], 0)
        np.testing.assert_array_equal(decision, truth)


if __name__ == "__main__":
    unittest.main()
