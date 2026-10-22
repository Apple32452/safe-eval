import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_stage27 import exact_audit, summarize
from two_stage import corrected_signal, potential_scores, run_synthetic


class TwoStageTests(unittest.TestCase):
    def test_exact_null_enumeration_and_selection_counterexample(self):
        result = exact_audit()
        self.assertGreater(result["enumerated_null_settings"], 0)
        self.assertEqual(result["expected_corrected_signal"], 0)
        self.assertAlmostEqual(result["naively_selected_pair_mean"], 0.6)

    def test_zero_query_probability_is_refused(self):
        with self.assertRaises(ValueError):
            corrected_signal(1, 0, 0.5, 0, 1)

    def test_unqueried_candidate_cannot_change_signal(self):
        self.assertEqual(corrected_signal(0, 0, 0.3, 0.25, 0),
                         corrected_signal(0, 1, 0.3, 0.25, 0))

    def test_full_pair_and_corrected_paths_complete_or_record_unresolved(self):
        rows = run_synthetic(repeats=2, max_rounds=40)
        self.assertEqual(len(rows), 8)
        for row in rows:
            for key in ("paired", "two_stage"):
                result = row[key]
                self.assertEqual(result["completed"], result["unresolved"] == 0)
                self.assertGreaterEqual(result["cost"], 1)
        self.assertEqual(len(summarize(rows)), 4)
        np.testing.assert_array_equal(potential_scores("tie")[0],
                                      potential_scores("tie")[1])


if __name__ == "__main__":
    unittest.main()
