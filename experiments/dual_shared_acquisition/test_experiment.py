import itertools
import unittest

import numpy as np

from experiment import ColumnModel, dual_proposal, edges_for, pair_factor, run_dual


class DualAllocationTests(unittest.TestCase):
    def setUp(self):
        patterns = np.array(list(itertools.product((0, 1), repeat=3)))
        self.model = ColumnModel(np.tile(patterns.T, (1, 20)))
        self.edges = edges_for(3, 'star')

    def test_overlap_and_selected_current_outcome_predictability(self):
        observed = np.full((3, 4), -1)
        predicted = self.model.predict(observed)
        q = dual_proposal(observed, predicted, self.edges, np.full(2, 2))
        self.assertAlmostEqual(q.sum(), 1.)
        self.assertTrue(np.all(q > 0))
        first = np.zeros((3, 4), int)
        original = run_dual(first, self.model, self.edges, 19)['trace'][0]
        second = first.copy()
        v, item = divmod(original['cell'], 4)
        second[v, item] = 1
        changed = run_dual(second, self.model, self.edges, 19)['trace'][0]
        self.assertEqual((original['cell'], original['q']), (changed['cell'], changed['q']))
        self.assertNotEqual(original['value'], changed['value'])

    def test_exact_true_null_factor_under_all_small_completions(self):
        observed = np.full((3, 2), -1)
        predicted = self.model.predict(observed)
        q = dual_proposal(observed, predicted, self.edges, np.full(2, 2))
        for a, b in ((0, 1), (1, 0)):
            factors, peak = pair_factor(observed, predicted, q, a, b)
            self.assertLessEqual(peak, 1+1e-12)
            for bits in itertools.product((0, 1), repeat=6):
                truth = np.asarray(bits).reshape(3, 2)
                if truth[a].sum() <= truth[b].sum():
                    actual = np.take_along_axis(factors, truth[:, :, None], axis=2)[:, :, 0]
                    self.assertLessEqual(float((q*actual).sum()), 1+1e-12)

    def test_exact_ties_and_unique_queries(self):
        scores = np.tile([[0, 1, 0, 1]], (3, 1))
        result = run_dual(scores, self.model, self.edges, 19)
        self.assertEqual(result['decisions'], [0, 0])
        self.assertEqual(result['wrong'], 0)
        self.assertEqual(len(set(x['cell'] for x in result['trace'])), result['paid'])


if __name__ == '__main__':
    unittest.main()
