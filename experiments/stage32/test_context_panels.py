"""Meaningful checks of target identity, ranking, propensities and replay."""
import unittest

import numpy as np

from run_context_panels import (METHODS, PANELS, adaptive_g_probability,
                                conditional_expectation, corrected_signal,
                                experiment, one_trajectory, pair_sign, ranking,
                                summarize, target_mean)


class PanelContextInvariants(unittest.TestCase):
    def test_context_reverses_target_and_naive_estimand(self):
        self.assertAlmostEqual(target_mean(), -0.4)
        for q_g, expected_naive in ((0.8, 0.48), (0.9, 0.64)):
            self.assertAlmostEqual(conditional_expectation(q_g, True), target_mean())
            self.assertAlmostEqual(conditional_expectation(q_g, False), expected_naive)
        with self.assertRaises(ValueError):
            conditional_expectation(1., True)

    def test_five_distinct_systems_and_orientation(self):
        for panel in (0, 1):
            for u in (0., 0.09, 0.89, 0.99):
                full = ranking(panel, u)
                self.assertEqual(set(full), set(PANELS[panel]))
                self.assertEqual(len(full), 5)
                self.assertEqual(pair_sign(full), 1 if u < (0.9 if panel == 0 else 0.1) else -1)

    def test_factors_bounded_even_for_rare_panel(self):
        for q_g in (0.8, 0.9):
            for panel in (0, 1):
                for sign in (-1, 1):
                    x, bound = corrected_signal(panel, sign, q_g)
                    self.assertLessEqual(abs(x), bound + 1e-12)
                    self.assertGreater(1 - 0.8 * x / bound, 0)
                    self.assertGreater(1 + 0.8 * x / bound, 0)
        self.assertEqual(adaptive_g_probability(1), 0.9)
        self.assertEqual(adaptive_g_probability(-1), 0.8)

    def test_matched_replay_and_capped_outcomes(self):
        rows = experiment(4, 120)
        self.assertEqual(rows, experiment(4, 120))
        self.assertEqual(len(rows), 4 * len(METHODS))
        summary = summarize(rows, 4)
        for method in METHODS:
            self.assertEqual(sum(summary[method][key] for key in ("wrong", "correct", "abstained")), 4)
        u = np.full(30, 0.5)
        self.assertEqual(one_trajectory(u, u, "adaptive_naive"),
                         one_trajectory(u, u, "adaptive_naive"))
        with self.assertRaises(ValueError):
            one_trajectory(u, np.ones(30), "adaptive_ipw")


if __name__ == "__main__":
    unittest.main()
