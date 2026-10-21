from __future__ import annotations

from fractions import Fraction
import itertools
import math
import unittest

import numpy as np

from paired_engine import (Q, P, CAP, MAX_N, METHODS, raw_evidence, binomial_table,
                           factor_integers, update_capital, features, PairOracle,
                           evaluate, decisions)
from paired_reference import brute_raw, rational_factors, raw_at_modes
from stage13_common import exclude_pair, ledger_for


class PairedConclusionInvariants(unittest.TestCase):
    def test_composite_null_optimization_matches_full_integer_enumeration(self):
        for n in range(2, 17):
            counts = np.array([(a, b, t - a - b) for t in range(n + 1)
                               for a in range(t + 1) for b in range(t - a + 1)])
            for t in range(n + 1):
                block = counts[counts.sum(axis=1) == t]
                actual = raw_evidence(n, *block.T)
                expected = np.array([brute_raw(n, *map(int, c), Q, CAP) for c in block]).T
                np.testing.assert_array_equal(actual, expected)
                for j, c in enumerate(block):
                    a, b, z = map(int, c)
                    self.assertEqual(raw_at_modes(n, a, b, z, Q, CAP), actual[0, j])

    def test_integer_factors_and_updates_match_fractions_and_overflow_bounds(self):
        self.assertLess(CAP * (392 * P * MAX_N), 2**63)
        rng = np.random.default_rng(13131)
        for n in (3, 24, 154, 589, 820):
            for _ in range(60):
                lower = int(rng.integers(-3 * P * n, 1))
                upper = int(rng.integers(0, 3 * P * n + 1))
                z = int(rng.integers(lower, upper + 1))
                numerator, denominator = factor_integers(np.array([z]), np.array([lower]), np.array([upper]), n)
                expected = rational_factors(z, lower, upper, n, P)
                old = rng.integers(0, CAP + 1, size=(2, 8, 1), dtype=np.int64)
                actual = update_capital(old, np.array([z]), np.array([lower]), np.array([upper]), n)
                for direction in range(2):
                    for expert in range(8):
                        f = Fraction(int(numerator[direction, expert, 0]), int(denominator[direction, expert, 0]))
                        self.assertEqual(f, expected[direction][expert])
                        self.assertGreaterEqual(f, Fraction(1, 2))
                        self.assertEqual(int(actual[direction, expert, 0]),
                                         min(CAP, int(int(old[direction, expert, 0]) * f)))

    def test_arbitrary_historical_predictions_preserve_exact_conditional_budgets(self):
        rng = np.random.default_rng(13132)
        for n in range(2, 11):
            for _ in range(40):
                population = rng.integers(-1, 2, n)
                r = int(rng.integers(1, n + 1))
                remaining = population[-r:]
                prediction = rng.integers(-P, P + 1, r)
                center = int(P * population[:-r].sum() + prediction.sum())
                zs = center + r * (P * remaining - prediction)
                low = center + r * (-P - int(prediction.max()))
                high = center + r * (P - int(prediction.min()))
                self.assertEqual(Fraction(int(zs.sum()), r * P * n), Fraction(int(population.sum()), n))
                for direction in (0, 1):
                    if (population.sum() <= 0 if direction == 0 else population.sum() >= 0):
                        factors = [rational_factors(z, low, high, n, P)[direction] for z in zs]
                        for expert in range(8):
                            self.assertLessEqual(sum(f[expert] for f in factors) / r, 1)

    def test_every_small_ternary_path_controls_wrong_early_decisions(self):
        rng = np.random.default_rng(13133)
        for n in range(2, 8):
            strings = np.array(list(itertools.product((-1, 0, 1), repeat=n)), dtype=int)
            count_a = (strings == 1).sum(axis=1)
            count_b = (strings == -1).sum(axis=1)
            history = rng.integers(0, 2, size=(5, n))
            histories = [history, history[:, ::-1], 1 - history]
            for a in range(n + 1):
                for b in range(n - a + 1):
                    paths = strings[(count_a == a) & (count_b == b)]
                    population = np.array([1] * a + [-1] * b + [0] * (n - a - b))
                    ledger = np.empty(paths.T.shape, dtype=int)
                    indices = {value: np.flatnonzero(population == value) for value in (-1, 0, 1)}
                    for j, path in enumerate(paths):
                        positions = {value: iter(indices[value]) for value in indices}
                        ledger[:, j] = [next(positions[value]) for value in path]
                    labels = np.stack([population == 1, population == -1]).astype(int)
                    trace = evaluate(histories, PairOracle(labels, len(paths)), ledger)
                    result = decisions(trace, population, thresholds=np.array([10 * Q, 40 * Q]))
                    truth = int(np.sign(a - b))
                    for level, error in enumerate((Fraction(1, 5), Fraction(1, 20))):
                        for method in range(len(METHODS)):
                            wrong = int(np.sum(result['direction'][method, level] != truth))
                            self.assertLessEqual(Fraction(wrong, len(paths)), error,
                                                 (n, a, b, method, level, wrong))

    def test_both_targets_excluded_and_current_outcomes_cannot_choose_their_predictions(self):
        rng = np.random.default_rng(13134)
        scores = rng.integers(0, 2, size=(8, 18))
        names = np.array(list('abcdefgh'))
        historical, background = exclude_pair(scores, names, 1, 5)
        changed = scores.copy()
        changed[[1, 5]] = 1 - changed[[1, 5]]
        historical2, background2 = exclude_pair(changed, names, 1, 5)
        np.testing.assert_array_equal(historical, historical2)
        np.testing.assert_array_equal(background, background2)
        for x, y in zip(features(historical), features(historical2)):
            np.testing.assert_array_equal(x, y)
        ledger = np.arange(18)[:, None]
        original = scores[[1, 5]]
        modified = original.copy()
        modified[:, 7:] = 1 - modified[:, 7:]
        histories = [historical, historical[:, ::-1], 1 - historical]
        first = evaluate(histories, PairOracle(original, 1), ledger)
        second = evaluate(histories, PairOracle(modified, 1), ledger)
        np.testing.assert_array_equal(first['states'][:, :, :8], second['states'][:, :, :8])
        np.testing.assert_array_equal(first['bets'][:, :, :7], second['bets'][:, :, :7])
        np.testing.assert_array_equal(first['raw'][:, :7], second['raw'][:, :7])

    def test_exact_ties_full_budget_and_invalid_oracles_or_ledgers(self):
        rng = np.random.default_rng(13135)
        n, repeats = 22, 4
        history = rng.integers(0, 2, size=(5, n))
        histories = [history, history[:, ::-1], 1 - history]
        y = rng.integers(0, 2, n)
        ledger = ledger_for(n, repeats, 13136)
        trace = evaluate(histories, PairOracle(np.stack([y, y]), repeats), ledger)
        decision = decisions(trace, y - y)
        self.assertTrue(np.all(decision['stop'] == n))
        self.assertTrue(np.all(decision['direction'] == 0))
        for invalid in (np.zeros_like(ledger), ledger.astype(float)):
            with self.assertRaises(ValueError):
                evaluate(histories, PairOracle(np.stack([y, y]), repeats), invalid)
        with self.assertRaises(ValueError):
            evaluate(histories, lambda index: np.full((repeats, 2), .5), ledger)
        oracle = PairOracle(np.stack([y, y]), repeats)
        oracle(ledger[0])
        with self.assertRaises(ValueError):
            oracle(ledger[0])


if __name__ == '__main__':
    unittest.main()
