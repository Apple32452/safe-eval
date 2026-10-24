"""Independently replay saved paths and summarize paired uncertainty."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
METHODS = ("target_random", "adaptive_ipw", "adaptive_augmented")
SCENARIOS = {
    "unequal_variance": ((.50, .95), (1, 1)),
    "unequal_duration": ((.80, .80), (1, 3)),
    "mixed_variance": ((.98, .55), (1, 1)),
    "homogeneous": ((.80, .80), (1, 1)),
    "opposed_tie": ((.90, .10), (1, 1)),
}
BET = (.10, .25, .50, .80)
FIELDS = ("tasks", "duration", "decision", "truth", "correct", "wrong",
          "abstained", "contradiction", "p0_tasks")


def replay(scenario, repeat, method, cap):
    probabilities, costs = SCENARIOS[scenario]
    token = f"20261024|{scenario}|{repeat}".encode()
    generator = np.random.default_rng(
        int.from_bytes(hashlib.sha256(token).digest()[:8], "little"))
    selector, response = generator.random((2, cap))
    seen = [0, 0]
    signed = [0, 0]
    wealth = [[1.] * 4, [1.] * 4]
    spent = 0
    side = 0
    contradiction = 0
    for index in range(cap):
        mean = [signed[s] / (seen[s] + 4) for s in range(2)]
        if method == "target_random" or index < 20:
            q = [.5, .5]
        else:
            weights = [.5 * math.sqrt(max(.05, 1 - mean[s] ** 2)) /
                       math.sqrt(costs[s]) for s in range(2)]
            q = [.15 + .7 * w / sum(weights) for w in weights]
        s = int(selector[index] >= q[0])
        y = 1 if response[index] < probabilities[s] else -1
        if method == "target_random":
            x, lo, hi = y, -1., 1.
        elif method == "adaptive_ipw":
            x = .5 * y / q[s]
            hi = max(.5 / qs for qs in q)
            lo = -hi
        else:
            baseline = (mean[0] + mean[1]) / 2
            x = baseline + .5 * (y - mean[s]) / q[s]
            lo = min(baseline + .5 * (-1 - mean[k]) / q[k]
                     for k in range(2))
            hi = max(baseline + .5 * (1 - mean[k]) / q[k]
                     for k in range(2))
        seen[s] += 1
        signed[s] += y
        spent += costs[s]
        for j, r in enumerate(BET):
            wealth[0][j] *= 1 + r * x / max(1., -lo)
            wealth[1][j] *= 1 - r * x / max(1., hi)
        # The full prespecified pilot is purchased before any declaration.
        if index >= 19:
            positive = sum(wealth[0]) / 4 >= 40
            negative = sum(wealth[1]) / 4 >= 40
            if positive or negative:
                contradiction = int(positive and negative)
                side = 0 if contradiction else (1 if positive else -1)
                break
    truth = 0 if scenario == "opposed_tie" else 1
    return dict(tasks=index + 1, duration=spent, decision=side, truth=truth,
                correct=int(side == truth and side != 0),
                wrong=int(side != truth and side != 0),
                abstained=int(side == 0), contradiction=contradiction,
                p0_tasks=seen[0])


def audit(directory):
    directory = Path(directory)
    meta = json.loads((directory / "metadata.json").read_text())
    protocol_hash = hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()
    if (meta["protocol_sha256"] != protocol_hash or meta["master"] != 20261024
            or meta["repeats"] != 100 or meta["cap"] != 2000
            or meta["pilot"] != 20 or meta["alpha"] != .05
            or tuple(meta["pi"]) != (.5, .5)
            or tuple(meta["rhos"]) != BET
            or {k: (tuple(v[0]), tuple(v[1])) for k, v in
                meta["scenarios"].items()} != SCENARIOS):
        raise AssertionError("Run does not match frozen protocol")
    with (directory / "replicates.csv").open(newline="") as handle:
        records = list(csv.DictReader(handle))
    if len(records) != 1500:
        raise AssertionError("Expected 5 x 100 x 3 saved paths")
    by_key = {}
    for row in records:
        key = row["scenario"], int(row["repeat"]), row["method"]
        if key in by_key or key[0] not in SCENARIOS or not 0 <= key[1] < 100 or key[2] not in METHODS:
            raise AssertionError(f"Bad or duplicate key: {key}")
        by_key[key] = {f: int(row[f]) for f in FIELDS}
    distributions = {}
    for scenario in SCENARIOS:
        distributions[scenario] = {}
        for method in METHODS:
            paths = []
            for repeat in range(100):
                key = scenario, repeat, method
                expected = replay(*key, cap=2000)
                if by_key.get(key) != expected:
                    raise AssertionError(f"Path replay mismatch at {key}")
                paths.append(expected)
            distributions[scenario][method] = paths
    saved = json.loads((directory / "summary.json").read_text())
    for scenario in SCENARIOS:
        for method in METHODS:
            paths = distributions[scenario][method]
            group = saved[scenario][method]
            correct_costs = [p["duration"] for p in paths if p["correct"]]
            expected = {
                "correct": len(correct_costs),
                "wrong": sum(p["wrong"] for p in paths),
                "abstained": sum(p["abstained"] for p in paths),
                "mean_capped_duration": sum(p["duration"] for p in paths) / 100,
                "mean_completed_duration": (
                    sum(correct_costs) / len(correct_costs) if correct_costs else None),
                "mean_capped_tasks": sum(p["tasks"] for p in paths) / 100,
            }
            for k, v in expected.items():
                if v is None and group[k] is None:
                    continue
                if not math.isclose(v, group[k], abs_tol=1e-9):
                    raise AssertionError(f"Summary mismatch: {scenario}, {method}, {k}")
    uncertainty = {}
    bootstrap = np.random.default_rng(20261025)
    for scenario in tuple(SCENARIOS)[:3]:
        uncertainty[scenario] = {}
        augmented = distributions[scenario]["adaptive_augmented"]
        for method in METHODS[:2]:
            control = distributions[scenario][method]
            if any(not a["correct"] or not b["correct"]
                   for a, b in zip(augmented, control)):
                raise AssertionError("Bootstrap comparison requires full completion")
            a = np.array([p["duration"] for p in augmented])
            b = np.array([p["duration"] for p in control])
            indices = bootstrap.integers(0, 100, size=(10000, 100))
            savings = 1 - a[indices].mean(axis=1) / b[indices].mean(axis=1)
            uncertainty[scenario][method] = {
                "saving_fraction": float(1 - a.mean() / b.mean()),
                "paired_bootstrap_95_percentile": [float(v) for v in
                                                  np.quantile(savings, [.025, .975])],
            }
    output = {"replayed_paths": len(by_key),
              "protocol_sha256": protocol_hash,
              "all_1500_rows_and_summary_verified": True,
              "paired_bootstrap_descriptive": uncertainty,
              "note": "Bootstrap intervals describe simulation variability, not human minutes or novel inference."}
    (directory / "audit.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="experiments/panel_aware_gate/results_reference")
    print(json.dumps(audit(parser.parse_args().input), indent=2))
