"""Check the conditional fixed-population claim with partial cached cells."""
import itertools
import unittest

import numpy as np

from sequential_probe import Design, certificate, factor


def completions(seen, known, sign):
    n = seen.shape[1]
    for bits in itertools.product((0, 1), repeat=2 * n):
        full = np.array(bits, dtype=np.int8).reshape(2, n)
        if np.array_equal(full[seen], known[seen]) and sign * (
            full[0].sum() - full[1].sum()) <= 0:
            yield full


class SequentialExactChecks(unittest.TestCase):
    def test_every_compatible_null_after_cached_purchases(self):
        n = 3
        histories = [
            ([], []),
            ([(0, 0)], [1]),
            ([(1, 0)], [0]),
            ([(0, 0), (1, 0)], [1, 0]),
            ([(0, 0), (1, 1), (0, 2)], [0, 1, 1]),
        ]
        for observed, values in histories:
            seen = np.zeros((2, n), dtype=bool)
            known = np.zeros((2, n), dtype=np.int8)
            for (v, i), value in zip(observed, values):
                seen[v, i], known[v, i] = True, value
            for q in (.5, 1):
                design = Design(seen, known, q, .8, .2)
                self.assertAlmostEqual(design.alt.sum(), 1)
                for sign in (-1, 1):
                    feasible = list(completions(seen, known, sign))
                    if not feasible:
                        continue
                    factors, fallback = factor(design, sign)
                    worst, witness = design.worst_null(factors, sign)
                    brute = max(design.row(full) @ factors for full in feasible)
                    self.assertAlmostEqual(worst, brute, places=8)
                    self.assertLessEqual(worst, 1 + 1e-9)
                    self.assertTrue(any(np.array_equal(witness, full)
                                        for full in feasible))
                    self.assertEqual(isinstance(fallback, bool), True)

    def test_unique_purchases_and_full_pool_sign(self):
        scores = np.array([[1, 1, 1, 0, 1, 1, 1, 0],
                           [0, 0, 1, 0, 0, 0, 1, 0]], dtype=np.int8)
        for q in (.5, 1):
            result = certificate(scores, .8, .2, q, seed=7)
            seen = set()
            for i, buy_a, buy_b in result["path"]:
                for v, bought in ((0, buy_a), (1, buy_b)):
                    if bought:
                        self.assertNotIn((v, i), seen)
                        seen.add((v, i))
            self.assertEqual(result["cost"], len(seen))
            self.assertEqual(result["decision"], result["truth"])


if __name__ == "__main__":
    unittest.main()
