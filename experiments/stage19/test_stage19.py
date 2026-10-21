import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "stage17"))
from continuous_engine import make_paths
from run_stage19 import hybrid_paths, simulate_hybrid


class CommonCoreTailInvariants(unittest.TestCase):
    def test_paths_share_core_and_remain_permutations(self):
        names = np.array(["A", "B", "C", "D"])
        pairs, paths, _, core_size = hybrid_paths(names, 9, "x-y", 3)
        self.assertEqual(core_size, 4)
        for repeat in range(3):
            common = paths[0, repeat, :core_size]
            for path in paths[:, repeat]:
                np.testing.assert_array_equal(path[:core_size], common)
                self.assertEqual(sorted(path.tolist()), list(range(9)))

    def test_pair_suffixes_are_repeat_specific(self):
        names = np.array(["A", "B", "C"])
        _, paths, _, _ = hybrid_paths(names, 12, "x-y", 2)
        self.assertFalse(np.array_equal(paths[:, 0], paths[:, 1]))

    def test_common_core_is_acquired_before_tail(self):
        scores = np.array(
            [[.9, .8, .1, .7, .4, .5], [.2, .3, .8, .1, .5, .6], [.7, .4, .6, .8, .2, .3]]
        )
        names = np.array(["A", "B", "C"])
        pairs, paths, common_priorities, core_size = hybrid_paths(names, 6, "x-y", 1)
        events, evidence = make_paths(scores, pairs, paths, threshold=120)
        tail_priority = np.arange(scores.size).reshape(scores.shape)
        _, acquired, _, _ = simulate_hybrid(
            scores,
            pairs,
            paths[:, 0],
            events[:, 0],
            evidence[:, 0],
            common_priorities[0],
            tail_priority,
            core_size,
            120,
            fractions=(0.5,),
        )
        common_items = set(paths[0, 0, :core_size].tolist())
        self.assertEqual(len(acquired), scores.shape[0] * core_size)
        self.assertEqual({item for _, item in acquired}, common_items)

    def test_full_budget_has_unique_cost_and_exact_truth(self):
        scores = np.array(
            [[.9, .8, .1, .7], [.2, .3, .8, .1], [.7, .4, .6, .8]]
        )
        names = np.array(["A", "B", "C"])
        pairs, paths, common_priorities, core_size = hybrid_paths(names, 4, "x-y", 1)
        events = np.full((len(pairs), 4), 2, dtype=np.int8)
        truth = np.sign(
            scores[pairs[:, 0]].sum(axis=1) - scores[pairs[:, 1]].sum(axis=1)
        )
        events[:, -1] = truth
        evidence = np.zeros_like(events, dtype=float)
        tail_priority = np.arange(scores.size).reshape(scores.shape)
        snapshots, acquired, _, decision = simulate_hybrid(
            scores,
            pairs,
            paths[:, 0],
            events,
            evidence,
            common_priorities[0],
            tail_priority,
            core_size,
            120,
            fractions=(1.0,),
        )
        self.assertEqual(len(acquired), scores.size)
        self.assertEqual(len(acquired), len(set(acquired)))
        self.assertEqual(snapshots[0]["wrong"], 0)
        np.testing.assert_array_equal(decision, truth)


if __name__ == "__main__":
    unittest.main()
