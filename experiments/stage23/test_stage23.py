import unittest

from audit_stage23 import (
    check_itemwise_lower_bound,
    check_resolution_schedule,
    exhaustive_audit,
)


class SynchronousMinimalityInvariants(unittest.TestCase):
    def test_incident_vertices_are_the_unique_minimum_query_set(self):
        checked = check_itemwise_lower_bound(5, ((0, 1), (0, 4), (2, 3)))
        self.assertEqual(checked, 32)

    def test_final_partial_common_block_is_accounted_exactly(self):
        result = check_resolution_schedule(
            5,
            ((0, 1), (0, 4)),
            (0, 1, 2, 3, 4),
            (1, 1),
        )
        self.assertEqual(result.pruned_completion, 3)
        self.assertEqual(result.common_completion, 5)

    def test_pruning_can_tie_the_common_control(self):
        result = check_resolution_schedule(
            3,
            ((0, 1), (1, 2)),
            (2, 0, 1),
            (2, 2),
        )
        self.assertEqual(result.pruned_completion, result.common_completion)

    def test_malformed_graphs_and_schedules_are_rejected(self):
        with self.assertRaises(ValueError):
            check_itemwise_lower_bound(3, ((1, 0),))
        with self.assertRaises(ValueError):
            check_resolution_schedule(3, ((0, 1),), (0, 0, 2), (1,))
        with self.assertRaises(ValueError):
            check_resolution_schedule(3, ((0, 1),), (0, 1, 2), (0,))

    def test_all_small_graphs_orders_and_resolution_schedules(self):
        report = exhaustive_audit(max_systems=4, max_rounds=3)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["graph_cases"], 71)
        self.assertEqual(report["queried_vertex_subsets"], 1068)
        self.assertEqual(report["resolution_schedule_cases"], 98664)
        self.assertGreater(report["per_edge_dominance_checks"], 0)
        self.assertGreater(report["strict_completion_gains"], 0)


if __name__ == "__main__":
    unittest.main()

