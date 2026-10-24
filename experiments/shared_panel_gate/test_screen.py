"""Finite-pool conditional-mean, predictable-bound and query invariants."""
import importlib.util
import unittest
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "shared_panel_screen", Path(__file__).with_name("run_screen.py"))
screen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(screen)


class SharedPanelInvariants(unittest.TestCase):
    def test_conditional_mean_after_adaptive_purchases_and_wrong_predictions(self):
        rng = np.random.default_rng(7)
        ledger = rng.choice([-1, 1], size=(screen.K, screen.N, len(screen.PAIRS)))
        ledger *= screen.EDGE_PANEL.T[:, None, :]
        removed = {(0, 0), (0, 1), (3, 12), (4, 4)}
        remaining = np.array([screen.N - sum(p == k for p, _ in removed)
                              for k in range(screen.K)], dtype=float)
        observed = sum((ledger[p, i].astype(int) for p, i in removed),
                       np.zeros(len(screen.PAIRS), dtype=int))
        m = rng.uniform(-.9, .9, size=(len(screen.PAIRS), screen.K))
        q = np.array([.05, .10, .15, .30, .20, .20])
        target = screen.WEIGHT * ledger.sum(axis=(0, 1))
        expectation = np.zeros(len(screen.PAIRS))
        for p in range(screen.K):
            for i in range(screen.N):
                if (p, i) in removed:
                    continue
                x, lo, hi = screen.score_bounds(
                    remaining, observed, m, q, p, ledger[p, i])
                self.assertTrue(np.all(x >= lo - 1e-12))
                self.assertTrue(np.all(x <= hi + 1e-12))
                expectation += q[p] / remaining[p] * x
        np.testing.assert_allclose(expectation, target, atol=1e-12)

    def test_e_factors_are_positive_and_mean_one_at_each_tie(self):
        ledger = np.zeros((screen.K, screen.N, len(screen.PAIRS)), dtype=np.int8)
        # Every target is exactly zero, including with deliberately poor m.
        m = np.full((len(screen.PAIRS), screen.K), .85)
        remaining = np.full(screen.K, screen.N, dtype=float)
        q = np.array([.05, .10, .15, .30, .20, .20])
        mean = np.zeros(len(screen.PAIRS))
        for p in range(screen.K):
            x, low, high = screen.score_bounds(
                remaining, np.zeros(len(screen.PAIRS)), m, q, p, ledger[p, 0])
            self.assertTrue(np.all(x >= low - 1e-12))
            self.assertTrue(np.all(x <= high + 1e-12))
            self.assertTrue(np.all(1 + screen.BET[None, :] * x[:, None] /
                                   np.maximum(1., -low)[:, None] >= .2 - 1e-12))
            self.assertTrue(np.all(1 - screen.BET[None, :] * x[:, None] /
                                   np.maximum(1., high)[:, None] >= .2 - 1e-12))
            mean += q[p] * x
        np.testing.assert_allclose(mean, 0., atol=1e-12)

    def test_reserve_and_pilot_full_support(self):
        remaining = np.array([96., 80., 55., 12., 1., 0.])
        m = np.zeros((len(screen.PAIRS), screen.K))
        active = np.zeros(len(screen.PAIRS), dtype=int)
        for method in screen.METHODS:
            pilot = screen.panel_proposal(remaining, m, active,
                                          np.array([1, 1, 2, 2, 3, 3]),
                                          method, 2)
            np.testing.assert_allclose(pilot, remaining / remaining.sum())
            later = screen.panel_proposal(remaining, m, active,
                                          np.array([1, 1, 2, 2, 3, 3]),
                                          method, 100)
            self.assertAlmostEqual(float(later.sum()), 1.)
            self.assertTrue(np.all(later[remaining > 0] >=
                                   .2 * remaining[remaining > 0] / remaining.sum()))
            self.assertEqual(later[-1], 0.)

    def test_unique_full_ledger_and_exact_final_truth(self):
        rng = screen.rng_for("context_shift", 2)
        ledger = screen.potential_ledger(rng, .75)
        panel_u, item_u = rng.random((2, screen.N * screen.K))
        for method in screen.METHODS:
            first = screen.one_path(ledger, panel_u, item_u, method,
                                    (1, 1, 2, 2, 3, 3))
            self.assertEqual(first, screen.one_path(
                ledger, panel_u, item_u, method, (1, 1, 2, 2, 3, 3)))
            self.assertEqual(first["tasks"], first["unique"])
            self.assertGreaterEqual(first["tasks"], screen.PILOT)
            self.assertLessEqual(first["tasks"], screen.N * screen.K)
            self.assertGreaterEqual(first["duration"], first["tasks"])
            if first["tasks"] == screen.N * screen.K:
                self.assertEqual(first["direct"] + first["exact"],
                                 first["certified"])
                self.assertEqual(first["wrong"], 0)


if __name__ == "__main__":
    unittest.main()
