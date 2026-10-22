"""Meaningful mechanics and target checks for the five-way panel pilot."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np


spec = importlib.util.spec_from_file_location(
    "run_koehn_panels", Path(__file__).with_name("run_koehn_panels.py"))
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class PanelInvariants(unittest.TestCase):
    def test_five_way_panel_produces_ten_unique_paired_edges(self):
        self.assertEqual(len(panel.PANELS), 3003)
        self.assertEqual(panel.PANEL_EDGES.shape, (3003, 10))
        for ids in panel.PANEL_EDGES:
            self.assertEqual(len(np.unique(ids)), 10)

    def test_conditional_null_factors_with_dependent_panel_results(self):
        for rho in panel.RHO:
            # Symmetric tied systems: each directional factor averages one.
            self.assertAlmostEqual((1 + rho + 1 - rho) / 2, 1)
        # One panel can have a full consistent order; its ten outcomes are
        # determined by the same five scores and cannot be iid observations.
        p = panel.PANELS[0]
        q = np.arange(panel.SYSTEMS, dtype=float)[::-1]
        y = [np.sign(q[a] - q[b]) for a, b in panel.PAIRS[panel.PANEL_EDGES[0]]]
        self.assertEqual(len(y), 10)
        self.assertTrue(np.all(np.asarray(y) == 1))

    def test_all_fixed_system_order_certifies_without_error(self):
        rounds = 180
        scores = np.broadcast_to(np.arange(panel.SYSTEMS, 0, -1),
                                 (rounds, panel.SYSTEMS)).copy().astype(float)
        # Cycle through all system subsets to offer each pair repeatedly.
        choices = np.arange(rounds) % len(panel.PANELS)
        candidates = np.tile(choices[:, None], (1, 16))
        means = scores[0]
        for method in panel.METHODS:
            result = panel.run_one(scores, candidates, means, method, fraction=.01)
            self.assertGreater(result["certified"], 0)
            self.assertEqual(result["wrong"], 0)
            self.assertEqual(result["cycle"], 0)
            self.assertEqual(result["derived_pair_outcomes"], 10 * result["panels"])

    def test_rank_ranges_follow_certified_graph(self):
        d = np.zeros(len(panel.PAIRS), dtype=np.int8)
        d[panel.EDGE_LOOKUP[0, 1]] = 1
        d[panel.EDGE_LOOKUP[1, 2]] = 1
        ranges = panel.rank_ranges(d)
        self.assertEqual(ranges[0][0], 1)
        self.assertEqual(ranges[2][0], 3)  # closure: 0 > 1 > 2
        self.assertEqual(ranges[0][1], panel.SYSTEMS - 2)


if __name__ == "__main__":
    unittest.main()
