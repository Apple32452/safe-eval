"""Tests of the stronger fixed-certificate label-accounting boundary."""
import itertools
import unittest

from audit_async_prefix import (
    asynchronous_labels,
    exhaustive_audit,
    pruned_labels,
    required_labels,
)
from audit_stage23 import check_resolution_schedule


class AsynchronousPrefixBoundary(unittest.TestCase):
    def test_star_matches_existing_pruned_completion(self):
        edges = ((0, 1), (0, 2))
        stops = (3, 1)
        expected = required_labels(3, edges, stops)
        self.assertEqual(len(expected), 7)
        self.assertEqual(pruned_labels(3, edges, stops), expected)
        self.assertEqual(asynchronous_labels(3, edges, stops, (1, 0, 0, 0)), expected)
        for order in itertools.permutations(range(3)):
            self.assertEqual(
                check_resolution_schedule(3, edges, order, stops).pruned_completion,
                len(expected),
            )

    def test_incomplete_or_excess_schedule_is_rejected(self):
        edges = ((0, 1), (0, 2))
        with self.assertRaises(ValueError):
            asynchronous_labels(3, edges, (2, 1), (0, 1))
        with self.assertRaises(ValueError):
            asynchronous_labels(3, edges, (2, 1), (0, 0, 0, 1))

    def test_all_small_asynchronous_interleavings(self):
        report = exhaustive_audit()
        self.assertEqual(report["status"], "passed")
        self.assertGreater(report["asynchronous_schedules"], report["stopping_assignments"])


if __name__ == "__main__":
    unittest.main()
