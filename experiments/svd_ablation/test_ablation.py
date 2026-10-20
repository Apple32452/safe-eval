import unittest
from fractions import Fraction

import numpy as np

from ablation import evaluate_arm, load_engine, reference_features
import stage9_engine
from certify_stage9 import pointwise_intervals
from wmt_experiment import QueryOracle


class AblationTests(unittest.TestCase):
    def setUp(self):
        self.h = np.random.default_rng(4).integers(0, 2, (5, 12)).astype(float)
        self.y = np.array([0, 1] * 6)
        self.raw = pointwise_intervals(12, 20)
        self.cal = self.raw.copy()

    def test_feature_removal_keeps_means_and_intercept(self):
        a, x, _ = reference_features(self.h)
        b, z, _ = reference_features(self.h, rank=0)
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(z, np.ones((12, 1)))
        np.testing.assert_array_equal(x[:, :1], z)
        self.assertEqual(x.shape, (12, 4))

    def test_isolated_engine_and_canonical_equivalence(self):
        original = stage9_engine.reference_features
        load_engine(False)
        self.assertIs(stage9_engine.reference_features, original)
        args = (self.h, QueryOracle(self.y, 3), 3, 7, self.raw, self.cal, Fraction(1, 100))
        canonical = stage9_engine.evaluate(*args)
        actual, _ = evaluate_arm(self.h, self.y, 3, 7, self.raw, self.cal, Fraction(1, 100), True)
        for key in canonical:
            np.testing.assert_array_equal(actual[key], canonical[key])

    def test_pairing_metrics_and_valid_stops(self):
        results = [evaluate_arm(self.h, self.y, 3, 7, self.raw, self.cal,
                               Fraction(1, 100), flag) for flag in (True, False)]
        np.testing.assert_array_equal(results[0][0]['selected'], results[1][0]['selected'])
        for flag, (trace, metrics) in zip((True, False), results):
            residuals = []
            def hook(t, indices, state):
                residuals.append(self.y[indices] - state['mu'][np.arange(3), indices])
            load_engine(flag)(self.h, QueryOracle(self.y, 3), 3, 7, self.raw,
                              self.cal, Fraction(1, 100), prequery_hook=hook)
            r = np.array(residuals)
            np.testing.assert_allclose(metrics['mse'], np.mean(r*r, axis=0))
            np.testing.assert_allclose(metrics['residual_variance'],
                                       np.mean(r*r, axis=0)-np.mean(r, axis=0)**2, atol=1e-15)
            for ledger in trace['selected'].T:
                np.testing.assert_array_equal(np.sort(ledger), np.arange(12))
            from stage8_common import decisions
            decisions(trace['counts'][3]/12, self.y.mean())

    def test_first_prediction_precedes_target_labels(self):
        for flag in (True, False):
            predictions = []
            for target in (self.y, 1-self.y):
                first = []
                def hook(t, indices, state):
                    if t == 1:
                        first.append(state['mu'])
                load_engine(flag)(self.h, QueryOracle(target, 3), 3, 7, self.raw,
                                  self.cal, Fraction(1, 100), prequery_hook=hook)
                predictions.append(first[0])
            np.testing.assert_array_equal(*predictions)
            np.testing.assert_allclose(predictions[0],
                np.broadcast_to(.5+.5*(self.h.mean(axis=0)-.5), (3, 12)))

    def test_pruning_exactly_matches_canonical_curves_and_metrics(self):
        for flag in (True, False):
            for alpha in (Fraction(1, 100), Fraction(1, 2), Fraction(0)):
                a, ma = evaluate_arm(self.h, self.y, 3, 7, self.raw, self.cal, alpha, flag)
                b, mb = evaluate_arm(self.h, self.y, 3, 7, self.raw, self.cal, alpha, flag, pruned=True)
                np.testing.assert_array_equal(a['counts'][3], b['prediction_counts'])
                np.testing.assert_array_equal(a['repaired'][2], b['prediction_repaired'])
                np.testing.assert_array_equal(a['selected'], b['selected'])
                for key in ma:
                    np.testing.assert_array_equal(ma[key], mb[key])

    def test_pruning_exactly_matches_real_pool_paths(self):
        from stage8_common import verify_protocol, build_cases
        from certify_stage9 import load_certificate
        from ablation import ROOT
        _, datasets = verify_protocol()
        cases = build_cases(datasets)
        for language in ('en-de', 'he-en', 'zh-en'):
            case, h, y = next(c for c in cases if c[0]['scenario'] == 'aligned' and c[0]['language_pair'] == language)
            cert, raw, cal = load_certificate(ROOT.parent/'stage9/certificates_reference', case['n'], verify_runtime=False)
            alpha = Fraction(cert['prediction_error_numerator'], cert['prediction_error_denominator'])
            for flag in (True, False):
                a, ma = evaluate_arm(h, y, 2, case['raw_seed'], raw, cal, alpha, flag)
                b, mb = evaluate_arm(h, y, 2, case['raw_seed'], raw, cal, alpha, flag, pruned=True)
                np.testing.assert_array_equal(a['counts'][3], b['prediction_counts'])
                np.testing.assert_array_equal(a['repaired'][2], b['prediction_repaired'])
                np.testing.assert_array_equal(a['selected'], b['selected'])
                for key in ma:
                    np.testing.assert_array_equal(ma[key], mb[key])


if __name__ == '__main__':
    unittest.main()
