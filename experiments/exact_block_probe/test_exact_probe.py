"""Exhaustive checks for the small partial-block calculation."""
import unittest

import numpy as np

from exact_probe import instance, run


class ExactBlockChecks(unittest.TestCase):
    def test_null_rows_are_conditional_expectations_for_fixed_matrices(self):
        n, q = 3, .2
        events, nulls, rows, alternative = instance(n, q, .85, .15)
        self.assertAlmostEqual(alternative.sum(), 1)
        self.assertEqual(len(nulls), 42)
        for j, scores in enumerate(nulls):
            self.assertLessEqual(scores[0].sum(), scores[1].sum())
            for k, (i, a, b) in enumerate(events):
                expected = (q if b != -1 else 1 - q) / n
                expected *= int(scores[0, i] == a and
                                (b == -1 or scores[1, i] == b))
                self.assertAlmostEqual(rows[j, k], expected)

    def test_exact_factors_satisfy_every_fixed_null_and_better_than_linear(self):
        result = run(n=4, q=.5, pa=.95, pb=.05)
        self.assertLessEqual(result["exact_max_null"], 1 + 1e-8)
        self.assertGreater(result["exact_growth"], result["ht_growth"])
        self.assertGreater(result["exact_growth_per_score"], .305)

    def test_full_blocks_match_optimized_linear_factor_in_symmetric_case(self):
        result = run(n=4, q=1, pa=.85, pb=.15)
        self.assertTrue(np.isclose(result["exact_growth"], result["ht_growth"],
                                   atol=1e-8))


if __name__ == "__main__":
    unittest.main()
