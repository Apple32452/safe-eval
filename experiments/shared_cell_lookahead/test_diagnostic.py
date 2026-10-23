"""Checks independent of the full nine-score outcome screen."""
import functools
import itertools
import random
import unittest

from diagnostic import (CELLS, EASY, ITEMS, POW3, STAR, Planner,
                        state_info, signs, trajectory)


def brute_completions(state, edges):
    digits = state_info(state)[0]
    unknown = [i for i, x in enumerate(digits) if x == 0]
    outcomes = set()
    for values in itertools.product((0, 1), repeat=len(unknown)):
        full = [x - 1 for x in digits]
        for cell, value in zip(unknown, values):
            full[cell] = value
        totals = [sum(full[v * ITEMS + i] for i in range(ITEMS))
                  for v in range(3)]
        outcomes.add(tuple((totals[a] > totals[b]) - (totals[a] < totals[b])
                           for a, b in edges))
    return outcomes


class LookaheadChecks(unittest.TestCase):
    def test_exact_logical_decisions_against_every_completion(self):
        rng = random.Random(73441)
        for _ in range(120):
            state = sum(rng.randrange(3) * power for power in POW3)
            declared = signs(state, STAR)
            compatible = brute_completions(state, STAR)
            for edge_index, sign in enumerate(declared):
                values = {joint[edge_index] for joint in compatible}
                self.assertEqual(sign is not None, len(values) == 1)
                if sign is not None:
                    self.assertEqual(values, {sign})

    def test_bellman_agrees_with_independent_two_item_recursion(self):
        p = (.75, .5, .25, .6, .4, .5, .2, .3, .7)
        planner = Planner(p, STAR)
        # Last item is initially bought for each system and scores zero.
        initial = tuple(sorted((2, 5, 8)))
        known = tuple((j, 0) for j in initial)

        @functools.lru_cache(maxsize=None)
        def brute(history):
            values = dict(history)
            state = sum((1 + score) * POW3[j] for j, score in history)
            if len(brute_completions(state, STAR)) == 1:
                return 0.
            options = []
            for cell in range(CELLS):
                if cell in values:
                    continue
                low = brute(tuple(sorted((*history, (cell, 0)))))
                high = brute(tuple(sorted((*history, (cell, 1)))))
                options.append(1 + (1 - p[cell]) * low + p[cell] * high)
            return min(options)

        initial_state = sum(POW3[j] for j in initial)
        self.assertAlmostEqual(planner.bellman(initial_state)[0], brute(known),
                               places=12)

    def test_unique_system_item_cost_and_shared_reference_cell(self):
        planner = Planner(EASY, STAR)
        for mask in (0, 273, 511):
            for method in ("lookahead", "greedy", "pruned_blocks", "common_blocks"):
                path = trajectory(mask, planner, method)
                cells = [(v, i) for v, i, _ in path["ledger"]]
                self.assertEqual(path["cost"], len(cells))
                self.assertEqual(len(cells), len(set(cells)))
                self.assertNotIn(None, path["decision"])


if __name__ == "__main__":
    unittest.main()
