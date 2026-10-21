import unittest

import numpy as np

from shared_pilot import (METHODS, make_paths, precommit_permutations,
                          simulate)


class SharedPilotInvariants(unittest.TestCase):
    def setUp(self):
        self.scores = np.array([[1, 1, 0, 1, 0, 1],
                                [0, 1, 0, 0, 1, 0],
                                [1, 0, 1, 1, 1, 0],
                                [0, 0, 0, 1, 0, 0]], dtype=float)
        self.names = np.array(['A', 'B', 'C', 'D'])

    def test_shared_labels_are_unique_and_full_budget_is_exact(self):
        pairs, perm = precommit_permutations(self.names, 6, 'synthetic', 3)
        events, evidence = make_paths(self.scores, pairs, perm)
        priority = np.arange(len(pairs))[::-1]
        for rep in range(3):
            for method in METHODS:
                snapshots, acquired, cursor, decisions = simulate(
                    self.scores, pairs, perm[:, rep], events[:, rep],
                    evidence[:, rep], method, fractions=(.25, .5, .75, 1.0),
                    priority=priority)
                self.assertEqual(len(acquired), len(set(acquired)))
                self.assertLessEqual(len(acquired), self.scores.size)
                for snap in snapshots:
                    self.assertEqual(snap['correct'] + snap['wrong'] +
                                     snap['unresolved'], len(pairs))
                    self.assertEqual(snap['wrong'], 0)
                self.assertEqual(snapshots[-1]['correct'], len(pairs))
                self.assertEqual(snapshots[-1]['unresolved'], 0)
                expected = np.sign(self.scores[pairs[:, 0]].sum(axis=1) -
                                   self.scores[pairs[:, 1]].sum(axis=1))
                np.testing.assert_array_equal(decisions, expected)

    def test_unseen_outcomes_cannot_change_a_pair_prefix(self):
        pairs, perm = precommit_permutations(self.names, 6, 'synthetic', 1)
        first = int(perm[0, 0, 0])
        changed = self.scores.copy()
        changed[pairs[0, 0], (first + 1) % 6] = 1 - changed[pairs[0, 0], (first + 1) % 6]
        before, wealth_before = make_paths(self.scores, pairs, perm)
        after, wealth_after = make_paths(changed, pairs, perm)
        self.assertEqual(before[0, 0, 0], after[0, 0, 0])
        self.assertEqual(wealth_before[0, 0, 0], wealth_after[0, 0, 0])

    def test_precommitted_orders_repeat_independently_of_policy(self):
        pairs, perm = precommit_permutations(self.names, 6, 'synthetic', 2)
        other_pairs, other = precommit_permutations(self.names, 6, 'synthetic', 2)
        np.testing.assert_array_equal(pairs, other_pairs)
        np.testing.assert_array_equal(perm, other)

    def test_unrevealed_labels_cannot_change_scheduling(self):
        pairs, perm = precommit_permutations(self.names, 6, 'synthetic', 1)
        paths, evidence = make_paths(self.scores, pairs, perm)
        for method in METHODS:
            original = simulate(self.scores, pairs, perm[:, 0], paths[:, 0],
                                evidence[:, 0], method, fractions=(.25,),
                                priority=np.arange(len(pairs))[::-1])
            unseen = next((s, i) for s in range(4) for i in range(6)
                          if (s, i) not in original[1])
            modified = self.scores.copy()
            modified[unseen] = 1 - modified[unseen]
            new_paths, new_evidence = make_paths(modified, pairs, perm)
            changed = simulate(modified, pairs, perm[:, 0], new_paths[:, 0],
                               new_evidence[:, 0], method, fractions=(.25,),
                               priority=np.arange(len(pairs))[::-1])
            self.assertEqual(original[1], changed[1])
            np.testing.assert_array_equal(original[2], changed[2])
            np.testing.assert_array_equal(original[3], changed[3])


if __name__ == '__main__':
    unittest.main()
