"""Compatibility, no-leakage and exact finite-pool checks for the new controls."""
import itertools
import unittest
import numpy as np
from stage8_common import STAGE7, METHODS, MIXTURES, load_data, build_cases, pack_curves, unpack_curves
from stage8_engine import evaluate_matched
from analyze_stage8 import replay_model_free
from reserve_fallback import evaluate_reserved
from safe_eval_v2 import directional_factors
from wmt_experiment import QueryOracle


class MatchedControls(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(81)
        self.history = rng.uniform(0, 1, (5, 18))
        self.outcomes = rng.integers(0, 2, 18).astype(float)

    def test_prediction_and_reserved_paths_match_unchanged_stage7(self):
        datasets, _ = load_data(STAGE7 / 'data')
        cases = build_cases(datasets)
        selected = [next(c for c in cases if c[0]['scenario'] == 'aligned' and c[0]['language_pair'] == pair)
                    for pair in ('en-de', 'he-en', 'zh-en')]
        selected.append(next(c for c in cases if c[0]['scenario'] == 'reversed_history' and c[0]['language_pair'] == 'en-de'))
        for case, history, outcomes in selected:
            args = dict(trials=2, seed=case['raw_seed'])
            original, old_diag = evaluate_reserved(history, QueryOracle(outcomes, 2), **args)
            matched, diag = evaluate_matched(history, QueryOracle(outcomes, 2), **args)
            np.testing.assert_array_equal(diag['selected'], old_diag['selected'])
            np.testing.assert_array_equal(diag['prediction_strength'], old_diag['prediction_strength'])
            for method in ('published_ppr95', 'ppr_reserve75', 'prediction_count_grid', 'reserve_mix75'):
                for field in ('lower', 'upper', 'stop', 'stop_lower', 'stop_upper'):
                    np.testing.assert_array_equal(matched[method][field], original[method][field])

    def test_model_free_outputs_do_not_depend_on_history(self):
        base, ledger = evaluate_matched(self.history, QueryOracle(self.outcomes, 4), 4, seed=8)
        for history in (1 - self.history, self.history[:, ::-1], np.full_like(self.history, .2)):
            result, diag = evaluate_matched(history, QueryOracle(self.outcomes, 4), 4, seed=8)
            np.testing.assert_array_equal(diag['selected'], ledger['selected'])
            np.testing.assert_array_equal(diag['zero_eta'], ledger['zero_eta'])
            for method in ('raw_count_grid', 'raw_reserve75', 'published_ppr95', 'ppr_reserve75'):
                for field in result[method]:
                    np.testing.assert_array_equal(result[method][field], base[method][field])

    def test_current_label_cannot_change_own_prediction_support_or_stake(self):
        _, first = evaluate_matched(self.history, QueryOracle(self.outcomes, 2), 2, seed=9)
        step = 6
        changed = self.outcomes.copy()
        changed[first['selected'][step, 0]] = 1 - changed[first['selected'][step, 0]]
        _, second = evaluate_matched(self.history, QueryOracle(changed, 2), 2, seed=9)
        np.testing.assert_array_equal(first['selected'], second['selected'])
        for field in ('prediction_strength', 'prediction_mu', 'prediction_eta', 'zero_eta', 'prediction_lower', 'prediction_upper'):
            np.testing.assert_array_equal(first[field][:step + 1, 0], second[field][:step + 1, 0])

    def test_one_step_corrected_draws_and_factors_are_conditionally_unbiased(self):
        outcomes = np.array([1., 0., 0., 1., 1., 0.])
        remaining = np.array([2, 3, 4, 5])
        n, observed = len(outcomes), 1.
        truth = outcomes.mean()
        for mu in (np.array([.05, .95, .2, .8]), np.full(4, .5), np.zeros(4)):
            base = (observed + mu.sum()) / n
            z = base + len(remaining) / n * (outcomes[remaining] - mu)
            low = base - len(remaining) / n * mu.max()
            high = base + len(remaining) / n * (1 - mu).max()
            self.assertAlmostEqual(z.mean(), truth, places=14)
            fp, fm = directional_factors(z, np.full(4, low), np.full(4, high), np.array([truth]), np.full(4, 3.), .9)
            self.assertAlmostEqual(fp.mean(), 1., places=14)
            self.assertAlmostEqual(fm.mean(), 1., places=14)
            self.assertGreaterEqual(min(fp.min(), fm.min()), .1 - 1e-12)

    def test_exact_enumerated_coverage_for_model_free_controls(self):
        n = 6
        permutations = np.array(list(itertools.permutations(range(n))), dtype=int).T
        for delta in (.05, .2):
            for bits in itertools.product((0., 1.), repeat=n):
                outcomes = np.array(bits)
                curves, _ = replay_model_free(permutations, outcomes, delta=delta)
                truth = outcomes.mean()
                for method in ('raw_count_grid', 'raw_reserve75'):
                    lower, upper = curves[method]
                    failures = ~((lower <= truth + 1e-12) & (truth <= upper + 1e-12)).all(axis=0)
                    self.assertLessEqual(failures.mean(), delta + 1e-12, (delta, bits, method))

    def test_replay_lossless_paths_unique_queries_and_reserve_bounds(self):
        for outcomes in (self.outcomes, np.zeros(18), np.ones(18)):
            result, diag = evaluate_matched(self.history, QueryOracle(outcomes, 5), 5, seed=17)
            encoded = pack_curves(result, diag)
            curves = unpack_curves(encoded)
            rebuilt, repaired = replay_model_free(diag['selected'], outcomes, 17)
            np.testing.assert_array_equal(repaired, diag['repaired'][0])
            for method in METHODS:
                np.testing.assert_array_equal(curves[method][0], result[method]['lower'])
                np.testing.assert_array_equal(curves[method][1], result[method]['upper'])
                np.testing.assert_array_equal(curves[method][:, -1], np.full((2, 5), outcomes.mean()))
                self.assertTrue(np.all(result[method]['stop_upper'] >= result[method]['stop_lower']))
                self.assertTrue(np.all(result[method]['stop_upper'] - result[method]['stop_lower'] <= .1 + 1e-12))
            for method in ('raw_count_grid', 'raw_reserve75'):
                np.testing.assert_array_equal(rebuilt[method], curves[method])
            for mixture in MIXTURES:
                self.assertTrue(np.all(result[mixture]['stop'] <= result['ppr_reserve75']['stop']))
            corrupted = diag['selected'].copy()
            corrupted[1, 0] = corrupted[0, 0]
            with self.assertRaises(ValueError):
                replay_model_free(corrupted, outcomes, 17)

    def test_fractional_target_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_matched(self.history, lambda _: np.array([.5]), 1)


if __name__ == '__main__':
    unittest.main()
