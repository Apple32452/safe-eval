import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_stage22 import (METHODS, circulant_edges, simulate_graph, star_edges,
                         task_graphs)


def fixture():
    scores = np.array([
        [.9, .8, .7, .6, .5],
        [.7, .6, .5, .4, .3],
        [.5, .4, .3, .2, .1],
        [.3, .2, .1, .0, .2],
        [.1, .2, .0, .1, .0],
    ])
    names = np.array(["e", "a", "d", "b", "c"])
    path = np.arange(scores.shape[1], dtype=np.int32)
    priority = np.arange(scores.size).reshape(scores.shape[1], scores.shape[0]).T
    return scores, names, path, priority


def event_paths(scores, pairs, path, crossing):
    truth = np.sign(
        scores[pairs[:, 0]].sum(axis=1) - scores[pairs[:, 1]].sum(axis=1)
    ).astype(np.int8)
    events = np.full((len(pairs), scores.shape[1]), 2, dtype=np.int8)
    for index, time in enumerate(crossing):
        events[index, time:] = truth[index]
    return np.tile(path, (len(pairs), 1)), events, truth


class GraphPruningInvariants(unittest.TestCase):
    def test_star_suite_uses_every_reference_without_duplicate_edges(self):
        _, names, _, _ = fixture()
        tasks = task_graphs(names, include_diagnostics=False)
        self.assertEqual([task["reference"] for task in tasks], list(range(5)))
        for task in tasks:
            edges = task["edges"]
            self.assertEqual(len(edges), 4)
            self.assertEqual(len({tuple(edge) for edge in edges.tolist()}), 4)
            self.assertTrue(all(task["reference"] in edge for edge in edges))

    def test_circulant_graphs_are_name_ordered_and_unique(self):
        _, names, _, _ = fixture()
        first = circulant_edges(names, (1,))
        second = circulant_edges(names.copy(), (1,))
        np.testing.assert_array_equal(first, second)
        self.assertEqual(len(first), len(names))
        self.assertEqual(len({tuple(edge) for edge in first.tolist()}), len(first))

    def test_final_decisions_are_exact_and_labels_unique(self):
        scores, _, path, priority = fixture()
        pairs = star_edges(len(scores), 0)
        paths, events, truth = event_paths(scores, pairs, path, [0, 1, 3, 4])
        for method in METHODS:
            result = simulate_graph(
                scores, pairs, paths, events, priority, method,
                fractions=(.25, .5, .75)
            )
            np.testing.assert_array_equal(result["decision"], truth)
            self.assertEqual(len(result["acquired"]), len(set(result["acquired"])))
            self.assertTrue(np.all(result["resolution_cost"] > 0))

    def test_per_edge_pathwise_dominance_for_all_small_crossings(self):
        scores, _, path, priority = fixture()
        pairs = np.asarray([(0, 1), (0, 2), (2, 3)], dtype=np.int16)
        for crossing in itertools.product(range(3), repeat=len(pairs)):
            paths, events, _ = event_paths(scores, pairs, path, crossing)
            fractions = tuple(i / scores.size for i in range(1, scores.size + 1))
            common = simulate_graph(
                scores, pairs, paths, events, priority, "star_common",
                fractions=fractions,
            )
            pruned = simulate_graph(
                scores, pairs, paths, events, priority, "star_pruned",
                fractions=fractions,
            )
            self.assertTrue(np.all(
                pruned["resolution_cost"] <= common["resolution_cost"]
            ))
            self.assertLessEqual(pruned["completion_cost"], common["completion_cost"])

    def test_active_set_is_committed_before_current_item_outcomes(self):
        scores, _, path, priority = fixture()
        pairs = np.asarray([(0, 1), (0, 2)], dtype=np.int16)
        paths, events, _ = event_paths(scores, pairs, path, [0, 0])
        result = simulate_graph(
            scores, pairs, paths, events, priority, "star_pruned", fractions=(.2,)
        )
        self.assertEqual(result["acquired"], [(0, 0), (1, 0), (2, 0)])
        self.assertNotIn((3, 0), result["acquired"])
        self.assertNotIn((4, 0), result["acquired"])

    def test_unrevealed_event_suffix_cannot_change_acquired_prefix(self):
        scores, _, path, priority = fixture()
        pairs = np.asarray([(0, 1), (0, 2), (2, 3)], dtype=np.int16)
        paths, events, _ = event_paths(scores, pairs, path, [2, 3, 4])
        original = simulate_graph(
            scores, pairs, paths, events, priority, "star_pruned", fractions=(.12,)
        )
        changed = events.copy()
        changed[:, 2:-1] = 2
        altered = simulate_graph(
            scores, pairs, paths, changed, priority, "star_pruned", fractions=(.12,)
        )
        self.assertEqual(original["acquired"][:3], altered["acquired"][:3])

    def test_noncommon_paths_and_duplicate_edges_are_rejected(self):
        scores, _, path, priority = fixture()
        pairs = np.asarray([(0, 1), (0, 2)], dtype=np.int16)
        paths, events, _ = event_paths(scores, pairs, path, [2, 3])
        paths[1] = paths[1, ::-1]
        with self.assertRaises(ValueError):
            simulate_graph(scores, pairs, paths, events, priority, "star_pruned")
        duplicate = np.asarray([(0, 1), (0, 1)], dtype=np.int16)
        duplicated_paths = np.tile(path, (2, 1))
        with self.assertRaises(ValueError):
            simulate_graph(
                scores, duplicate, duplicated_paths, events, priority, "star_pruned"
            )


if __name__ == "__main__":
    unittest.main()
