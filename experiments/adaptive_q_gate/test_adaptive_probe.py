"""Finite-null checks and ledger invariants for predictable q selection."""
import itertools
import unittest

import numpy as np

from adaptive_probe import QS, adaptive_certificate, choose_q


class AdaptiveChecks(unittest.TestCase):
    def test_chosen_factor_is_valid_for_all_compatible_fixed_nulls(self):
        n = 3
        for purchased in ([], [(0, 0, 1)], [(0, 0, 0), (1, 1, 1)]):
            seen = np.zeros((2, n), dtype=bool)
            known = np.zeros((2, n), dtype=np.int8)
            for v, i, value in purchased:
                seen[v, i], known[v, i] = True, value
            q, design, positive, fallback = choose_q(seen, known, .8, .2)
            self.assertIn(q, QS)
            compatible = []
            for bits in itertools.product((0, 1), repeat=2 * n):
                full = np.array(bits, dtype=np.int8).reshape(2, n)
                if (np.array_equal(full[seen], known[seen]) and
                        full[0].sum() <= full[1].sum()):
                    compatible.append(full)
            self.assertTrue(compatible)
            exact = max(design.row(full) @ positive for full in compatible)
            worst, _ = design.worst_null(positive, 1)
            self.assertAlmostEqual(worst, exact)
            self.assertLessEqual(worst, 1 + 1e-9)

    def test_no_repeated_purchases_and_correct_final_sign(self):
        scores = np.array([[1, 1, 1, 0, 1, 1, 1, 0],
                           [0, 0, 1, 0, 0, 0, 1, 0]], dtype=np.int8)
        result = adaptive_certificate(scores, .8, .2, seed=123)
        bought = set()
        for item, buy_a, buy_b, q in result["path"]:
            self.assertIn(q, QS)
            for v, selected in ((0, buy_a), (1, buy_b)):
                if selected:
                    self.assertNotIn((v, item), bought)
                    bought.add((v, item))
        self.assertEqual(result["cost"], len(bought))
        self.assertEqual(result["decision"], result["truth"])


if __name__ == "__main__":
    unittest.main()
