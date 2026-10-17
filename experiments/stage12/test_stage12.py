"""Checks of null budgets, independent assignment enumeration and edge cases."""
from fractions import Fraction as F
import unittest

from assignment_boost import (capped_factors, centered_boost, centered_factors,
                              naive_plugin_counterexample, worst_expectation)
from audit_stage12 import enumerated_expectations


class AssignmentBudgetChecks(unittest.TestCase):
    def test_top_k_matches_enumeration_for_general_factor_tables(self):
        tables = [((0, 2), (2, 0), (1, 3), (3, 1)),
                  ((F(1, 4), F(3, 2)), (1, 1), (2, F(1, 4))),
                  ((1, 0),)]
        for table in tables:
            for k in range(len(table) + 1):
                for b in (F(1), F(5, 4), F(4)):
                    for cap in (F(3, 2), F(3)):
                        with self.subTest(table=table, k=k, b=b, cap=cap):
                            brute = enumerated_expectations(
                                capped_factors(table, k, b, cap), k)
                            self.assertEqual(max(brute),
                                             worst_expectation(table, k, b, cap))

    def test_both_stake_signs_and_ties_choose_largest_predictions(self):
        p = (F(1, 10), F(9, 10), F(1, 2), F(9, 10), F(0), F(1))
        for k in range(len(p) + 1):
            for theta in (F(-1, 2), F(0), F(1, 2)):
                table = centered_factors(p, k, theta)
                self.assertTrue(all(x == 1 for x in enumerated_expectations(table, k)))
                for b in (F(1), F(2), F(8)):
                    capped = capped_factors(table, k, b, F(3, 2))
                    ones = set(sorted(range(len(p)), key=lambda i: p[i], reverse=True)[:k])
                    selected = sum((capped[i][int(i in ones)]
                                    for i in range(len(p))), F(0)) / len(p)
                    self.assertEqual(selected, max(enumerated_expectations(capped, k)))

    def test_plugin_probability_law_is_not_a_valid_null_budget(self):
        example = naive_plugin_counterexample()
        self.assertEqual(example["working_mean"], 1)
        self.assertEqual(example["true_mean"], F(185, 181))
        self.assertEqual(example["robust_multiplier"], 1)

    def test_boost_has_strict_improvement_when_clipping_frees_budget(self):
        p = (F(0), F(1))
        theta = F(1)
        # k=0 has factors 3/2 and 1/2; a smaller cap releases budget.
        cap = F(5, 4)
        table = centered_factors(p, 0, theta)
        boost = centered_boost(p, 0, theta, cap)
        self.assertEqual(boost.multiplier, F(3, 2))
        self.assertTrue(boost.finite_maximum)
        self.assertEqual(worst_expectation(table, 0, boost.multiplier, cap), 1)
        self.assertGreater(worst_expectation(table, 0, boost.multiplier + F(1, 100), cap), 1)

    def test_zero_factors_allow_saturated_limit_without_finite_maximum(self):
        # k=1 and theta=2 give feasible factors [0,2] for either assignment.
        p, theta, cap = (F(1, 2), F(1, 2)), F(2), F(3, 2)
        table = centered_factors(p, 1, theta)
        boost = centered_boost(p, 1, theta, cap)
        self.assertFalse(boost.finite_maximum)
        self.assertEqual(worst_expectation(table, 1, boost.multiplier, cap), F(3, 4))
        self.assertEqual(worst_expectation(table, 1, boost.multiplier * 100, cap), F(3, 4))

    def test_reject_invalid_counts_factors_and_inexact_inputs(self):
        for k in (True, F(1, 2), -1, 3):
            with self.assertRaises(ValueError):
                centered_factors((0, 1), k, F(1, 2))
        with self.assertRaises(TypeError):
            centered_factors((0.1, 0.9), 1, 1)
        with self.assertRaises(ValueError):
            centered_factors((0, 1), 2, 3)
        with self.assertRaises(ValueError):
            centered_boost((F(1, 2),), 0, 1, 1)


if __name__ == "__main__":
    unittest.main()
