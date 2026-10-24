import unittest

from probe import CELLS, N, audit, coefficients, conditional_audit, draw_distribution


class JointCellProbeTests(unittest.TestCase):
    def test_exhaustive_conditional_audit_and_ambiguous_reference(self):
        result = audit()
        self.assertEqual(result["states"], 2 ** (3 * N) * 2 ** (3 * N))
        self.assertGreater(result["joint_null_states"], 0)
        self.assertEqual(result["same_leaf_worlds"], ((0, 2), (2, 0)))

    def test_reference_score_is_not_required_for_joint_sum(self):
        h = coefficients()
        self.assertTrue(all(h[0, i] == 0 for i in range(N)))
        matrix = {cell: (1. if cell[0] == 2 else 0.) for cell in CELLS}
        p = draw_distribution({}, h)
        self.assertTrue(all(cell[0] != 0 for cell in p))
        mean, _, _ = conditional_audit(matrix, {}, p, h)
        self.assertAlmostEqual(mean, 2.)


if __name__ == "__main__":
    unittest.main()
