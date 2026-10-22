"""Independently aggregate saved Stage 30 costs and replay ledger endpoints."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from run_star_gate import EDGES, METHODS, SCENARIOS, ledger, population, run_one


def analyze(directory):
    directory = Path(directory)
    with (directory / "replicates.csv").open(newline="") as stream:
        raw = list(csv.DictReader(stream))
    saved = json.loads((directory / "SUMMARY.json").read_text())
    repeats = saved["repeats"]
    if len(raw) != repeats * len(SCENARIOS) * len(METHODS):
        raise AssertionError("Missing or duplicated method trajectories")
    results = {}
    for row in raw:
        key = (row["scenario"], int(row["repeat"]), row["method"])
        if key in results or key[0] not in SCENARIOS or key[2] not in METHODS or not 0 <= key[1] < repeats:
            raise AssertionError("Invalid or duplicated trajectory key")
        values = {name: int(row[name]) for name in
                  ("cost", "rounds", "correct", "wrong", "unresolved", "queried")}
        values["complete"] = row["complete"] == "True"
        if row["complete"] not in ("True", "False") or values["cost"] < 0:
            raise AssertionError("Invalid cost or completion flag")
        if values["correct"] + values["wrong"] + values["unresolved"] != EDGES:
            raise AssertionError("Every edge needs one state")
        if values["complete"] != (values["unresolved"] == 0):
            raise AssertionError("Completion contradicts unresolved edges")
        if values["cost"] != values["rounds"] + values["queried"]:
            raise AssertionError("Reference and candidate cost mismatch")
        results[key] = values
    # The tie control reaches the original cap. Recreate the full ledger: a
    # shortened RNG call would change later item/rater and coin streams.
    original_cap = max(values["rounds"] for values in results.values())
    for scenario in SCENARIOS:
        for repeat in (0, repeats - 1):
            item, rater, coins = ledger(scenario, repeat, original_cap)
            scores = population(scenario)
            for method in METHODS:
                replay = run_one(scores, item, rater, coins, method)
                if replay != results[scenario, repeat, method]:
                    raise AssertionError("Ledger replay mismatch: " + repr((scenario, repeat, method)))
    grouped = defaultdict(dict)
    audit = {}
    for scenario in SCENARIOS:
        for method in METHODS:
            rows = [results[scenario, i, method] for i in range(repeats)]
            mean_cost = float(np.mean([r["cost"] for r in rows]))
            completed = sum(r["complete"] for r in rows)
            wrong = sum(r["wrong"] for r in rows)
            mean_correct = float(np.mean([r["correct"] for r in rows]))
            mean_unresolved = float(np.mean([r["unresolved"] for r in rows]))
            reported = next(x for x in saved["scenarios"] if x["scenario"] == scenario)["methods"][method]
            expected = dict(completed=completed, wrong=wrong, mean_cost=mean_cost,
                            mean_correct=mean_correct, mean_unresolved=mean_unresolved)
            if expected != reported:
                raise AssertionError("Summary disagrees with saved trajectories")
            grouped[scenario][method] = rows
        paired = np.array([x["cost"] for x in grouped[scenario]["paired"]], dtype=float)
        measures = {}
        for method in METHODS[1:]:
            alternative = np.array([x["cost"] for x in grouped[scenario][method]], dtype=float)
            descriptive = []
            if scenario != "tie":
                rng = np.random.default_rng(20261023 + SCENARIOS.index(scenario) * 2 + METHODS.index(method))
                for _ in range(2000):
                    indices = rng.integers(repeats, size=repeats)
                    descriptive.append(100 * (1 - alternative[indices].mean() / paired[indices].mean()))
            measures[method] = dict(
                percent_mean_saving=float(100 * (1 - alternative.mean() / paired.mean())),
                cheaper_ledgers=int(np.sum(alternative < paired)),
                descriptive_bootstrap_percent_interval=(list(np.percentile(descriptive, [2.5, 97.5]))
                                                        if descriptive else None))
        audit[scenario] = measures
    gate = [x["cost_gate_passed"] for x in saved["scenarios"]]
    recomputed = []
    for scenario in SCENARIOS:
        p = grouped[scenario]["paired"]
        pass_here = False
        if scenario != "tie" and all(x["complete"] for x in p):
            p_cost = np.mean([x["cost"] for x in p])
            pass_here = any(all(x["complete"] for x in grouped[scenario][method]) and
                            sum(x["wrong"] for x in grouped[scenario][method]) <= sum(x["wrong"] for x in p) and
                            np.mean([x["cost"] for x in grouped[scenario][method]]) <= .9 * p_cost
                            for method in METHODS[1:])
        recomputed.append(pass_here)
    if gate != recomputed or saved["overall_gate_passed"] != (sum(recomputed) >= 3):
        raise AssertionError("Predeclared cost gate mismatch")
    return dict(status="passed", checked_trajectories=len(results),
                replayed=2 * len(SCENARIOS) * len(METHODS),
                method_comparisons=audit, overall_gate_passed=saved["overall_gate_passed"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    report = analyze(args.input)
    (Path(args.input) / "ANALYSIS.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
