"""Exploratory five-way judgment-panel allocation under Koehn's 2012 model."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np


SYSTEMS = 15
PANEL_SIZE = 5
ALPHA = 0.05
RHO = np.array((0.10, 0.25, 0.50, 0.80))
PAIRS = np.array(list(itertools.combinations(range(SYSTEMS), 2)), dtype=np.int16)
PANELS = np.array(list(itertools.combinations(range(SYSTEMS), PANEL_SIZE)), dtype=np.int16)
EDGE_LOOKUP = np.full((SYSTEMS, SYSTEMS), -1, dtype=np.int16)
EDGE_LOOKUP[PAIRS[:, 0], PAIRS[:, 1]] = np.arange(len(PAIRS))
PANEL_EDGES = np.array([
    [EDGE_LOOKUP[a, b] for a, b in itertools.combinations(panel, 2)]
    for panel in PANELS
], dtype=np.int16)
METHODS = ("uniform_panel", "unresolved_panel")
SEED = 20261022


def rank_ranges(directions):
    """Conservative possible rank ranges from the directed certified DAG."""
    better = np.zeros((SYSTEMS, SYSTEMS), dtype=bool)
    for edge, direction in enumerate(directions):
        if direction:
            i, j = PAIRS[edge]
            winner, loser = (i, j) if direction > 0 else (j, i)
            better[winner, loser] = True
    for k in range(SYSTEMS):
        better |= better[:, k, None] & better[None, k, :]
    if np.any(np.diag(better)):
        # A cycle is a visible inconsistency among the declared directions.
        return None
    lower = 1 + better.sum(axis=0)
    upper = SYSTEMS - better.sum(axis=1)
    return [(int(a), int(b)) for a, b in zip(lower, upper)]


def run_one(qualities, candidate_panel_ids, means, method, fraction=0.70):
    if method not in METHODS:
        raise ValueError(method)
    if candidate_panel_ids.ndim != 2 or candidate_panel_ids.shape[0] != len(qualities):
        raise ValueError("One nonempty candidate panel list per round required")
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0,1]")
    target = math.ceil(fraction * len(PAIRS))
    threshold = math.log(2 * len(PAIRS) / ALPHA)
    state = np.zeros(len(PAIRS), dtype=np.int8)
    log_wealth = np.zeros((len(PAIRS), 2, len(RHO)))
    rounds = 0
    for t, candidates in enumerate(candidate_panel_ids):
        if int(np.sum(state != 0)) >= target:
            break
        if method == "uniform_panel":
            choice = int(candidates[0])
        else:
            unresolved = (state[PANEL_EDGES[candidates]] == 0).sum(axis=1)
            choice = int(candidates[int(np.argmax(unresolved))])
        edges = PANEL_EDGES[choice]
        active = edges[state[edges] == 0]
        a, b = PAIRS[active].T
        y = np.where(qualities[t, a] > qualities[t, b], 1., -1.)
        log_wealth[active, 0, :] += np.log1p(y[:, None] * RHO)
        log_wealth[active, 1, :] += np.log1p(-y[:, None] * RHO)
        evidence = np.logaddexp.reduce(log_wealth[active], axis=2) - math.log(len(RHO))
        if np.any((evidence[:, 0] >= threshold) & (evidence[:, 1] >= threshold)):
            raise AssertionError("Opposite declarations at the same time")
        state[active[evidence[:, 0] >= threshold]] = 1
        state[active[evidence[:, 1] >= threshold]] = -1
        rounds += 1
    true_sign = np.sign(means[PAIRS[:, 0]] - means[PAIRS[:, 1]])
    width = rank_ranges(state)
    return {
        "method": method,
        "panels": rounds,
        "derived_pair_outcomes": PANEL_EDGES.shape[1] * rounds,
        "certified": int(np.sum(state != 0)),
        "complete": int(np.sum(state != 0) >= target),
        "wrong": int(np.sum((state != 0) & (state != true_sign))),
        "mean_rank_width": float(np.mean([hi - lo + 1 for lo, hi in width])) if width else None,
        "cycle": int(width is None),
    }


def experiment(repeats, rounds, candidate_count=16):
    if min(repeats, rounds, candidate_count) <= 0:
        raise ValueError("Positive repeats, cap, and candidate count required")
    rows = []
    for repeat in range(repeats):
        rng = np.random.default_rng(SEED + repeat)
        means = rng.uniform(0, 10, SYSTEMS)
        qualities = rng.normal(means, math.sqrt(10), size=(rounds, SYSTEMS))
        candidates = rng.integers(len(PANELS), size=(rounds, candidate_count))
        for method in METHODS:
            rows.append({"repeat": repeat, **run_one(qualities, candidates, means, method)})
    return rows


def summarize(rows, repeats):
    summary = {}
    for method in METHODS:
        group = [r for r in rows if r["method"] == method]
        assert len(group) == repeats
        summary[method] = {
            "completed": sum(r["complete"] for r in group),
            "mean_capped_panels": float(np.mean([r["panels"] for r in group])),
            "mean_certified_pairs": float(np.mean([r["certified"] for r in group])),
            "mean_rank_width": float(np.mean([r["mean_rank_width"] for r in group
                                               if r["mean_rank_width"] is not None])),
            "wrong": sum(r["wrong"] for r in group),
            "cycles": sum(r["cycle"] for r in group),
        }
    if summary["uniform_panel"]["completed"] == summary["unresolved_panel"]["completed"] == repeats:
        uniform = summary["uniform_panel"]["mean_capped_panels"]
        active = summary["unresolved_panel"]["mean_capped_panels"]
        summary["paired_relative_saving"] = 1 - active / uniform
    else:
        summary["paired_relative_saving"] = None
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--rounds", type=int, default=6000)
    parser.add_argument("--output", type=Path, default=Path("results/stage31_development"))
    args = parser.parse_args()
    rows = experiment(args.repeats, args.rounds)
    summary = summarize(rows, args.repeats)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "summary.json").write_text(json.dumps({
        "model": "Koehn 2012-style iid normal quality, 15 systems, 5 per panel, variance 10",
        "seed": SEED, "repeats": args.repeats, "cap": args.rounds,
        "target_certified_pairs": 74, "alpha_familywise": ALPHA,
        "candidate_panels_per_round": 16, "summary": summary,
    }, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print("Results:", args.output)


if __name__ == "__main__":
    main()
