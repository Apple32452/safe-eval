"""Identity and independent-replay checks for the frozen oracle diagnostic."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit import audit
from run_probe import K, evaluate, proxy, run


class PanelOracleChecks(unittest.TestCase):
    def test_duration_rate_reparameterization(self):
        q = np.array([.07, .11, .17, .19, .22, .24])
        cost = np.array([1., 2., 3., 2., 1., 4.])
        coefficients = np.arange(1, 16 * K + 1, dtype=float).reshape(16, K) / 31.
        r = q / (q @ cost)
        self.assertAlmostEqual(float(r @ cost), 1.)
        self.assertAlmostEqual(proxy(q, coefficients, cost),
                               float(np.max(coefficients @ (1. / r))))

    def test_shifted_ledger_feasibility_and_control_dominance(self):
        row = evaluate("context_and_cost", 0)
        q = np.asarray(row["q"]["oracle"])
        self.assertAlmostEqual(q.sum(), 1.)
        self.assertGreaterEqual(q.min(), .2 / K - 1e-9)
        self.assertGreater(row["feasible_starts"], 0)
        self.assertLessEqual(row["proxy"]["oracle"],
                             min(row["proxy"]["all_pair"],
                                 row["proxy"]["uniform"]) * (1 + 1e-7))

    def test_independent_replay_rejects_modified_proxy(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "experiment"
            run(output, repeats=1)
            self.assertEqual(audit(output)["cases"], 3)
            rows_file = output / "rows.json"
            rows = json.loads(rows_file.read_text())
            rows[0]["proxy"]["oracle"] *= 1.01
            rows_file.write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError, "Incorrect proxy"):
                audit(output)


if __name__ == "__main__":
    unittest.main()
