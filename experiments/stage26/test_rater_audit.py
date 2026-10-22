import sys
from pathlib import Path
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_raters import summarize


class RaterAuditTests(unittest.TestCase):
    def test_same_rater_twice_is_not_two_distinct_raters(self):
        records = {"xx-yy": {"item": {
            "A": [{"annotator": "r1", "score": 90}, {"annotator": "r1", "score": 70}],
            "B": [{"annotator": "r1", "score": 80}, {"annotator": "r2", "score": 80}],
            "C": [{"annotator": "r3", "score": 70}, {"annotator": "r4", "score": 70}],
        }}}
        matrices = {"xx-yy": (np.zeros((3, 1)), np.array(["A", "B", "C"]),
                              np.array(["item"]))}
        rows, total = summarize(records, matrices)
        self.assertEqual(total["ratings"], 6)
        self.assertEqual(total["cells_with_two_ratings"], 3)
        self.assertEqual(total["cells_with_two_raters"], 2)
        self.assertEqual(total["cells_with_same_rater_repeated"], 1)
        self.assertEqual(total["pair_items_shared_rater"], 1)
        self.assertEqual(total["pair_items"], 3)
        self.assertEqual(total["cells_with_score_disagreement"], 1)
        self.assertEqual(total["same_rater_absolute_difference"], 20)
        self.assertEqual(total["pair_first_second_opposite"], 1)
        self.assertEqual(total["pair_mean_tie"], 1)
        self.assertEqual(rows[0]["distinct_raters_per_cell"], {1: 1, 2: 2})


if __name__ == "__main__":
    unittest.main()
