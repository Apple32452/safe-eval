"""Algebraic and sequential invariants for the frozen panel-aware screen."""
import importlib.util
import math
import unittest
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "panel_aware_screen", Path(__file__).with_name("run_screen.py"))
screen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(screen)


class PanelAwareInvariants(unittest.TestCase):
    def test_corrected_signals_have_target_expectation_with_bad_predictions(self):
        for probabilities in ((.90, .10), (.98, .55), (.50, .95), (.12, .72)):
            target = sum(screen.PI[s] * (2 * probabilities[s] - 1)
                         for s in (0, 1))
            for q, m in (((.15, .85), (.90, -.90)),
                         ((.68, .32), (-.70, .80)),
                         ((.50, .50), (0., 0.))):
                for method in screen.METHODS[1:]:
                    self.assertAlmostEqual(
                        screen.conditional_mean(method, q, m, probabilities),
                        target, places=12)
            self.assertAlmostEqual(
                screen.conditional_mean("target_random", screen.PI, (0., 0.),
                                        probabilities), target, places=12)
        with self.assertRaises(ValueError):
            screen.signal_and_bounds("target_random", 0, 1, (.2, .8), (0., 0.))

    def test_predictable_bounds_and_null_factor_expectations(self):
        for q, m in (((.15, .85), (.90, -.90)),
                     ((.68, .32), (-.70, .80)),
                     ((.50, .50), (0., 0.))):
            for method in screen.METHODS[1:]:
                outcomes = [screen.signal_and_bounds(method, s, y, q, m)
                            for s in (0, 1) for y in (-1, 1)]
                for x, low, high in outcomes:
                    self.assertLessEqual(low, x)
                    self.assertLessEqual(x, high)
                    self.assertGreaterEqual(
                        1 - max(screen.RHOS) * x / max(1., high), .2 - 1e-12)
                    self.assertGreaterEqual(
                        1 + max(screen.RHOS) * x / max(1., -low), .2 - 1e-12)
                # Both directional nulls hold at a tie, even if m is wrong.
                p = (.9, .1)
                mean = screen.conditional_mean(method, q, m, p)
                self.assertAlmostEqual(mean, 0.)
                for rho in screen.RHOS:
                    lower, upper = outcomes[0][1:]
                    positive_factor = 1 + rho * mean / max(1., -lower)
                    negative_factor = 1 - rho * mean / max(1., upper)
                    self.assertAlmostEqual(positive_factor, 1.)
                    self.assertAlmostEqual(negative_factor, 1.)

    def test_positive_reserve_and_paid_target_pilot(self):
        for counts, sums, duration in (((20, 0), (20, 0), (1, 3)),
                                       ((0, 30), (0, -30), (3, 1)),
                                       ((100, 100), (0, 100), (1, 1))):
            q = screen.proposal(counts, sums, duration)
            self.assertAlmostEqual(sum(q), 1.)
            self.assertTrue(all(q[s] >= .3 * screen.PI[s] for s in (0, 1)))
        panels = np.full(screen.PILOT, .49)
        outcomes = np.full(screen.PILOT, .99)
        for method in screen.METHODS:
            row = screen.one_trajectory(panels, outcomes, method,
                                        (.5, .95), (1, 3))
            self.assertEqual(row["tasks"], screen.PILOT)
            self.assertEqual(row["p0_tasks"], screen.PILOT)
            self.assertEqual(row["duration"], screen.PILOT)
            self.assertEqual(row["correct"] + row["wrong"] +
                             row["abstained"], 1)

    def test_matched_latent_stream_reproducible_and_ledger_consistent(self):
        rng = np.random.default_rng(screen.seed("unequal_variance", 7))
        panels, judgments = rng.random((2, 200))
        for method in screen.METHODS:
            first = screen.one_trajectory(panels, judgments, method,
                                          (.5, .95), (1, 3))
            second = screen.one_trajectory(panels, judgments, method,
                                           (.5, .95), (1, 3))
            self.assertEqual(first, second)
            self.assertGreaterEqual(first["duration"], first["tasks"])
            self.assertEqual(first["duration"],
                             first["p0_tasks"] +
                             3 * (first["tasks"] - first["p0_tasks"]))
            self.assertFalse(first["contradiction"] and first["decision"])


if __name__ == "__main__":
    unittest.main()
