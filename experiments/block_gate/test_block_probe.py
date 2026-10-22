"""Exact one-step design audit and a paired Stage 22 path check."""
import itertools
import unittest

import numpy as np

from block_probe import (RHOS, block_certificate, design, matched_stage22_cost,
                         signals_and_bounds)


class BlockGateInvariants(unittest.TestCase):
    def test_binary_states_conditional_mean_support_and_e_factors(self):
        # Includes arbitrarily revealed masks and a history-adaptive q. All
        # possible block outcomes are enumerated, rather than Monte Carlo tested.
        edges = np.array([(0, 1), (0, 2)], dtype=np.int16)
        checked = 0
        for bits in itertools.product((0., 1.), repeat=6):
            scores = np.asarray(bits).reshape(3, 2)
            for mask in itertools.product((False, True), repeat=6):
                seen = np.asarray(mask).reshape(3, 2)
                active_edges = np.array([not (seen[a].all() and seen[b].all())
                                         for a, b in edges])
                if not active_edges.any():
                    continue
                q = .25 if scores[0, seen[0]].sum() > 0 else .75
                eligible, chance = design(seen, edges, active_edges, q)
                active = np.unique(edges[active_edges].ravel())
                enumerated = []
                for item in eligible:
                    unknown = active[~seen[active, item]]
                    for flags in itertools.product((0, 1), repeat=len(unknown) - 1):
                        bought = [(int(unknown[0]), int(item))]
                        bought.extend((int(v), int(item))
                                      for v, flag in zip(unknown[1:], flags) if flag)
                        probability = (q ** sum(flags) * (1-q) **
                                       (len(flags) - sum(flags)) / len(eligible))
                        enumerated.append((probability,
                                           signals_and_bounds(scores, seen, edges,
                                                              active_edges, chance, bought)))
                self.assertAlmostEqual(sum(p for p, _ in enumerated), 1.)
                for e in np.flatnonzero(active_edges):
                    a, b = edges[e]
                    target = scores[a].sum() - scores[b].sum()
                    terms = [(p, next(value for index, *value in updates if index == e))
                             for p, updates in enumerated]
                    self.assertAlmostEqual(sum(p * x for p, (x, _, _) in terms), target)
                    for p, (x, low, high) in terms:
                        self.assertGreaterEqual(x, low - 1e-12)
                        self.assertLessEqual(x, high + 1e-12)
                        self.assertGreaterEqual(np.min(1 + RHOS * x / max(1., -low)), .2 - 1e-12)
                        self.assertGreaterEqual(np.min(1 - RHOS * x / max(1., high)), .2 - 1e-12)
                    if target <= 0:
                        expected = sum(p * (1 + .8 * x / max(1., -low))
                                       for p, (x, low, _) in terms)
                        self.assertLessEqual(expected, 1 + 1e-12)
                    if target >= 0:
                        expected = sum(p * (1 - .8 * x / max(1., high))
                                       for p, (x, _, high) in terms)
                        self.assertLessEqual(expected, 1 + 1e-12)
                    checked += 1
        self.assertGreater(checked, 1000)

    def test_full_block_matches_stage22_events_on_same_path(self):
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage17"))
        from continuous_engine import directional_paths

        scores = np.array([[1., 0., 1., 1., 0., 1., 0., 1., 1., 0., 1., 1.],
                           [0., 1., 0., 1., 1., 0., 1., 0., 0., 1., 0., 1.]])
        edges = np.array([(0, 1)])
        result = block_certificate(scores, edges, np.random.default_rng(17),
                                   q=1., return_trace=True)
        order = [row["item"] for row in result["trace"]]
        order += [i for i in range(scores.shape[1]) if i not in order]
        diffs = (scores[0, order] - scores[1, order]).reshape(1, 1, -1)
        events, _ = directional_paths(diffs, 2 * len(edges) / .05)
        for t, row in enumerate(result["trace"]):
            self.assertEqual(row["decisions"][0], int(events[0, 0, t]))
            self.assertEqual(len(row["bought"]), 2)
            x = row["updates"][0][1]
            a = sum(diffs[0, 0, :t])
            self.assertAlmostEqual(x, a + (len(order) - t) * diffs[0, 0, t])
        self.assertEqual(result["wrong"], 0)
        stage22 = matched_stage22_cost(scores, edges, order,
                                       np.random.default_rng(9))
        self.assertLessEqual(stage22, result["cost"])
        self.assertLess(result["cost"] - stage22, scores.shape[0])

    def test_duplicate_free_completion_and_ties(self):
        edges = np.array([(0, 1), (0, 2)])
        for scores in (np.ones((3, 8)),
                       np.array([[1.] * 8, [0.] * 8, [1.] * 8])):
            for q in (1., .75, .5):
                result = block_certificate(scores, edges, np.random.default_rng(4),
                                           q=q, return_trace=True)
                cells = [cell for block in result["trace"] for cell in block["bought"]]
                self.assertEqual(len(cells), len(set(cells)))
                self.assertEqual(result["cost"], len(cells))
                self.assertEqual(result["wrong"], 0)
                self.assertLessEqual(result["cost"], scores.size)


if __name__ == "__main__":
    unittest.main()
