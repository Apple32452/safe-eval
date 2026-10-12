"""Exact finite-pool verification for the supplemental published PPR control."""
import itertools
import math
import unittest
import numpy as np
from binary_control import evaluate_binary, log_ppr, ppr_interval
from wmt_experiment import QueryOracle
from safe_eval_v3 import evaluate_fallbacks


class BinaryControlInvariants(unittest.TestCase):
    def test_ratio_matches_prior_over_shifted_beta_binomial_posterior(self):
        for n, t, s in ((12, 3, 1), (25, 8, 4), (10, 10, 6)):
            ratio = log_ppr(np.array([s]), t, n)[0]
            for k in range(s, n - (t - s) + 1):
                remaining, unobserved_successes = n - t, k - s
                # Beta-binomial posterior over K-s, with parameters (1+s,1+t-s).
                log_comb = math.lgamma(remaining + 1) - math.lgamma(unobserved_successes + 1) - math.lgamma(remaining - unobserved_successes + 1)
                a, b = 1 + s, 1 + t - s
                log_post = (log_comb + math.lgamma(unobserved_successes + a)
                    + math.lgamma(remaining - unobserved_successes + b) - math.lgamma(remaining + a + b)
                    - math.lgamma(a) - math.lgamma(b) + math.lgamma(a + b))
                self.assertAlmostEqual(ratio[k], -math.log(n + 1) - log_post, places=11)

    def test_exact_enumerated_anytime_coverage_for_small_pool(self):
        n, delta = 8, .2
        for total_successes in range(n + 1):
            paths = list(itertools.combinations(range(n), total_successes))
            binary = np.zeros((len(paths), n), dtype=int)
            for j, positions in enumerate(paths):
                binary[j, list(positions)] = 1
            counts = np.cumsum(binary, axis=1)
            failed = np.zeros(len(paths), dtype=bool)
            for t in range(1, n + 1):
                lo, hi = ppr_interval(counts[:, t - 1], t, n, delta)
                failed |= (lo > total_successes / n) | (hi < total_successes / n)
            self.assertLessEqual(float(failed.mean()), delta + 1e-12)

    def test_unique_paired_queries_full_mean_and_nonempty_stops(self):
        rng = np.random.default_rng(420)
        history = rng.uniform(size=(6, 32)); binary = rng.integers(0, 2, 32)
        run = evaluate_binary(QueryOracle(binary, 5), 32, 5, seed=9)
        other, diag = evaluate_fallbacks(history, QueryOracle(binary, 5), 5, seed=9)
        np.testing.assert_array_equal(run['selected'], diag['selected'])
        np.testing.assert_allclose(run['lower'][-1], binary.mean())
        np.testing.assert_allclose(run['upper'][-1], binary.mean())
        self.assertTrue(np.all(run['stop_upper'] >= run['stop_lower']))
        self.assertTrue(np.all(run['stop_upper'] - run['stop_lower'] <= .1 + 1e-12))

    def test_fractional_outcome_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_binary(QueryOracle(np.full(8, .5), 2), 8, 2, seed=1)


if __name__ == '__main__':
    unittest.main()
