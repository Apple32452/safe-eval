"""Independent audit of the saved Stage 28 trajectory table and cost gate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from joint_queries import EDGES, METHODS, SCENARIOS, SEED, populations


def audit_saved(folder):
    folder = Path(folder)
    manifest = json.loads((folder / "SUMMARY.json").read_text())
    ledger_path = folder / "REPLICATES.csv"
    assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == manifest["replicates_sha256"]
    protocol = manifest["protocol"]
    expected_repeats = protocol["repeats"]
    signs = {x["scenario"]: x["population_signs"] for x in manifest["summary"]}
    for scenario in SCENARIOS:
        scores = populations(scenario)
        independently_computed = [int(np.sign(scores[i].mean() - scores[j].mean()))
                                  for i, j in EDGES]
        assert signs[scenario] == independently_computed
    rows = {}
    with ledger_path.open(newline="") as stream:
        for record in csv.DictReader(stream):
            scenario, method = record["scenario"], record["method"]
            repeat = int(record["repeat"])
            assert scenario in SCENARIOS and method in METHODS
            assert 0 <= repeat < expected_repeats
            decisions = [int(record[f"d{i}{j}"]) for i, j in EDGES]
            assert all(x in (-1, 0, 1) for x in decisions)
            completed, wrong = int(record["complete"]), int(record["wrong"])
            unresolved = int(record["unresolved"])
            cost, rounds = int(record["cost"]), int(record["rounds"])
            assert completed == int(all(x != 0 for x in decisions))
            assert unresolved == sum(x == 0 for x in decisions)
            assert wrong == sum(d != 0 and d != truth for d, truth in zip(decisions, signs[scenario]))
            assert 0 < rounds <= protocol["rounds"]
            assert rounds <= cost <= 3 * rounds
            key = (scenario, repeat, method)
            assert key not in rows
            rows[key] = dict(cost=cost, rounds=rounds, complete=completed, wrong=wrong)
    assert len(rows) == len(SCENARIOS) * expected_repeats * len(METHODS)

    saved = {(r["scenario"], r["method"]): r for r in manifest["summary"]}
    assert len(saved) == len(SCENARIOS) * len(METHODS)
    comparisons = []
    for scenario in SCENARIOS:
        for method in METHODS:
            group = [rows[(scenario, i, method)] for i in range(expected_repeats)]
            match = [(rows[(scenario, i, "paired_adaptive")], rows[(scenario, i, method)])
                     for i in range(expected_repeats)
                     if rows[(scenario, i, "paired_adaptive")]["complete"]
                     and rows[(scenario, i, method)]["complete"]]
            r = saved[(scenario, method)]
            assert r["completed"] == sum(x["complete"] for x in group)
            assert r["wrong_runs"] == sum(x["wrong"] > 0 for x in group)
            assert np.isclose(r["mean_cost_stop_or_cap"], np.mean([x["cost"] for x in group]))
            assert np.isclose(r["mean_rounds_stop_or_cap"], np.mean([x["rounds"] for x in group]))
            assert r["jointly_completed_with_paired_adaptive"] == len(match)
            if match:
                assert np.isclose(r["mean_cost_on_jointly_completed"],
                                  np.mean([b["cost"] for a, b in match]))
                assert np.isclose(r["paired_adaptive_cost_on_jointly_completed"],
                                  np.mean([a["cost"] for a, b in match]))
            else:
                assert r["mean_cost_on_jointly_completed"] is None
        if scenario == "tie":
            continue
        for candidate, baseline in (("coupled_fixed", "independent_fixed"),
                                    ("coupled_fixed", "paired_fixed"),
                                    ("coupled_adaptive", "paired_adaptive"),
                                    ("coupled_allocation", "paired_adaptive")):
            differences = np.array([rows[(scenario, i, candidate)]["cost"]
                                    - rows[(scenario, i, baseline)]["cost"]
                                    for i in range(expected_repeats)])
            rng = np.random.default_rng(SEED + 100 * SCENARIOS.index(scenario)
                                        + 10 * METHODS.index(candidate) + METHODS.index(baseline))
            indexes = rng.integers(expected_repeats, size=(5000, expected_repeats))
            low, high = np.quantile(np.mean(differences[indexes], axis=1), (.025, .975))
            comparisons.append(dict(scenario=scenario, candidate=candidate, baseline=baseline,
                                    mean_extra_labels=float(np.mean(differences)),
                                    descriptive_bootstrap_95=[float(low), float(high)]))

    joint_methods = ("coupled_fixed", "coupled_adaptive", "coupled_allocation")
    gate = {}
    for candidate in joint_methods:
        completion_all = all(saved[(s, candidate)]["completed"] >=
                             max(saved[(s, "paired_fixed")]["completed"],
                                 saved[(s, "paired_adaptive")]["completed"])
                             for s in SCENARIOS if s != "tie")
        cheaper_scenarios = [s for s in SCENARIOS if s != "tie" and
                             saved[(s, candidate)]["mean_cost_stop_or_cap"] <
                             min(saved[(s, "paired_fixed")]["mean_cost_stop_or_cap"],
                                 saved[(s, "paired_adaptive")]["mean_cost_stop_or_cap"])]
        gate[candidate] = dict(completion_all=completion_all,
                               cheaper_scenarios=cheaper_scenarios,
                               passed=completion_all and len(cheaper_scenarios) >= 3)
    result = dict(trajectories=len(rows), exact_settings=manifest["exact_audit"]["enumerated_settings"],
                  wrong_declarations=sum(r["wrong"] for r in rows.values()),
                  gate=gate, paired_cost_comparisons=comparisons)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    print(json.dumps(audit_saved(args.input), indent=2))
