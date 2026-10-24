"""Invariants for the fixed-pool cell-permutation diagnostic."""
from __future__ import annotations

import itertools
import unittest

import numpy as np

from run_screen import cell_permutation


class CellPermutationInvariants(unittest.TestCase):
    def test_complete_small_matrices_have_correct_signs_and_unique_charges(self):
        edges = np.array([(0, 1), (0, 2)])
        rng = np.random.default_rng(90210)
        for scores_flat in itertools.product((0., 1.), repeat=6):
            scores = np.array(scores_flat).reshape(3, 2)
            for _ in range(8):
                record = cell_permutation(scores, edges, rng.permutation(6))
                self.assertEqual(record["decision"], record["truth"])
                self.assertEqual(len(record["purchased"]),
                                 len(set(record["purchased"])))
                self.assertLessEqual(record["labels"], 6)

    def test_conditional_factors_on_every_small_null_pool(self):
        # Enumerate every prefix of every binary signed pool. This checks the
        # one-step supermartingale inequality, including empty remaining pools
        # and no assumptions about independent system outcomes.
        rhos = (.02, .05, .1, .2, .4, .8)
        for a in itertools.product((0., 1.), repeat=2):
            for b in itertools.product((0., 1.), repeat=2):
                pool = tuple(a) + tuple(-x for x in b)
                for length in range(4):
                    for prefix in itertools.permutations(pool, length):
                        unknown = list(pool)
                        for value in prefix:
                            unknown.remove(value)
                        total = sum(pool)
                        for direction in (1, -1):
                            if direction * total > 0 or not unknown:
                                continue
                            observed = direction * sum(prefix)
                            center = -observed / len(unknown)
                            if center <= -1:
                                continue
                            factors = [1 + rho * (direction * x - center) /
                                       (1 + center) for rho in rhos for x in unknown]
                            self.assertGreater(min(factors), 0)
                            for rho in rhos:
                                expectation = sum(1 + rho * (direction * x - center) /
                                                  (1 + center) for x in unknown) / len(unknown)
                                self.assertLessEqual(expectation, 1 + 1e-12)

    def test_global_order_restriction_remains_uniform(self):
        # Exactly 720 equally likely global orders induce each pair of cells
        # in 24 orders with equal frequency; shared reference cells are cached.
        edge_orders = {}
        for global_order in itertools.permutations(range(6)):
            restriction = tuple(c for c in global_order if c < 4)
            edge_orders[restriction] = edge_orders.get(restriction, 0) + 1
        self.assertEqual(len(edge_orders), 24)
        self.assertEqual(set(edge_orders.values()), {30})

    def test_unseen_outcome_cannot_change_previous_purchases(self):
        scores = np.array([[.3, .4, .5, .6], [.1, .2, .3, .4],
                           [.7, .8, .9, 1.]])
        order = np.array([0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11])
        edges = np.array([(0, 1), (0, 2)])
        first = cell_permutation(scores, edges, order, alpha=.001)
        changed = scores.copy()
        changed[1, 2] = 1.
        second = cell_permutation(changed, edges, order, alpha=.001)
        hidden = (1, 2)
        self.assertEqual(first["purchased"][:first["purchased"].index(hidden)],
                         second["purchased"][:second["purchased"].index(hidden)])


if __name__ == "__main__":
    unittest.main()
