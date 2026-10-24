"""Theorem characterization and explicit boundary tests."""
from __future__ import annotations

import unittest

from audit import (audit, component_compatibility, components,
                   direct_compatibility, eligible_panels)


class ContextCompatibilityTests(unittest.TestCase):
    def test_exact_small_graph_enumeration(self):
        record = audit()
        self.assertEqual(record["graphs"], 63)
        self.assertEqual(record["complete_components"], 1)
        self.assertEqual(record["sparse_components"], 2)
        self.assertAlmostEqual(record["context_witness"]["bias"], .15)

    def test_full_panel_graph_unique_uniform_weights(self):
        edges = ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3))
        panels = eligible_panels(4, 3, edges)
        self.assertEqual(len(components(panels, edges)), 1)
        self.assertTrue(direct_compatibility(panels, edges, [3] * len(panels)))
        self.assertFalse(direct_compatibility(panels, edges, [1, 1, 1, 2]))

    def test_disconnected_panels_allow_component_reweighting(self):
        edges = ((0, 1), (4, 5))
        panels = eligible_panels(6, 3, edges)
        groups = components(panels, edges)
        weights = [0] * len(panels)
        for w, group in enumerate(groups, 1):
            for j in group:
                weights[j] = w
        self.assertTrue(direct_compatibility(panels, edges, weights))
        self.assertTrue(component_compatibility(panels, edges, weights))
        weights[groups[0][0]] += 1
        self.assertFalse(direct_compatibility(panels, edges, weights))

    def test_zero_propensity_is_not_a_compatible_target_design(self):
        panels = eligible_panels(4, 3, ((0, 1),))
        with self.assertRaises(ValueError):
            direct_compatibility(panels, ((0, 1),), [1, 0])


if __name__ == "__main__":
    unittest.main()
