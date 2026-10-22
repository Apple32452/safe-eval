"""Replay saved acquisition ledgers and evaluate the frozen development gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from sequential_probe import matched_stage22_cost

SCENARIOS = {"aligned_strong": (.9, .1),
             "aligned_moderate": (.7, .3),
             "shifted_opposite": (.3, .7)}


def audit(results):
    summary = {}
    n = 32
    repeats = len(results["aligned_strong"]["cases"])
    for name, (true_a, true_b) in SCENARIOS.items():
        costs = {key: [] for key in ("1", "0.75", "0.5", "stage22")}
        fallbacks = {key: 0 for key in ("1", "0.75", "0.5")}
        for rep, case in enumerate(results[name]["cases"]):
            rng = np.random.default_rng(20261024 + rep + 100 * len(name))
            scores = (rng.random((2, n)) < np.array([[true_a], [true_b]])).astype(np.int8)
            truth = int(np.sign(scores[0].sum() - scores[1].sum()))
            if int(scores[0].sum() - scores[1].sum()) != case["true_gap"]:
                raise AssertionError("Fixed target gap differs from saved run")
            for q in ("1", "0.75", "0.5"):
                row = case["methods"][q]
                ledger = [(v, i) for i, a, b in row["path"]
                          for v, bought in ((0, a), (1, b)) if bought]
                if len(ledger) != len(set(ledger)) or len(ledger) != row["cost"]:
                    raise AssertionError("Double-bought or mispriced score")
                if row["truth"] != truth or row["decision"] != truth or row["wrong"]:
                    raise AssertionError("Wrong completed fixed-pool sign")
                costs[q].append(row["cost"])
                fallbacks[q] += row["fallbacks"]
            prefix = [i for i, _, _ in case["methods"]["1"]["path"]]
            order = np.array(prefix + [i for i in range(n) if i not in prefix],
                             dtype=np.int32)
            control = matched_stage22_cost(scores, np.array([[0, 1]], dtype=np.int16),
                                           order, np.random.default_rng(55191 + rep))
            if control != case["stage22"]:
                raise AssertionError("Stage 22 matched control changed")
            costs["stage22"].append(control)
        means = {q: float(np.mean(v)) for q, v in costs.items()}
        for q in means:
            if not np.isclose(means[q], results[name]["mean_cost"][q]):
                raise AssertionError("Saved mean does not match cases")
        rng = np.random.default_rng(8844 + len(name))
        paired_intervals = {}
        for q in ("0.75", "0.5"):
            delta = np.asarray(costs[q]) - np.asarray(costs["1"])
            boot = np.mean(delta[rng.integers(0, repeats, (5000, repeats))], axis=1)
            paired_intervals[q] = [float(v) for v in np.quantile(boot, [.025, .975])]
        summary[name] = dict(mean_cost=means, fallbacks=fallbacks,
                             paired_difference_vs_full_ci95=paired_intervals,
                             percent_vs_full={q: 100 * (means[q] / means["1"] - 1)
                                              for q in ("0.75", "0.5")},
                             percent_vs_stage22={q: 100 * (means[q] / means["stage22"] - 1)
                                                 for q in ("0.75", "0.5")})
    gate = {}
    for q in ("0.75", "0.5"):
        gate[q] = (all(summary[s]["percent_vs_full"][q] <= -10 and
                       summary[s]["percent_vs_stage22"][q] <= -10
                       for s in ("aligned_strong", "aligned_moderate")) and
                   summary["shifted_opposite"]["percent_vs_full"][q] <= 10)
    return dict(repeats=repeats, summary=summary, passed=gate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.input.read_text())), indent=2))
