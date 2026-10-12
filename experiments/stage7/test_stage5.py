"""Structural validity, compatibility and all-path reserve checks."""
import math
import unittest
import numpy as np
from binary_control import evaluate_binary, log_ppr
from reserve_fallback import (candidate_hull, repair_empty_interval, evaluate_reserved, WEIGHTS)
from safe_eval_v1 import corrected_draws
from safe_eval_v2 import directional_factors
from safe_eval_v3 import evaluate_fallbacks, mixture_log_wealth
from wmt_experiment import QueryOracle


class ReserveInvariants(unittest.TestCase):
    def test_published_raw_process_matches_previous_control(self):
        rng = np.random.default_rng(501); n, paths = 32, 6
        h, y = rng.uniform(size=(7, n)), rng.integers(0, 2, n)
        runs, diag = evaluate_reserved(h, QueryOracle(y, paths), paths, seed=7)
        for name, weight in [('published_ppr95', 1.)] + [(f'ppr_reserve{int(100*w)}', w) for w in WEIGHTS]:
            old = evaluate_binary(QueryOracle(y, paths), n, paths, seed=7, delta=.05 * weight)
            for key in ('lower', 'upper', 'stop', 'stop_lower', 'stop_upper'):
                np.testing.assert_allclose(runs[name][key], old[key], atol=1e-12)
            np.testing.assert_array_equal(diag['selected'], old['selected'])

    def test_legacy_prediction_and_gate_are_preserved(self):
        rng = np.random.default_rng(502); n, paths = 36, 8
        h, y = rng.uniform(size=(8, n)), rng.integers(0, 2, n)
        old, old_diag = evaluate_fallbacks(h, QueryOracle(y, paths), paths, seed=9)
        new, diag = evaluate_reserved(h, QueryOracle(y, paths), paths, seed=9)
        for name, previous in [('legacy_trust201', 'stage2_trust'), ('legacy_gate201', 'predictable_gate')]:
            for key in ('lower', 'upper', 'stop', 'stop_lower', 'stop_upper'):
                np.testing.assert_allclose(new[name][key], old[previous][key], atol=1e-12)
        np.testing.assert_array_equal(diag['selected'], old_diag['selected'])
        np.testing.assert_allclose(diag['prediction_strength'], old_diag['prediction_strength'])
        np.testing.assert_allclose(diag['legacy_gate'], old_diag['gate_prediction'])

    def test_count_hull_contains_disconnected_candidate_sets(self):
        grid = np.arange(11) / 10
        masks = np.zeros((3, 11), dtype=bool)
        masks[0, [1, 4, 8]] = True; masks[1, 5] = True
        lo, hi = candidate_hull(masks, grid)
        np.testing.assert_allclose(lo, [.1, .5, 1.])
        np.testing.assert_allclose(hi, [.8, .5, 0.])
        self.assertTrue(np.all((grid[None, :] >= lo[:, None])[masks]))
        self.assertTrue(np.all((grid[None, :] <= hi[:, None])[masks]))

    def test_empty_repair_preserves_the_reserved_raw_interval(self):
        ml, mu = np.array([.3, .7, 1.]), np.array([.5, .2, 0.])
        rl, ru = np.array([.2, .1, 1.]), np.array([.6, .4, 0.])
        lo, hi, repair = repair_empty_interval(ml, mu, rl, ru)
        np.testing.assert_allclose(lo, [.3, .1, 1.]); np.testing.assert_allclose(hi, [.5, .4, 0.])
        np.testing.assert_array_equal(repair, [False, True, True])
        self.assertTrue(np.all(lo >= rl)); self.assertTrue(np.all(hi <= ru))

    def test_fixed_mixture_reserves_raw_log_capital_even_at_extremes(self):
        raw = np.array([-1000., 0., 500., np.inf])
        pred = np.array([500., -1000., 0., -1000.])
        for weight in WEIGHTS:
            mix = mixture_log_wealth(raw, pred, weight)
            self.assertTrue(np.all(mix >= raw + math.log(weight) - 1e-12))

    def test_ppr_one_step_is_a_supermartingale_including_boundary_states(self):
        # Directly verify conditional expectation using feasible fixed K states.
        for n in (4, 9):
            for t in range(n):
                for total in range(n + 1):
                    for successes in range(max(0, t - (n - total)), min(t, total) + 1):
                        current = math.exp(log_ppr(np.array([successes]), t, n)[0, total])
                        probability = (total - successes) / (n - t)
                        expected = 0.
                        for outcome, chance in ((0, 1 - probability), (1, probability)):
                            if chance:
                                after = math.exp(log_ppr(np.array([successes + outcome]), t + 1, n)[0, total])
                                expected += chance * after
                        self.assertLessEqual(expected, current + 1e-10)

    def test_prediction_and_mixed_next_wealth_have_valid_conditional_expectation(self):
        rng = np.random.default_rng(503)
        for _ in range(40):
            n = 12; count = int(rng.integers(0, 9)); remaining = n - count
            values = rng.integers(0, 2, n); observed = int(values[:count].sum())
            total = int(values.sum()); truth = total / n
            mu = rng.uniform(size=remaining); p = np.full(remaining, 1 / remaining)
            draws = corrected_draws(observed, mu, p, values[count:], n)
            base = (observed + mu.sum()) / n
            lo, hi = base - remaining / n * mu.max(), base + remaining / n * (1 - mu).max()
            fp, fm = directional_factors(draws, np.full(remaining, lo), np.full(remaining, hi),
                                         np.array([truth]), np.full(remaining, 2.), .9)
            previous_plus, previous_minus = 1.7, .4
            expected_prediction = .5 * previous_plus * fp[:, 0].mean() + .5 * previous_minus * fm[:, 0].mean()
            previous_prediction = .5 * (previous_plus + previous_minus)
            self.assertAlmostEqual(expected_prediction, previous_prediction, places=12)
            raw_previous = math.exp(log_ppr(np.array([observed]), count, n)[0, total])
            raw_expected = np.mean([math.exp(log_ppr(np.array([observed + int(y)]), count + 1, n)[0, total]) for y in values[count:]])
            for weight in WEIGHTS:
                self.assertLessEqual(weight * raw_expected + (1 - weight) * expected_prediction,
                                     weight * raw_previous + (1 - weight) * previous_prediction + 1e-10)

    def test_all_path_precision_stop_and_interval_bound(self):
        rng = np.random.default_rng(504); n, paths = 40, 30
        h = rng.uniform(size=(8, n)); y = rng.integers(0, 2, n)
        runs, diag = evaluate_reserved(h, QueryOracle(y, paths), paths, seed=4, delta=.2, epsilon=.1)
        for weight in WEIGHTS:
            suffix = str(int(100 * weight)); mix, raw = runs['reserve_mix' + suffix], runs['ppr_reserve' + suffix]
            self.assertTrue(np.all(mix['stop'] <= raw['stop']))
            self.assertTrue(np.all(mix['lower'] >= raw['lower'] - 1e-12))
            self.assertTrue(np.all(mix['upper'] <= raw['upper'] + 1e-12))
        for run in runs.values():
            self.assertTrue(np.all(run['stop_upper'] >= run['stop_lower']))
            self.assertTrue(np.all(run['stop_upper'] - run['stop_lower'] <= .2 + 1e-12))
            np.testing.assert_allclose(run['lower'][-1], y.mean()); np.testing.assert_allclose(run['upper'][-1], y.mean())

    def test_present_outcome_does_not_change_its_prediction_strength_or_gate(self):
        rng = np.random.default_rng(505); h = rng.uniform(size=(8, 28))
        def oracle(last):
            calls = [0]
            def query(indices):
                calls[0] += 1
                return np.full(4, 0. if calls[0] <= 15 else last)
            return query
        _, a = evaluate_reserved(h, oracle(0.), 4, seed=6)
        _, b = evaluate_reserved(h, oracle(1.), 4, seed=6)
        for name in ('prediction_strength', 'legacy_gate', 'legacy_gate_slope'):
            np.testing.assert_allclose(a[name][:16], b[name][:16], atol=1e-12)
        np.testing.assert_array_equal(a['selected'], b['selected'])

    def test_fractional_target_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_reserved(np.full((4, 20), .5), lambda ix: np.full(len(ix), .5), 3)


if __name__ == '__main__':
    unittest.main()
