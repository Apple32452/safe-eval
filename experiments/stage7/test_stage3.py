"""Deterministic checks for predictable switching and fixed wealth mixtures."""
import unittest
import numpy as np
from safe_eval_v1 import corrected_draws
from safe_eval_v2 import directional_factors, evaluate_uniform_many
from safe_eval_v3 import evaluate_fallbacks, mixture_log_wealth


class FallbackInvariants(unittest.TestCase):
    def test_preserved_component_trajectories(self):
        rng = np.random.default_rng(301)
        h, y = rng.uniform(size=(12, 28)), rng.uniform(size=(3, 28))
        oracle = lambda ix: y[np.arange(3), ix]
        new, diag = evaluate_fallbacks(h, oracle, 3, seed=9)
        for name, settings in [('uniform_raw', dict(prediction_strength=0, cap_fraction=.5, stake_rule='legacy')),
                               ('raw_cap90', dict(prediction_strength=0, cap_fraction=.9, stake_rule='legacy')),
                               ('raw_targeted', dict(prediction_strength=0, cap_fraction=.9, stake_rule='targeted')),
                               ('stage2_trust', dict(prediction_strength=.5, learn_trust=True))]:
            old = evaluate_uniform_many(h, oracle, 3, seed=9, **settings)
            for key in ('lower', 'upper', 'estimate', 'stop', 'stop_lower', 'stop_upper'):
                np.testing.assert_allclose(new[name][key], old[key], atol=1e-12)
            np.testing.assert_array_equal(diag['selected'], old['selected'])
        np.testing.assert_allclose(diag['prediction_strength'], old['prediction_strength'])

    def test_always_raw_gate_is_identical_to_raw_process(self):
        rng = np.random.default_rng(302)
        h, y = rng.uniform(size=(9, 24)), rng.uniform(size=24)
        runs, diag = evaluate_fallbacks(h, lambda ix: y[ix], 4, seed=8, slope_threshold=1e6)
        self.assertTrue(np.all(diag['gate_prediction'] == 0))
        for key in runs['uniform_raw']:
            np.testing.assert_allclose(runs['uniform_raw'][key], runs['predictable_gate'][key], atol=1e-12)

    def test_always_prediction_gate_is_identical_to_prediction_process(self):
        rng = np.random.default_rng(303)
        h, y = rng.uniform(size=(9, 24)), rng.uniform(size=24)
        runs, diag = evaluate_fallbacks(h, lambda ix: y[ix], 4, seed=8,
                                      anchors=0, slope_threshold=-1e6)
        self.assertTrue(np.all(diag['gate_prediction'] == 1))
        for key in runs['stage2_trust']:
            np.testing.assert_allclose(runs['stage2_trust'][key], runs['predictable_gate'][key], atol=1e-12)

    def test_current_outcome_cannot_change_its_own_gate(self):
        rng = np.random.default_rng(304)
        h = rng.uniform(size=(10, 32))
        def make_oracle(late):
            calls = [0]
            def oracle(ix):
                calls[0] += 1
                return np.full(4, .4 if calls[0] <= 16 else late)
            return oracle
        a, da = evaluate_fallbacks(h, make_oracle(.1), 4, seed=6)
        b, db = evaluate_fallbacks(h, make_oracle(.9), 4, seed=6)
        for key in ('gate_prediction', 'gate_slope', 'prediction_strength',
                    'raw_variance', 'prediction_variance'):
            np.testing.assert_allclose(da[key][:17], db[key][:17], atol=1e-12)
        np.testing.assert_array_equal(da['selected'], db['selected'])
        for key in ('lower', 'upper', 'estimate'):
            np.testing.assert_allclose(a['predictable_gate'][key][:16],
                                       b['predictable_gate'][key][:16], atol=1e-12)

    def test_combined_factors_have_unit_conditional_expectation(self):
        rng = np.random.default_rng(305)
        for _ in range(100):
            y, mu = rng.uniform(size=11), rng.uniform(size=11)
            p = np.full(11, 1 / 11)
            rz = corrected_draws(0, np.zeros(11), p, y, 11)
            pz = corrected_draws(0, mu, p, y, 11)
            base = mu.mean()
            lo, hi = base - mu.max(), base + (1 - mu).max()
            true_q = np.array([y.mean()])
            rf = directional_factors(rz, np.zeros(11), np.ones(11), true_q,
                                     np.full(11, rng.uniform(.1, 20)), .5)
            pf = directional_factors(pz, np.full(11, lo), np.full(11, hi), true_q,
                                     np.full(11, rng.uniform(.1, 20)), .9)
            weight = rng.uniform()
            for raw, prediction in zip(rf, pf):
                factor = (1 - weight) * raw + weight * prediction
                self.assertAlmostEqual(float(p @ factor[:, 0]), 1., places=12)

    def test_mixture_log_wealth_reserves_raw_capital(self):
        rng = np.random.default_rng(306)
        raw, pred = rng.uniform(-1000, 1000, (2, 1000))
        mixed = mixture_log_wealth(raw, pred, .75)
        self.assertTrue(np.all(mixed >= raw + np.log(.75) - 1e-12))
        self.assertTrue(np.isfinite(mixed).all())
        np.testing.assert_allclose(mixture_log_wealth(raw, raw, .75), raw, atol=1e-12)

    def test_pathwise_mixture_interval_dominates_reserved_raw_interval(self):
        rng = np.random.default_rng(307)
        h, y = rng.uniform(size=(12, 36)), rng.uniform(size=(8, 36))
        runs, _ = evaluate_fallbacks(h, lambda ix: y[np.arange(8), ix], 8, seed=7)
        self.assertTrue(np.all(runs['mixture75']['lower'] >= runs['raw_reserve75']['lower'] - 1e-12))
        self.assertTrue(np.all(runs['mixture75']['upper'] <= runs['raw_reserve75']['upper'] + 1e-12))

    def test_convex_factors_preserve_monotone_inversion(self):
        rng = np.random.default_rng(308)
        grid = np.linspace(0, 1, 1001)
        for _ in range(40):
            lo = rng.uniform(-2, 0, (2, 4))
            hi = rng.uniform(1, 3, (2, 4))
            z = rng.uniform(lo, hi)
            eta = rng.uniform(.1, 100, (2, 4))
            rf = directional_factors(z[0], lo[0], hi[0], grid, eta[0], .5)
            pf = directional_factors(z[1], lo[1], hi[1], grid, eta[1], .9)
            weight = rng.uniform(size=(4, 1))
            plus, minus = [(1 - weight) * a + weight * b for a, b in zip(rf, pf)]
            self.assertTrue(np.all(np.diff(plus, axis=1) <= 1e-12))
            self.assertTrue(np.all(np.diff(minus, axis=1) >= -1e-12))
            self.assertGreaterEqual(min(plus.min(), minus.min()), .1 - 1e-12)

    def test_unique_queries_exact_final_mean_and_nonempty_precision_stops(self):
        rng = np.random.default_rng(309)
        h = rng.uniform(size=(10, 30))
        for y in [rng.uniform(size=30), np.zeros(30), np.ones(30)]:
            seen = np.zeros((4, 30), dtype=bool)
            def oracle(ix):
                self.assertFalse(seen[np.arange(4), ix].any())
                seen[np.arange(4), ix] = True
                return y[ix]
            runs, _ = evaluate_fallbacks(h, oracle, 4, seed=5)
            self.assertTrue(seen.all())
            for tr in runs.values():
                np.testing.assert_allclose(tr['lower'][-1], y.mean(), atol=1e-12)
                np.testing.assert_allclose(tr['upper'][-1], y.mean(), atol=1e-12)
                widths = tr['stop_upper'] - tr['stop_lower']
                self.assertTrue(np.all((widths >= 0) & (widths <= .1 + 1e-12)))


if __name__ == '__main__':
    unittest.main()
