"""Validity and predictability checks for the new acquisition rule."""
import itertools
import unittest

import numpy as np

from experiment import ColumnModel, certificate_proposal, edges_for, pair_factor, run_certificate


class CertificateAcquisitionTests(unittest.TestCase):
    def setUp(self):
        patterns = np.array(list(itertools.product((0, 1), repeat=3)), dtype=int)
        self.model = ColumnModel(np.tile(patterns.T, (1, 16)))
        self.edges = edges_for(3, 'star')

    def test_positive_predictable_probabilities_with_partially_seen_items(self):
        observed = np.full((3, 12), -1, dtype=int)
        observed[1, 3] = 1
        observed[0, 7] = 0
        decision = np.array([2, 2])
        prediction = self.model.predict(observed)
        q = certificate_proposal(observed, prediction, self.edges, decision)
        self.assertAlmostEqual(q.sum(), 1.)
        self.assertTrue(np.all(q[observed < 0] > 0))
        self.assertTrue(np.all(q[observed >= 0] == 0))
        # Change the very first hidden purchased score: its own selection
        # probability and selected identity must stay identical.
        first = np.zeros((3, 4), dtype=int)
        original = run_certificate(first, self.model, self.edges, 43)['trace'][0]
        second = first.copy()
        v, item = divmod(original['cell'], 4)
        second[v, item] = 1
        changed = run_certificate(second, self.model, self.edges, 43)['trace'][0]
        self.assertEqual(original['cell'], changed['cell'])
        self.assertEqual(original['q'], changed['q'])
        self.assertNotEqual(original['value'], changed['value'])

    def test_true_null_expectation_every_small_completion(self):
        observed = np.full((3, 2), -1, dtype=int)
        prediction = self.model.predict(observed)
        q = certificate_proposal(observed, prediction, self.edges, np.array([2, 2]))
        for a, b in ((0, 1), (1, 0)):
            factor, peak = pair_factor(observed, prediction, q, a, b)
            self.assertLessEqual(peak, 1+1e-12)
            for bits in itertools.product((0, 1), repeat=6):
                truth = np.array(bits).reshape(3, 2)
                if truth[a].sum() <= truth[b].sum():
                    actual = np.take_along_axis(factor, truth[:, :, None], axis=2)[:, :, 0]
                    self.assertLessEqual(float(np.sum(q*actual)), 1+1e-12)

    def test_ties_complete_with_unique_paid_cells(self):
        scores = np.tile(np.array([[1, 0, 1, 0]]), (3, 1))
        result = run_certificate(scores, self.model, self.edges, 43)
        self.assertEqual(result['decisions'], [0, 0])
        self.assertEqual(result['wrong'], 0)
        self.assertEqual(result['paid'], len(result['trace']))
        self.assertEqual(result['paid'], len(set(x['cell'] for x in result['trace'])))


if __name__ == '__main__':
    unittest.main()
