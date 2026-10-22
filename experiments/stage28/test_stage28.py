"""Tests of identifiable target, conditional correction, and pre-draw bets."""
import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_stage28 import exact_audit, summarize
from analyze_stage28 import audit_saved
from joint_queries import (EDGES, METHODS, Evidence, bounds_for_edge,
                           corrected_edge, query_probabilities, run_experiment)


class JointQueriesTests(unittest.TestCase):
    def test_exact_unbiasedness_bounds_and_residual_covariance(self):
        result = exact_audit()
        self.assertEqual(result["enumerated_settings"], 1296 + 8 * 16 * 16 * 2)
        np.testing.assert_allclose(result["null_mean_signals"]["coupled"], [0., 0., 0.], atol=1e-12)

    def test_unqueried_scores_do_not_affect_any_edge(self):
        m = np.full((2, 2), .5)
        q = np.full((2, 2), .75)
        z = np.zeros(2, dtype=int)
        for edge in range(len(EDGES)):
            self.assertEqual(corrected_edge(edge, 1., np.array((0., 0.)), z, m, q),
                             corrected_edge(edge, 1., np.array((1., 1.)), z, m, q))

    def test_allocation_has_positive_overlap_and_expected_budget(self):
        seen = np.array(((100000, 50), (40, 100000)))
        squares = np.array(((0., 15.), (10., 0.)))
        reference = np.array((20, 80))
        q = query_probabilities(squares, seen, reference, allocation=True)
        weights = (reference + 2) / (sum(reference) + 4)
        self.assertTrue(np.all(q >= .25) and np.all(q <= 1))
        self.assertAlmostEqual(float(np.sum(q * weights)), 1.5, places=7)

    def test_bets_are_prepared_from_history_and_have_safe_factors(self):
        evidence = Evidence(adaptive=True)
        m = np.array(((.2, .8), (.3, .7)))
        q = np.array(((.25, .75), (.5, 1.)))
        bounds = [bounds_for_edge(e, m, q) for e in range(len(EDGES))]
        bets = evidence.prepare(bounds).copy()
        for edge in range(len(EDGES)):
            evidence.update(edge, -.5, bounds, bets)
        self.assertTrue(np.all(bets[:, 0] * np.array([x[0] for x in bounds])[:, None] < 1))
        self.assertTrue(np.all(bets[:, 1] * np.array([x[1] for x in bounds])[:, None] < 1))
        self.assertFalse(np.array_equal(bets, evidence.prepare(bounds)))

    def test_all_methods_charge_labels_and_record_unresolved(self):
        rows = run_experiment(repeats=2, rounds=40)
        self.assertEqual(len(rows), 10)
        self.assertEqual(len(summarize(rows)), len(METHODS) * 5)
        for row in rows:
            for method in METHODS:
                result = row["methods"][method]
                self.assertEqual(result["complete"], result["unresolved"] == 0)
                self.assertGreaterEqual(result["cost"], result["rounds"])
                self.assertLessEqual(result["cost"], 3 * result["rounds"])
                self.assertLessEqual(result["wrong"], len(EDGES))

    def test_saved_trajectories_recompute_cost_and_gate(self):
        result = audit_saved(Path(__file__).resolve().parent / "results_reference")
        self.assertEqual(result["trajectories"], 3500)
        self.assertEqual(result["exact_settings"], 5392)
        self.assertTrue(all(not x["passed"] for x in result["gate"].values()))


if __name__ == "__main__":
    unittest.main()
