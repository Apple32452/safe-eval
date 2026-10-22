"""Exhaustively check predictable selection and centered finite-pool bets."""
import itertools
import unittest

import numpy as np

from predictive_probe import POLICIES, RHOS, certificate, design, step_signals


class PredictiveBlockInvariants(unittest.TestCase):
    def test_conditional_target_bounds_and_supermartingale(self):
        edges = np.array([(0, 1), (0, 2)])
        m = np.array([[.2, .8], [.4, .6], [.7, .3]])
        checks = 0
        for bits in itertools.product((0., 1.), repeat=6):
            scores = np.asarray(bits).reshape(3, 2)
            for mask in itertools.product((False, True), repeat=6):
                seen = np.asarray(mask).reshape(3, 2)
                unresolved = np.array([not (seen[a].all() and seen[b].all())
                                       for a, b in edges])
                if not unresolved.any():
                    continue
                observed = np.where(seen, scores, 0.)
                for policy in POLICIES:
                    eligible, item_prob, q, chance, designated = design(
                        seen, observed, m, edges, unresolved, policy)
                    active = np.unique(edges[unresolved].ravel())
                    outcomes = []
                    for item, p in zip(eligible, item_prob):
                        unknown = active[~seen[active, item]]
                        other = [int(v) for v in unknown if v != designated[int(item)]]
                        for flags in itertools.product((False, True), repeat=len(other)):
                            bought = [(designated[int(item)], int(item))]
                            bought.extend((v, int(item)) for v, flag in zip(other, flags) if flag)
                            mass = p * np.prod([q[v] if flag else 1-q[v]
                                                for v, flag in zip(other, flags)])
                            acquired = observed.copy()
                            for v, i in bought:
                                acquired[v, i] = scores[v, i]
                            updates = step_signals(seen, observed, acquired, m, edges,
                                                   unresolved, chance, bought)
                            outcomes.append((mass, updates))
                    self.assertAlmostEqual(sum(prob for prob, _ in outcomes), 1.)
                    for e in np.flatnonzero(unresolved):
                        a, b = edges[e]
                        total = scores[a].sum() - scores[b].sum()
                        terms = [(p, next(value for idx, *value in updates if idx == e))
                                 for p, updates in outcomes]
                        self.assertAlmostEqual(sum(p*x for p, (x, _, _) in terms), total)
                        for p, (x, low, high) in terms:
                            self.assertGreaterEqual(x + 1e-10, low)
                            self.assertLessEqual(x - 1e-10, high)
                            self.assertGreaterEqual(np.min(1+RHOS*x/max(1.,-low)), .2-1e-10)
                            self.assertGreaterEqual(np.min(1-RHOS*x/max(1.,high)), .2-1e-10)
                        if total <= 0:
                            self.assertLessEqual(sum(p*(1+.8*x/max(1.,-low))
                                                     for p,(x,low,_) in terms), 1+1e-10)
                        if total >= 0:
                            self.assertLessEqual(sum(p*(1-.8*x/max(1.,high))
                                                     for p,(x,_,high) in terms), 1+1e-10)
                        checks += 1
        self.assertGreater(checks, 1000)

    def test_current_unpurchased_outcome_cannot_change_design(self):
        m = np.array([[.3, .7, .5], [.6, .4, .5], [.2, .8, .5]])
        edges = np.array([(0, 1), (0, 2)])
        seen = np.array([[True, False, False], [False, False, False],
                         [False, False, False]])
        a = np.zeros_like(m)
        a[0, 0] = 1.
        b = a.copy()
        b[~seen] = 1.
        for policy in POLICIES:
            first = design(seen, np.where(seen, a, 0.), m, edges,
                           np.array([True, True]), policy)
            second = design(seen, np.where(seen, b, 0.), m, edges,
                            np.array([True, True]), policy)
            for i in (0, 1, 2, 3):
                np.testing.assert_allclose(first[i], second[i])
            self.assertEqual(first[4], second[4])

    def test_complete_ties_and_unique_purchases(self):
        edges = np.array([(0, 1), (0, 2)])
        for scores in (np.ones((3, 8)),
                       np.array([[1.]*8, [0.]*8, [1.]*8])):
            predictions = np.tile(np.linspace(.05, .95, 8), (3, 1))
            for policy in POLICIES:
                result = certificate(scores, predictions, edges,
                                     np.random.default_rng(28), policy,
                                     return_trace=True)
                cells = [cell for step in result["trace"] for cell in step["bought"]]
                self.assertEqual(result["wrong"], 0)
                self.assertEqual(len(cells), len(set(cells)))
                self.assertEqual(result["cost"], len(cells))
                self.assertLessEqual(result["cost"], scores.size)


if __name__ == "__main__":
    unittest.main()
