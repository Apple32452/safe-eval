"""Finite-pool validity, predictability, and matched-control checks."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_feasible import (EDGE_PANEL, K, N, PAIRS, SCENARIOS, WEIGHT,
                          fitted_proposal, one_candidate, one_case,
                          remaining_proposal, rng_for)
from run_screen import one_path, potential_ledger, score_bounds


class FeasiblePanelChecks(unittest.TestCase):
    def test_learned_proposal_preserves_finite_pool_conditional_mean(self):
        rng = np.random.default_rng(731)
        ledger = rng.choice([-1, 1], size=(K, N, len(PAIRS))) * EDGE_PANEL.T[:, None, :]
        removed = {(0, 0), (0, 1), (3, 12), (4, 4)}
        remaining = np.array([N - sum(p == k for p, _ in removed)
                              for k in range(K)], dtype=float)
        observed = sum((ledger[p, i].astype(int) for p, i in removed),
                       np.zeros(len(PAIRS), dtype=int))
        m = rng.uniform(-.9, .9, size=(len(PAIRS), K))
        q_star, _ = fitted_proposal(m, np.array([1., 1., 2., 2., 3., 3.]))
        q = remaining_proposal(remaining, q_star)
        expectation = np.zeros(len(PAIRS))
        for p in range(K):
            for i in range(N):
                if (p, i) in removed:
                    continue
                x, low, high = score_bounds(remaining, observed, m, q, p, ledger[p, i])
                self.assertTrue(np.all((x >= low - 1e-12) & (x <= high + 1e-12)))
                expectation += q[p] / remaining[p] * x
        np.testing.assert_allclose(expectation, WEIGHT * ledger.sum(axis=(0, 1)),
                                   atol=1e-12)
        remaining[-1] = 0
        q = remaining_proposal(remaining, q_star)
        self.assertEqual(q[-1], 0.)
        self.assertTrue(np.all(q[:-1] > 0))

    def test_current_outcome_cannot_change_its_own_panel_or_item(self):
        rng = rng_for("context_shift", 8)
        ledger = potential_ledger(rng, SCENARIOS["context_shift"][0])
        panels, items = rng.random((2, K * N))
        trace = []
        one_candidate(ledger, panels, items, SCENARIOS["context_shift"][1],
                      trace=trace)
        self.assertGreater(len(trace), 48)
        panel, item, q = trace[48]
        changed = ledger.copy()
        changed[panel, item, EDGE_PANEL[:, panel]] *= -1
        trace_changed = []
        one_candidate(changed, panels, items, SCENARIOS["context_shift"][1],
                      trace=trace_changed)
        self.assertEqual([(p, i) for p, i, _ in trace[:49]],
                         [(p, i) for p, i, _ in trace_changed[:49]])
        np.testing.assert_array_equal(q, trace_changed[48][2])

    def test_controls_reproduce_original_and_full_exhaustion_is_exact(self):
        rng = rng_for("context_and_cost", 0)
        amplitude, costs = SCENARIOS["context_and_cost"]
        ledger = potential_ledger(rng, amplitude)
        panels, items = rng.random((2, K * N))
        rows = one_case("context_and_cost", 0)
        for row in rows[:3]:
            original = one_path(ledger, panels, items, row["method"], costs)
            for name, value in original.items():
                self.assertEqual(row[name], value)
        full = one_candidate(ledger, panels, items, costs, required=len(PAIRS) + 1)
        self.assertEqual(full["tasks"], N * K)
        self.assertEqual(full["unique"], N * K)
        self.assertEqual(full["wrong"], 0)
        self.assertEqual(full["certified"], int(np.count_nonzero(
            ledger.sum(axis=(0, 1)))))


if __name__ == "__main__":
    unittest.main()
