"""Historical-prediction block selection for fixed-pool graph comparisons.

Development only. Predictions are supplied before sampling target labels.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "block_gate"))
from block_probe import RHOS, matched_stage22_cost  # noqa: E402
sys.path.insert(0, str(ROOT / "experiments" / "stage22"))
from run_stage22 import star_edges  # noqa: E402

POLICIES = ("full_predict", "uniform_partial_predict", "graph_partial_predict")


def design(seen, observed, predictions, edges, unresolved, policy):
    """Return eligible items, their probabilities, and cell inclusion chances.

    The unobserved entries of ``observed`` must be zero, so this function
    cannot depend on any as-yet-unpurchased target score.
    """
    if policy not in POLICIES:
        raise ValueError("Unknown acquisition policy")
    active_edges = edges[unresolved]
    active = np.unique(active_edges.ravel())
    eligible = np.flatnonzero(np.any(~seen[active], axis=0))
    if not len(eligible):
        raise AssertionError("Unresolved edge has no available endpoint")
    systems, items = seen.shape
    degrees = np.bincount(active_edges.ravel(), minlength=systems)
    q = np.ones(systems) if policy == "full_predict" else np.full(systems, .75)
    if policy == "graph_partial_predict":
        estimated_totals = (observed + (~seen) * predictions).sum(axis=1)
        q = np.full(systems, .2)
        for a, b in active_edges:
            closeness = np.exp(-abs(estimated_totals[a] - estimated_totals[b]) /
                               (.12 * items))
            q[a] = max(q[a], .2 + .8 * closeness)
            q[b] = max(q[b], .2 + .8 * closeness)
        weighted = np.array([
            1. + sum(degrees[v] * predictions[v, i] * (1 - predictions[v, i])
                     for v in active if not seen[v, i])
            for i in eligible
        ])
        item_prob = .5 / len(eligible) + .5 * weighted / weighted.sum()
    else:
        item_prob = np.full(len(eligible), 1. / len(eligible))
    chance = np.zeros_like(predictions, dtype=float)
    designated = {}
    for i, p in zip(eligible, item_prob):
        unknown = active[~seen[active, i]]
        guaranteed = int(sorted(unknown, key=lambda v: (-degrees[v], int(v)))[0])
        designated[int(i)] = guaranteed
        chance[unknown, i] = p * q[unknown]
        chance[guaranteed, i] = p
    return eligible, item_prob, q, chance, designated


def step_signals(seen, observed, acquired, predictions, edges, unresolved,
                 chance, bought):
    """Predictable centered HT signal and support range for each active edge."""
    updates = []
    for e in np.flatnonzero(unresolved):
        a, b = map(int, edges[e])
        center = float(observed[a].sum() - observed[b].sum() +
                       predictions[a, ~seen[a]].sum() -
                       predictions[b, ~seen[b]].sum())
        negative = np.zeros(seen.shape[1])
        positive = np.zeros_like(negative)
        ua, ub = ~seen[a], ~seen[b]
        negative[ua] += predictions[a, ua] / chance[a, ua]
        negative[ub] += (1 - predictions[b, ub]) / chance[b, ub]
        positive[ua] += (1 - predictions[a, ua]) / chance[a, ua]
        positive[ub] += predictions[b, ub] / chance[b, ub]
        low, high = center - negative.max(), center + positive.max()
        x = center + sum((1 if v == a else -1 if v == b else 0) *
                         (acquired[v, i] - predictions[v, i]) / chance[v, i]
                         for v, i in bought)
        updates.append((int(e), float(x), float(low), float(high)))
    return updates


def certificate(scores, predictions, edges, rng, policy="graph_partial_predict",
                alpha=.05, return_trace=False):
    scores = np.asarray(scores, dtype=float)
    predictions = np.asarray(predictions, dtype=float)
    edges = np.asarray(edges, dtype=np.int16)
    if scores.ndim != 2 or scores.shape[1] < 2 or predictions.shape != scores.shape:
        raise ValueError("Scores and pre-trained predictions must have the same matrix shape")
    if not (np.isfinite(scores).all() and np.isfinite(predictions).all() and
            np.all((0 <= scores) & (scores <= 1)) and
            np.all((0 <= predictions) & (predictions <= 1))):
        raise ValueError("Scores and predictions must be in [0,1]")
    if policy not in POLICIES or not 0 < alpha < 1 or not len(edges):
        raise ValueError("Invalid policy, alpha, or edge list")
    seen = np.zeros_like(scores, dtype=bool)
    observed = np.zeros_like(scores)
    decisions = np.full(len(edges), 2, dtype=np.int8)
    log_plus = np.zeros((len(edges), len(RHOS)))
    log_minus = np.zeros_like(log_plus)
    threshold = np.log(2 * len(edges) / alpha)
    cost = 0
    trace = []

    def close_exact():
        for e in np.flatnonzero(decisions == 2):
            a, b = map(int, edges[e])
            known = observed[a].sum() - observed[b].sum()
            lower = known - np.count_nonzero(~seen[b])
            upper = known + np.count_nonzero(~seen[a])
            if lower > 1e-12:
                decisions[e] = 1
            elif upper < -1e-12:
                decisions[e] = -1
            elif np.all(seen[a]) and np.all(seen[b]):
                decisions[e] = np.sign(known)

    while np.any(decisions == 2):
        unresolved = decisions == 2
        eligible, item_prob, q, chance, designated = design(
            seen, observed, predictions, edges, unresolved, policy)
        item = int(rng.choice(eligible, p=item_prob))
        active = np.unique(edges[unresolved].ravel())
        unknown = active[~seen[active, item]]
        selected = [designated[item]]
        selected.extend(int(v) for v in unknown
                        if v != designated[item] and rng.random() < q[v])
        bought = [(v, item) for v in selected]
        # This temporary ledger reads newly chosen scores only after the
        # predictable item/subset draw. The design saw masked ``observed``.
        acquired = observed.copy()
        for v, i in bought:
            acquired[v, i] = scores[v, i]
        updates = step_signals(seen, observed, acquired, predictions, edges,
                               unresolved, chance, bought)
        for e, x, low, high in updates:
            forward = 1 + RHOS * x / max(1., -low)
            reverse = 1 - RHOS * x / max(1., high)
            if np.min(forward) <= 0 or np.min(reverse) <= 0:
                raise AssertionError("Predictable support bound was violated")
            log_plus[e] += np.log(forward)
            log_minus[e] += np.log(reverse)
        for v, i in bought:
            if seen[v, i]:
                raise AssertionError("Purchased a target score twice")
            seen[v, i] = True
            observed[v, i] = scores[v, i]
        cost += len(bought)
        close_exact()
        for e in np.flatnonzero(decisions == 2):
            peak_plus, peak_minus = log_plus[e].max(), log_minus[e].max()
            forward = (peak_plus + np.log(np.mean(np.exp(log_plus[e] - peak_plus)))
                       >= threshold)
            reverse = (peak_minus + np.log(np.mean(np.exp(log_minus[e] - peak_minus)))
                       >= threshold)
            if forward and not reverse:
                decisions[e] = 1
            elif reverse and not forward:
                decisions[e] = -1
        if return_trace:
            trace.append(dict(item=item, bought=bought, updates=updates,
                              decisions=decisions.tolist(), cost=cost))
        if cost > scores.size:
            raise AssertionError("Exceeded the fixed query pool")
    truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                    scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
    return dict(cost=cost, wrong=int(np.any(decisions != truth)),
                decisions=decisions.tolist(), trace=trace if return_trace else None)


def synthetic_case(name, rep, items=128, history=256):
    scenarios = {
        "easy-independent": (np.array([.9, .1, .2, .4, .6]), False, False),
        "weak-independent": (np.array([.6, .5, .48, .45, .42]), False, False),
        "easy-correlated": (np.array([.9, .1, .2, .4, .6]), True, False),
        "heterogeneous-star": (np.array([.9, .89, .85, .5, .1]), False, False),
        "reversed-history": (np.array([.9, .1, .2, .4, .6]), False, True),
    }
    base, correlated, reversed_history = scenarios[name]
    rng = np.random.default_rng(20261023 + rep + 100 * len(name))
    side_test, side_train = rng.uniform(-1, 1, size=items), rng.uniform(-1, 1, size=history)
    beta = .14 * np.ones(len(base))
    target_prob = np.clip(base[:, None] + beta[:, None] * side_test, .01, .99)
    historical_base = (1 - base) if reversed_history else base
    historical_beta = -beta if reversed_history else beta
    train_prob = np.clip(historical_base[:, None] +
                         historical_beta[:, None] * side_train, .01, .99)
    historical_labels = (rng.random((len(base), history)) < train_prob).astype(float)
    test_u = rng.random((1 if correlated else len(base), items))
    scores = (test_u < target_prob).astype(float)
    # A ridge regression on *separate* historical examples and disclosed
    # side features. The target matrix is never passed to this fit.
    features = np.column_stack((np.ones(history), side_train))
    test_features = np.column_stack((np.ones(items), side_test))
    coefficients = np.linalg.solve(features.T @ features +
                                    np.diag([.01, .2]), features.T @ historical_labels.T)
    predictions = np.clip((test_features @ coefficients).T, .02, .98)
    return scores, predictions, star_edges(len(base), 0)


def run(repeats=30):
    if repeats < 1:
        raise ValueError("Positive repeat count required")
    results = {}
    for name in ("easy-independent", "weak-independent", "easy-correlated",
                 "heterogeneous-star", "reversed-history"):
        costs = {policy: [] for policy in POLICIES}
        wrong = {policy: 0 for policy in POLICIES}
        raw = []
        for rep in range(repeats):
            scores, predictions, edges = synthetic_case(name, rep)
            full = certificate(scores, predictions, edges,
                               np.random.default_rng(4000 + rep),
                               "full_predict", return_trace=True)
            prefix = [step["item"] for step in full["trace"]]
            if len(set(prefix)) != len(prefix):
                raise AssertionError("Full control revisited an item")
            remainder = [i for i in range(scores.shape[1]) if i not in prefix]
            order = prefix + list(np.random.default_rng(9000 + rep).permutation(remainder))
            raw.append(matched_stage22_cost(scores, edges, order,
                                            np.random.default_rng(5000 + rep)))
            for policy in POLICIES:
                output = full if policy == "full_predict" else certificate(
                    scores, predictions, edges, np.random.default_rng(4000 + rep), policy)
                costs[policy].append(output["cost"])
                wrong[policy] += output["wrong"]
        results[name] = dict(repeats=repeats, raw_stage22=raw,
                             methods={policy: dict(costs=costs[policy], wrong=wrong[policy],
                                                   mean=float(np.mean(costs[policy])),
                                                   vs_raw_percent=float(100*(
                                                       np.mean(costs[policy]) / np.mean(raw)-1)),
                                                   vs_predict_full_percent=float(100*(
                                                       np.mean(costs[policy]) /
                                                       np.mean(costs["full_predict"])-1)))
                                      for policy in POLICIES})
        print(name, "raw", round(np.mean(raw), 2),
              {p: (round(results[name]["methods"][p]["mean"], 2),
                   round(results[name]["methods"][p]["vs_predict_full_percent"], 2))
               for p in POLICIES}, flush=True)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.repeats)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
