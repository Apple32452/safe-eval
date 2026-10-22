"""Predeclared synthetic comparison: Stage 22 and elementary partial bounds."""
from __future__ import annotations

import argparse
import csv
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage17"))
sys.path.insert(0, str(HERE.parent / "stage22"))
from continuous_engine import make_paths
from partial_exposure import run_dynamic, run_static

SEED = 20261022
SYSTEMS = 5
ITEMS = 24
REPEATS = 100
ALPHA = 0.05
SCENARIOS = ("tie", "weak", "strong", "anticorrelated")
GRAPHS = ("star", "ring", "complete")


def matrix(scenario):
    rng = np.random.default_rng(SEED + SCENARIOS.index(scenario))
    common = rng.uniform(-0.20, 0.20, size=ITEMS)
    if scenario == "tie":
        # Identical columns for every system: exact full-pool ties.
        base = (rng.random(ITEMS) < 0.5).astype(float)
        return np.tile(base, (SYSTEMS, 1))
    if scenario == "weak":
        levels = np.array([0.42, 0.46, 0.50, 0.54, 0.58])
    elif scenario == "strong":
        levels = np.array([0.12, 0.30, 0.50, 0.70, 0.88])
    elif scenario == "anticorrelated":
        base = (rng.random(ITEMS) < 0.5).astype(float)
        return np.vstack([base, 1 - base, np.roll(base, 1),
                          1 - np.roll(base, 1), rng.integers(0, 2, ITEMS)])
    else:
        raise ValueError("Unknown scenario")
    return (rng.random((SYSTEMS, ITEMS)) <
            np.clip(levels[:, None] + common[None, :], 0, 1)).astype(float)


def edges_for(graph):
    if graph == "star":
        return np.asarray([(0, j) for j in range(1, SYSTEMS)], dtype=np.int16)
    if graph == "ring":
        return np.asarray(sorted({tuple(sorted((j, (j + 1) % SYSTEMS)))
                                  for j in range(SYSTEMS)}), dtype=np.int16)
    if graph == "complete":
        return np.asarray(list(combinations(range(SYSTEMS), 2)), dtype=np.int16)
    raise ValueError("Unknown graph")


def run(output, repeats=REPEATS):
    if repeats < 1:
        raise ValueError("At least one repeat required")
    rng = np.random.default_rng(SEED)
    rows = []
    for scenario in SCENARIOS:
        scores = matrix(scenario)
        for graph in GRAPHS:
            pairs = edges_for(graph)
            # Two directions per edge; Bonferroni family error 0.05.
            threshold = 2 * len(pairs) / ALPHA
            for repeat in range(repeats):
                permutation = rng.permutation(ITEMS)
                paths = np.tile(permutation, (len(pairs), 1))
                priority = rng.permutation(SYSTEMS * ITEMS).reshape(SYSTEMS, ITEMS)
                events, _ = make_paths(scores, pairs, paths[:, None, :], threshold)
                e = events[:, 0]
                baseline = run_static(scores, pairs, paths, e, priority)
                dynamic = run_dynamic(scores, pairs, paths, e, priority,
                                      partial_bounds=False)
                partial = run_dynamic(scores, pairs, paths, e, priority,
                                      partial_bounds=True)
                assert partial["cost"] <= dynamic["cost"] <= baseline["cost"]
                rows.append(dict(scenario=scenario, graph=graph, repeat=repeat,
                                 edges=len(pairs), baseline=baseline["cost"],
                                 dynamic=dynamic["cost"], partial=partial["cost"],
                                 deterministic=partial["deterministic"],
                                 baseline_wrong=baseline["wrong"],
                                 dynamic_wrong=dynamic["wrong"],
                                 partial_wrong=partial["wrong"]))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "replicates.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for scenario in SCENARIOS:
        for graph in GRAPHS:
            group = [r for r in rows if r["scenario"] == scenario and r["graph"] == graph]
            mean = lambda key: sum(r[key] for r in group) / len(group)
            summary.append(dict(scenario=scenario, graph=graph,
                                baseline=mean("baseline"), dynamic=mean("dynamic"),
                                partial=mean("partial"),
                                partial_relative_saving=(sum(r["baseline"] - r["partial"]
                                                             for r in group) /
                                                         sum(r["baseline"] for r in group)),
                                deterministic_per_repeat=mean("deterministic"),
                                baseline_family_error=sum(r["baseline_wrong"] > 0 for r in group),
                                partial_family_error=sum(r["partial_wrong"] > 0 for r in group)))
    metadata = dict(seed=SEED, systems=SYSTEMS, items=ITEMS, repeats=repeats,
                    alpha=ALPHA, scenario=list(SCENARIOS), graphs=list(GRAPHS),
                    matrix_shas={scenario: __import__("hashlib").sha256(
                        matrix(scenario).tobytes()).hexdigest() for scenario in SCENARIOS},
                    decision="Exploratory baseline gate, no new-method claim")
    (output / "summary.json").write_text(json.dumps(dict(metadata=metadata, rows=summary),
                                                      indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()
    run(args.output, args.repeats)
