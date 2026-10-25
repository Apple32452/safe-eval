import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from joint_order import ORDERS, decide, possible_orders, state_update
from run_study import run_cells, stage22


class JointOrderChecks(unittest.TestCase):
    def test_empty_survivors_never_imply_a_sign(self):
        actual = decide(np.zeros(3, int), np.full(3, 2), np.ones(13, bool),
                        np.full(3, 2))
        np.testing.assert_array_equal(actual, [2, 2, 2])

    def test_reference_cancellation_does_not_identify_reference_edges(self):
        s, m = np.array([0, 0, 2]), np.array([2, 0, 0])
        actual = decide(s, m, ~possible_orders(s, m), np.full(3, 2))
        np.testing.assert_array_equal(actual, [2, 2, -1])
        self.assertEqual(len(ORDERS), 13)

    def test_changed_current_cell_cannot_change_its_purchase_or_proposal(self):
        scores = np.array([[0, 1, 0, 1], [1, 1, 0, 0], [1, 0, 1, 1]])
        first = run_cells(scores, (.2, .5, .8), 913)
        selected = first["trace"][3]
        changed = scores.copy()
        changed[selected["row"], selected["item"]] ^= 1
        second = run_cells(changed, (.2, .5, .8), 913)
        for left, right in zip(first["trace"][:4], second["trace"][:4]):
            self.assertEqual((left["row"], left["item"]), (right["row"], right["item"]))
            np.testing.assert_array_equal(left["q"], right["q"])
        for run in (first, second):
            self.assertEqual(len(run["trace"]), len({(r["row"], r["item"]) for r in run["trace"]}))
            self.assertTrue(all(m["correct_completion"] for g in run["stops"].values()
                                for m in g.values()))

    def test_ties_resolve_exactly_at_full_endpoints(self):
        outcome = run_cells(np.zeros((3, 2), int), (.2, .5, .8), 771)
        for method in outcome["stops"]["triangle"].values():
            self.assertEqual(method["paid"], 6)
            self.assertEqual(method["decisions"], [0, 0, 0])

    def test_stage22_footprint_matches_preserved_schedule(self):
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "stage22"))
        from run_stage22 import make_paths, simulate_graph
        scores = np.array([[1]*8, [0]*8, [0, 1]*4])
        edges = np.array([[0, 1], [0, 2]], dtype=np.int16)
        order = np.array([2, 5, 3, 1, 7, 4, 6, 0])
        paths = np.tile(order, (2, 1))
        events, _ = make_paths(scores, edges, paths[:, None, :], 80.)
        priority = np.arange(24).reshape(3, 8)
        original = simulate_graph(scores, edges, paths, events[:, 0], priority, "star_pruned")
        current = stage22(scores, (0, 1), order)
        self.assertEqual(current["paid"], original["completion_cost"])
        self.assertEqual(current["decisions"], original["decision"].tolist())


if __name__ == "__main__":
    unittest.main()
