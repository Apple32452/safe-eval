import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_star_gate import bounds, ledger, population, run_one, RHOS


class ProspectiveStarTests(unittest.TestCase):
    def test_exact_coin_expectation_and_pre_draw_bounds(self):
        q = .75
        for m0 in (.1, .5, .9):
            for m1 in (.1, .5, .9):
                prediction = [m0, m1]
                negative, positive = bounds(prediction, q)
                for a in (0, 1):
                    for b in (0, 1):
                        off = a - prediction[a]
                        on = off - (b - prediction[a]) / q
                        self.assertAlmostEqual((1 - q) * off + q * on, a - b)
                        self.assertLessEqual(max(off, on), positive + 1e-12)
                        self.assertGreaterEqual(min(off, on), -negative - 1e-12)
                        for direction, c in ((1, negative), (-1, positive)):
                            for rho in RHOS:
                                self.assertGreaterEqual(1 + rho * direction * off / c, 0)
                                self.assertGreaterEqual(1 + rho * direction * on / c, 0)

    def test_full_acquisition_accounting_and_tie(self):
        score = population("tie")
        item, rater, coins = ledger("tie", 0, 4)
        paired = run_one(score, item, rater, coins, "paired", audit=True)
        self.assertEqual(paired["cost"], 18 * paired["rounds"])
        self.assertEqual(paired["wrong"], 0)
        self.assertEqual(paired["truth"][-1], 0)
        self.assertEqual(paired["decisions"][-1], 0)

    def test_prefix_nopeek_query_coin(self):
        score = population("shared_easy")
        item, rater, coins = ledger("shared_easy", 0, 5)
        original = run_one(score, item, rater, coins, "partial")
        score2 = score.copy()
        # Change only a future item/rater cell never on this five-step ledger.
        missing = next((i, j) for i in range(64) for j in range(8)
                       if not any((item == i) & (rater == j)))
        score2[1, missing[0], missing[1]] ^= 1
        changed = run_one(score2, item, rater, coins, "partial")
        for key in ("cost", "rounds", "queried"):
            self.assertEqual(original[key], changed[key])

    def test_completed_rounds_and_hidden_candidate_labels(self):
        score = population("shared_easy")
        item, rater, coins = ledger("shared_easy", 0, 2000)
        paired = run_one(score, item, rater, coins, "paired")
        self.assertTrue(paired["complete"])
        self.assertEqual(paired["cost"], paired["rounds"] + paired["queried"])
        # If no candidate is selected, changing every candidate outcome may
        # change the audited truth but cannot change the acquired evidence.
        no_candidate = np.ones_like(coins)
        unseen = run_one(score, item[:4], rater[:4], no_candidate[:4], "partial", audit=True)
        modified = score.copy()
        modified[1:] = 1 - modified[1:]
        changed = run_one(modified, item[:4], rater[:4], no_candidate[:4], "partial", audit=True)
        self.assertEqual(unseen["decisions"], changed["decisions"])
        self.assertEqual(unseen["cost"], changed["cost"])


if __name__ == "__main__":
    unittest.main()
