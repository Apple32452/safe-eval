"""Paid-label prospective reference-star pilot with matched item/rater ledgers."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

SYSTEMS = 18
EDGES = SYSTEMS - 1
ALPHA = .05
Q = .75
RHOS = (.10, .25, .50, .85)
SEED = 20261022
SCENARIOS = ("shared_easy", "shared_weak", "independent", "long_tail", "tie")
METHODS = ("paired", "partial", "degree_switch")


def population(scenario):
    if scenario not in SCENARIOS:
        raise ValueError(scenario)
    rng = np.random.default_rng(SEED + SCENARIOS.index(scenario))
    item = rng.uniform(-.05, .05, (64, 1))
    rater = rng.uniform(-.025, .025, (1, 8))
    shared = rng.random((64, 8))
    if scenario == "shared_weak":
        levels = np.concatenate(([.72], np.linspace(.08, .48, EDGES)))
    elif scenario == "long_tail":
        levels = np.concatenate(([.82], np.linspace(.08, .38, EDGES - 1), [.56]))
    else:
        levels = np.concatenate(([.83], np.linspace(.08, .50, EDGES)))
    outputs = []
    for j, level in enumerate(levels):
        latent = rng.random((64, 8)) if scenario == "independent" else shared
        if scenario == "tie" and j == EDGES:
            outputs.append(outputs[0].copy())
        else:
            outputs.append((latent < np.clip(level + item + rater, 0, 1)).astype(np.uint8))
    return np.stack(outputs)


def bounds(predictions, q):
    """Bounds on reference minus corrected candidate, before seeing A."""
    minimum, maximum = math.inf, -math.inf
    for a in (0, 1):
        m = float(predictions[a])
        minimum = min(minimum, a - m - (1 - m) / q, a - m)
        maximum = max(maximum, a - m + m / q, a - m)
    return max(-minimum, 1e-12), max(maximum, 1e-12)


def update_wealth(wealth, observation, limits):
    """Return four-component mixture wealth in each directional process."""
    negative, positive = limits
    if not -negative - 1e-10 <= observation <= positive + 1e-10:
        raise AssertionError("Observation outside pre-draw bounds")
    stakes = np.asarray(RHOS)
    wealth[0] += np.log1p(stakes * observation / negative)
    wealth[1] += np.log1p(-stakes * observation / positive)
    return np.logaddexp.reduce(wealth, axis=1) - math.log(len(RHOS))


def ledger(scenario, repeat, rounds):
    rng = np.random.default_rng(SEED + 10000 * SCENARIOS.index(scenario) + repeat)
    return (rng.integers(64, size=rounds), rng.integers(8, size=rounds),
            rng.random((rounds, EDGES)))


def run_one(scores, item_ids, rater_ids, coins, method, audit=False):
    if method not in METHODS:
        raise ValueError(method)
    state = np.zeros(EDGES, dtype=np.int8)
    wealth = np.zeros((EDGES, 2, len(RHOS)))
    # Beta(2,2) prior in each reference stratum; all subsequent labels paid.
    label_sum = np.zeros((EDGES, 2)) + 2
    label_count = np.zeros((EDGES, 2)) + 4
    cost = 0
    queried = 0
    processed = 0
    log_threshold = math.log(2 * EDGES / ALPHA)
    for t in range(len(item_ids)):
        active = np.flatnonzero(state == 0)
        if not len(active):
            break
        processed += 1
        q = (1. if method == "paired" or (method == "degree_switch" and len(active) <= 4)
             else Q)
        # Freeze prediction and bounds before drawing the round's indices.
        predictions = label_sum[active] / label_count[active]
        limits = [bounds(prediction, q) for prediction in predictions]
        a = int(scores[0, item_ids[t], rater_ids[t]])
        cost += 1
        for index, edge in enumerate(active):
            bought = bool(coins[t, edge] < q)
            b = int(scores[edge + 1, item_ids[t], rater_ids[t]]) if bought else 0
            if bought:
                cost += 1
                queried += 1
            m = predictions[index, a]
            g = a - m - (b - m) / q if bought else a - m
            if q == 1 and abs(g - (a - b)) > 1e-12:
                raise AssertionError("Paired correction mismatch")
            evidence = update_wealth(wealth[edge], g, limits[index])
            if evidence[0] >= log_threshold and evidence[1] >= log_threshold:
                raise AssertionError("Opposite declarations")
            if evidence[0] >= log_threshold:
                state[edge] = 1
            elif evidence[1] >= log_threshold:
                state[edge] = -1
            if bought:
                label_count[edge, a] += 1
                label_sum[edge, a] += b
    truth = np.sign(scores[0].mean() - scores[1:].mean(axis=(1, 2))).astype(int)
    result = dict(cost=cost, rounds=processed, complete=bool(np.all(state)),
                  correct=int(np.sum((state != 0) & (state == truth))),
                  wrong=int(np.sum((state != 0) & (state != truth))),
                  unresolved=int(np.sum(state == 0)), queried=queried)
    if audit:
        result["decisions"] = state.astype(int).tolist()
        result["truth"] = truth.tolist()
    return result


def experiment(repeats, rounds):
    if repeats <= 0 or rounds <= 0:
        raise ValueError("Positive repeats and cap required")
    results = []
    for scenario in SCENARIOS:
        scores = population(scenario)
        truth = np.sign(scores[0].mean() - scores[1:].mean(axis=(1, 2))).astype(int)
        if scenario == "tie":
            assert np.sum(truth == 0) == 1
        else:
            assert np.all(truth != 0)
        for repeat in range(repeats):
            item, rater, coins = ledger(scenario, repeat, rounds)
            for method in METHODS:
                results.append(dict(scenario=scenario, repeat=repeat, method=method,
                                    **run_one(scores, item, rater, coins, method)))
    return results


def summarize(results, repeats):
    rows = []
    for scenario in SCENARIOS:
        group = {}
        for method in METHODS:
            values = [r for r in results if r["scenario"] == scenario and r["method"] == method]
            group[method] = dict(completed=sum(r["complete"] for r in values),
                                 wrong=sum(r["wrong"] for r in values),
                                 mean_cost=float(np.mean([r["cost"] for r in values])),
                                 mean_correct=float(np.mean([r["correct"] for r in values])),
                                 mean_unresolved=float(np.mean([r["unresolved"] for r in values])))
        passed = False
        if scenario != "tie" and group["paired"]["completed"] == repeats:
            passed = any(group[m]["completed"] >= group["paired"]["completed"] and
                         group[m]["wrong"] <= group["paired"]["wrong"] and
                         group[m]["mean_cost"] <= .9 * group["paired"]["mean_cost"]
                         for m in METHODS[1:])
        rows.append(dict(scenario=scenario, methods=group, cost_gate_passed=passed))
    return dict(repeats=repeats, scenarios=rows,
                overall_gate_passed=sum(r["cost_gate_passed"] for r in rows) >= 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=2000)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    results = experiment(args.repeats, args.rounds)
    with (output / "replicates.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    summary = summarize(results, args.repeats)
    (output / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
