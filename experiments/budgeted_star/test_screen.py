"""Accounting, nonanticipation and certificate invariants for the star screen."""
from __future__ import annotations

import itertools
import unittest

import numpy as np

from run_screen import (estimate_stopping_prefix, simulate_footprint,
                        star_offline_optimum)
from run_stage22 import star_edges
from continuous_engine import make_paths


class BudgetedStarTests(unittest.TestCase):
    def test_hindsight_optimum_matches_all_edge_subsets(self):
        for lengths in itertools.product(range(1, 5), repeat=4):
            for budget in range(1, 21):
                brute = max(len(selected) for size in range(5)
                            for selected in itertools.combinations(lengths, size)
                            if sum(selected) + max(selected, default=0) <= budget)
                self.assertEqual(star_offline_optimum(lengths, budget), brute)

    def test_forecast_reads_only_supplied_observed_prefix(self):
        observed = [0.7, 0.1, 0.4, 0.2]
        self.assertTrue(5 <= estimate_stopping_prefix(observed, 16, 80) <= 16)
        self.assertEqual(estimate_stopping_prefix(observed, 4, 80), 4)

    def test_small_binary_matrices_never_repeat_and_finish_exactly(self):
        edges = star_edges(3, 0)
        order = np.arange(3, dtype=np.int32)
        priorities = np.arange(9).reshape(3, 3)
        perm = np.tile(order, (len(edges), 1))
        for bits in itertools.product((0., 1.), repeat=9):
            matrix = np.asarray(bits).reshape(3, 3)
            events, _ = make_paths(matrix, edges, perm[:, None, :], 80)
            result = simulate_footprint(matrix, edges, order, events[:, 0],
                                        priorities, 80, budget=4, pilot=1)
            self.assertEqual(len(set(result["purchased"])),
                             result["completion_cost"])
            self.assertLessEqual(result["snapshot"]["labels"], 4)
            np.testing.assert_array_equal(
                result["final_decisions"],
                np.sign(matrix[edges[:, 0]].sum(axis=1) -
                        matrix[edges[:, 1]].sum(axis=1)).astype(np.int8))

    def test_a_hidden_single_cell_cannot_change_purchases_before_it(self):
        edges = star_edges(3, 0)
        order = np.arange(8, dtype=np.int32)
        priorities = np.arange(24).reshape(3, 8)
        perm = np.tile(order, (len(edges), 1))
        base = np.array([[1, 0, 1, 1, 1, 0, 1, 0],
                         [0, 1, 0, 1, 0, 1, 0, 1],
                         [0, 1, 1, 0, 0, 1, 0, 0]], dtype=float)
        events, _ = make_paths(base, edges, perm[:, None, :], 80)
        baseline = simulate_footprint(base, edges, order, events[:, 0],
                                      priorities, 80, budget=12, pilot=1)
        for v in range(3):
            for i in range(1, 8):
                alternative = base.copy()
                alternative[v, i] = 1 - alternative[v, i]
                alt_events, _ = make_paths(alternative, edges,
                                           perm[:, None, :], 80)
                changed = simulate_footprint(
                    alternative, edges, order, alt_events[:, 0],
                    priorities, 80, budget=12, pilot=1)
                cell = (v, i)
                if cell in baseline["purchased"]:
                    pos = baseline["purchased"].index(cell)
                    self.assertEqual(baseline["purchased"][:pos + 1],
                                     changed["purchased"][:pos + 1])
                else:
                    self.assertEqual(baseline["purchased"],
                                     changed["purchased"])


if __name__ == "__main__":
    unittest.main()
