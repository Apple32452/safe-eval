"""Check the inferential step and completed fixed-pool accounting."""
import itertools
import unittest

import numpy as np

from arm_probe import Arm, arm_certificate


class ArmGateInvariants(unittest.TestCase):
    def test_one_step_supermartingale_for_every_binary_small_pool(self):
        # Enumerate all conditional draw sets after a known prefix; compare
        # the actual implemented wealth change to its conditional expectation.
        n = 4
        for bits in itertools.product((0., 1.), repeat=n):
            pop = np.asarray(bits)
            mean = pop.mean()
            for count in range(n):
                for prefix in itertools.permutations(range(n), count):
                    arm = Arm(n, alpha=.05, systems=1, order=np.arange(n))
                    for i in prefix:
                        arm.update(pop[i])
                        # Each mean grid is nested: rejection of a harder
                        # null implies rejection of every easier one.
                        self.assertTrue(np.all(arm.plus[:-1] >= arm.plus[1:] - 1e-12))
                        self.assertTrue(np.all(arm.minus[:-1] <= arm.minus[1:] + 1e-12))
                    rest = [i for i in range(n) if i not in prefix]
                    for grid_index in (0, 25, 50, 75, 100):
                        threshold = grid_index / 100
                        before_plus = arm.plus[grid_index].copy()
                        before_minus = arm.minus[grid_index].copy()
                        plus_factors, minus_factors = [], []
                        for i in rest:
                            candidate = Arm(n, alpha=.05, systems=1,
                                            order=np.arange(n))
                            candidate.count = arm.count
                            candidate.total = arm.total
                            candidate.plus = arm.plus.copy()
                            candidate.minus = arm.minus.copy()
                            candidate.update(pop[i])
                            after_plus = candidate.plus[grid_index]
                            after_minus = candidate.minus[grid_index]
                            if np.isfinite(before_plus).all():
                                plus_factors.append(np.exp(after_plus - before_plus))
                            if np.isfinite(before_minus).all():
                                minus_factors.append(np.exp(after_minus - before_minus))
                        # Deterministic rejection at an impossible null can
                        # have infinite wealth; do not use it as a bet.
                        if mean <= threshold and np.isfinite(before_plus).all():
                            self.assertTrue(np.all(np.mean(plus_factors, axis=0)
                                                   <= 1 + 1e-12))
                        if mean >= threshold and np.isfinite(before_minus).all():
                            self.assertTrue(np.all(np.mean(minus_factors, axis=0)
                                                   <= 1 + 1e-12))

    def test_full_pool_tie_and_opposite_signs(self):
        for scores in (np.ones((2, 8)),
                       np.array([[1.] * 8, [0.] * 8]),
                       np.array([[0.] * 8, [1.] * 8])):
            cost, wrong = arm_certificate(scores, np.array([(0, 1)]),
                                          np.random.default_rng(20261022))
            self.assertEqual(wrong, 0)
            self.assertGreater(cost, 0)
            self.assertLessEqual(cost, scores.size)
            if np.all(scores == 1):
                self.assertEqual(cost, scores.size)


if __name__ == "__main__":
    unittest.main()
