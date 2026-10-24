"""Exact finite-assignment and input-integrity tests."""
from __future__ import annotations

import itertools
import unittest
from statistics import variance

from exact_test import ALLOCATIONS, analyze_rows, exact_pvalue
from power_plan import plan


def key_and_responses():
    key, responses = [], []
    # The same judge can serve on a second independent document, but each
    # document has four distinct judges and balanced randomized contexts.
    for doc in ("doc-a", "doc-b"):
        for i in range(4):
            task = f"{doc}-{i}"
            slots = ("A", "X", "B", "Y", "Z") if i % 2 else (
                "Y", "B", "Z", "A", "X")
            ranking = [3, 2, 4, 1, 5] if i % 2 else [5, 4, 3, 1, 2]
            key.append({"task_id": task, "item_id": doc,
                        "rater_id": f"judge-{i}",
                        "context": "P1" if i >= 2 else "P0",
                        **{f"slot_{j}": x for j, x in enumerate(slots, 1)}})
            responses.append({"task_id": task, "rater_id": f"judge-{i}",
                              "seconds": "60",
                              **{f"rank_{j}": str(x) for j, x in
                                 enumerate(ranking, 1)}})
    return key, responses


class PanelRandomizationTests(unittest.TestCase):
    def test_known_exact_tails_include_equality(self):
        block = [(-1, False), (-1, False), (1, True), (1, True)]
        self.assertAlmostEqual(exact_pvalue([block])["two_sided_p"], 1 / 3)
        self.assertAlmostEqual(exact_pvalue([block] * 3)["two_sided_p"], 2 / 216)
        self.assertEqual(exact_pvalue([[(0, False), (0, False),
                                         (0, True), (0, True)]])["two_sided_p"], 1)

    def test_exact_null_type_i_for_all_assignments_in_small_blocks(self):
        # The same four fixed potential outcomes are observed in every
        # allocation. This is the complete randomization distribution under
        # the sharp null; exact p-values must be superuniform.
        outcomes = ((-1, 0, 1, 1), (-1, -1, 0, 1))
        pvals = []
        for choices in itertools.product(ALLOCATIONS, repeat=2):
            blocks = [[(y, j in chosen) for j, y in enumerate(values)]
                      for values, chosen in zip(outcomes, choices)]
            pvals.append(exact_pvalue(blocks)["two_sided_p"])
        for alpha in (.05, .1, .2, .5, 1.0):
            self.assertLessEqual(sum(p <= alpha for p in pvals) / 36,
                                 alpha + 1e-12)

    def test_repeated_judges_across_documents_and_panel_positions(self):
        key, responses = key_and_responses()
        result = analyze_rows(key, responses)
        self.assertEqual(result["documents"], 2)
        self.assertEqual(result["total_assignments"], "36")
        self.assertGreaterEqual(result["two_sided_p"], 0)
        self.assertLessEqual(result["two_sided_p"], 1)

    def test_invalid_assignment_and_missing_response_fail(self):
        key, responses = key_and_responses()
        with self.assertRaises(ValueError):
            analyze_rows(key, responses[:-1])
        bad = [dict(x) for x in key]
        bad[1]["rater_id"] = bad[0]["rater_id"]
        with self.assertRaises(ValueError):
            analyze_rows(bad, responses)
        bad = [dict(x) for x in key]
        bad[1]["context"] = "P1"
        with self.assertRaises(ValueError):
            analyze_rows(bad, responses)

    def test_idealized_scale_has_four_judgments_per_document(self):
        result = plan()
        self.assertEqual(result["pilot_tasks"], 160)
        self.assertTrue(.5 < result["approx_min_detectable_signed_effect"] < .53)
        self.assertEqual([x["approx_tasks"] // x["approx_documents"]
                          for x in result["scenarios"]], [4, 4, 4])

    def test_exact_four_judge_randomization_variance_bound(self):
        worst = max(variance(outcomes) for outcomes in
                    itertools.product((-1, 0, 1), repeat=4))
        self.assertAlmostEqual(worst, 4 / 3)


if __name__ == "__main__":
    unittest.main()
