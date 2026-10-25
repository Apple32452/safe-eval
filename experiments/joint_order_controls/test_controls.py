import sys
import unittest
from itertools import product
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import controls
from controls import paired_update, rebalance, run_block


class AdditionalControlChecks(unittest.TestCase):
    def test_rebalanced_factor_matches_known_binary_log_optimum(self):
        f, fallback, success = rebalance(np.array([[1.8, .2], [.2, 1.8]]),
                                         np.array([.7, .3]))
        np.testing.assert_allclose(f, [1.4, .6], atol=2e-6)
        self.assertLessEqual(float(np.mean(f)), 1+1e-12)
        self.assertFalse(fallback)
        self.assertTrue(success)

    def test_paired_factors_cover_every_small_remaining_sequence(self):
        for counts in product(range(3), repeat=3):
            for m in (1, 2, 3):
                fit = paired_update(counts, (.2, .8), sum(counts)+m)
                d = counts[2]-counts[0]
                for remaining in product((-1, 0, 1), repeat=m):
                    if d+sum(remaining) <= 0:
                        expectation = np.mean(fit['factor'][np.array(remaining)+1])
                        self.assertLessEqual(expectation, 1+1e-10)

    def test_current_item_cannot_change_its_own_factor_or_active_set(self):
        scores = np.array([[0, 1, 0, 1, 0, 1], [1, 0, 0, 1, 1, 0],
                           [0, 1, 1, 0, 1, 0]])
        changed = scores.copy(); changed[0, 2] ^= 1
        original = paired_update
        records, runs = [], []
        for matrix in (scores, changed):
            calls = []
            def spy(*args):
                answer = original(*args)
                calls.append((args, answer['factor'].copy()))
                return answer
            with patch.object(controls, 'paired_update', side_effect=spy):
                runs.append(run_block(matrix, (.2, .5, .8), list(range(6)),
                                      'star', 'paired_exact_closure'))
            records.append(calls)
        for left, right in zip(runs[0]['trace'][:3], runs[1]['trace'][:3]):
            self.assertEqual(left['item'], right['item'])
            self.assertEqual(left['active'], right['active'])
        # No requested edge can resolve on this fixture's first two items.
        self.assertEqual(len(records[0][:12]), 12)
        for left, right in zip(records[0][:12], records[1][:12]):
            self.assertEqual(left[0], right[0])
            np.testing.assert_array_equal(left[1], right[1])

    def test_retirement_ledger_matches_incident_prefix_footprint(self):
        scores = np.array([[1]*16, [0]*16, [0, 1]*8])
        for method in controls.METHODS[1:]:
            run = run_block(scores, (.8, .2, .5), list(range(16)), 'star', method)
            ledger = {(v, row['item']) for row in run['trace'] for v in row['active']}
            self.assertEqual(run['paid'], len(ledger))
            prefix = [next(i+1 for i, row in enumerate(run['trace'])
                           if row['decisions'][e] != 2) for e in range(2)]
            self.assertEqual(run['paid'], max(prefix)+sum(prefix))
            self.assertTrue(any(len(row['active']) < 3 for row in run['trace']))
            self.assertEqual(run['decisions'], [1, 1])

    def test_exact_ties_exhaust_both_endpoints(self):
        for graph in controls.GRAPHS:
            for method in controls.METHODS[1:]:
                run = run_block(np.zeros((3, 3), int), (.2, .5, .8), [1, 2, 0],
                                graph, method)
                self.assertEqual(run['paid'], 9)
                self.assertEqual(run['decisions'], [0]*len(controls.GRAPHS[graph]))
                self.assertEqual(run['wrong'], 0)


if __name__ == '__main__':
    unittest.main()
