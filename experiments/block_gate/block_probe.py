"""Development screen: shared-item, partial-system acquisition versus Stage 22.

All target scores are fixed. Randomness comes only from the predictable block
design, not from a superpopulation assumption about items or systems.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "cell_level_gate"))
sys.path.insert(0, str(ROOT / "experiments" / "stage22"))
from run_stage22 import make_paths, simulate_graph, star_edges  # noqa: E402

RHOS = np.array([.02, .05, .1, .2, .4, .8])


def design(seen: np.ndarray, edges: np.ndarray, unresolved: np.ndarray, q: float):
    """Return eligible items and predictable conditional inclusion chances.

    One unknown endpoint on a chosen item is always bought; each other
    unknown active endpoint is bought independently with probability q.
    """
    if not 0 < q <= 1:
        raise ValueError("The inclusion floor q must be in (0,1]")
    active = np.unique(edges[unresolved].ravel())
    eligible = np.flatnonzero(np.any(~seen[active], axis=0))
    if not len(eligible):
        raise AssertionError("Unresolved edge without available endpoints")
    chance = np.zeros(seen.shape, dtype=float)
    for i in eligible:
        unknown = active[~seen[active, i]]
        chance[unknown, i] = q / len(eligible)
        chance[unknown[0], i] = 1. / len(eligible)
    return eligible, chance


def signals_and_bounds(scores: np.ndarray, seen: np.ndarray,
                       edges: np.ndarray, unresolved: np.ndarray,
                       chance: np.ndarray, bought: list[tuple[int, int]]):
    """Conditional HT signal and support bounds for each unresolved edge.

    The support has exactly one item per block. For a plus signal, only the
    b endpoint can be negative and for a minus signal only a can be positive.
    Their separate maxima across possible items give valid bounds.
    """
    values = []
    for e in np.flatnonzero(unresolved):
        a, b = map(int, edges[e])
        known = float(scores[a, seen[a]].sum() - scores[b, seen[b]].sum())
        max_a = float(np.max(1. / chance[a, ~seen[a]])) if np.any(~seen[a]) else 0.
        max_b = float(np.max(1. / chance[b, ~seen[b]])) if np.any(~seen[b]) else 0.
        x = known + sum((1 if v == a else -1 if v == b else 0)
                        * float(scores[v, i]) / chance[v, i]
                        for v, i in bought)
        values.append((int(e), x, known - max_b, known + max_a))
    return values


def block_certificate(scores, edges, rng, q=1., alpha=.05,
                      return_trace=False):
    scores = np.asarray(scores, dtype=float)
    edges = np.asarray(edges, dtype=np.int16)
    if scores.ndim != 2 or scores.shape[1] < 2 or not np.isfinite(scores).all():
        raise ValueError("Expected a finite systems-by-items score matrix")
    if np.any((scores < 0) | (scores > 1)) or len(edges) == 0:
        raise ValueError("Scores must be in [0,1] and edges nonempty")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    if not 0 < q <= 1:
        raise ValueError("q must lie in (0,1]")
    systems, items = scores.shape
    seen = np.zeros_like(scores, dtype=bool)
    log_plus = np.zeros((len(edges), len(RHOS)))
    log_minus = np.zeros_like(log_plus)
    decisions = np.full(len(edges), 2, dtype=np.int8)
    trace = []
    cost = 0
    log_threshold = np.log(2 * len(edges) / alpha)

    def close_exact():
        for e in np.flatnonzero(decisions == 2):
            a, b = map(int, edges[e])
            known = float(scores[a, seen[a]].sum() - scores[b, seen[b]].sum())
            low = known - np.count_nonzero(~seen[b])
            high = known + np.count_nonzero(~seen[a])
            if low > 1e-12:
                decisions[e] = 1
            elif high < -1e-12:
                decisions[e] = -1
            elif np.all(seen[a]) and np.all(seen[b]):
                decisions[e] = np.sign(known)

    def crossed(log_wealth):
        peak = np.max(log_wealth)
        return peak + np.log(np.mean(np.exp(log_wealth - peak))) >= log_threshold

    close_exact()
    while np.any(decisions == 2):
        unresolved = decisions == 2
        eligible, chance = design(seen, edges, unresolved, q)
        item = int(rng.choice(eligible))
        active = np.unique(edges[unresolved].ravel())
        unknown = active[~seen[active, item]]
        selected = [int(unknown[0])]
        selected.extend(int(v) for v in unknown[1:] if rng.random() < q)
        bought = [(v, item) for v in selected]
        updates = signals_and_bounds(scores, seen, edges, unresolved, chance, bought)
        for e, x, low, high in updates:
            factor_plus = 1 + RHOS * x / max(1., -low)
            factor_minus = 1 - RHOS * x / max(1., high)
            if np.min(factor_plus) <= 0 or np.min(factor_minus) <= 0:
                raise AssertionError("Predictable support bound was violated")
            log_plus[e] += np.log(factor_plus)
            log_minus[e] += np.log(factor_minus)
        for v, i in bought:
            if seen[v, i]:
                raise AssertionError("A score was purchased twice")
            seen[v, i] = True
            cost += 1
        close_exact()
        for e in np.flatnonzero(decisions == 2):
            forward, reverse = crossed(log_plus[e]), crossed(log_minus[e])
            if forward and not reverse:
                decisions[e] = 1
            elif reverse and not forward:
                decisions[e] = -1
        if return_trace:
            trace.append(dict(item=item, bought=bought,
                              updates=[(e, x, low, high) for e, x, low, high in updates],
                              cost=cost, decisions=decisions.tolist()))
        if cost > systems * items:
            raise AssertionError("Invalid label accounting")
    truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                    scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
    return dict(cost=cost, wrong=int(np.any(decisions != truth)),
                decisions=decisions.tolist(), trace=trace if return_trace else None)


def matched_stage22_cost(scores, edges, item_order, rng, alpha=.05):
    """Price frozen Stage 22 on the full-block trial's exact item path."""
    systems, items = scores.shape
    item_order = np.asarray(item_order, dtype=np.int32)
    if not np.array_equal(np.sort(item_order), np.arange(items)):
        raise ValueError("The control needs a complete shared item permutation")
    paths = np.tile(item_order, (len(edges), 1))
    priority = np.empty((systems, items), dtype=np.int64)
    position = 0
    for i in item_order:
        for v in rng.permutation(systems):
            priority[v, i] = position
            position += 1
    events, _ = make_paths(scores, edges, paths[:, None, :],
                           2 * len(edges) / alpha)
    result = simulate_graph(scores, edges, paths, events[:, 0], priority,
                            "star_pruned")
    return result["completion_cost"]


def run(repeats=30, qs=(1., .75, .5)):
    if repeats < 1:
        raise ValueError("Positive repeats required")
    if 1. not in qs:
        raise ValueError("q=1 is required for a matched Stage 22 item path")
    scenarios = {
        "easy-independent": (np.array([.9, .1, .2, .4, .6]), False),
        "weak-independent": (np.array([.6, .5, .48, .45, .42]), False),
        "easy-correlated": (np.array([.9, .1, .2, .4, .6]), True),
        "heterogeneous-star": (np.array([.9, .89, .85, .5, .1]), False),
    }
    results = {}
    for name, (probabilities, correlated) in scenarios.items():
        old = []
        costs = {str(q): [] for q in qs}
        wrong = {str(q): 0 for q in qs}
        for rep in range(repeats):
            rng = np.random.default_rng(20261022 + rep + 100 * len(name))
            u = rng.random((1 if correlated else len(probabilities), 128))
            scores = (u < probabilities[:, None]).astype(float)
            edges = star_edges(len(probabilities), 0)
            full = block_certificate(scores, edges,
                                     np.random.default_rng(4000 + rep),
                                     q=1., return_trace=True)
            prefix = [row["item"] for row in full["trace"]]
            if len(set(prefix)) != len(prefix):
                raise AssertionError("Full-block control repeated an item")
            remainder = [i for i in range(scores.shape[1]) if i not in prefix]
            order = prefix + list(np.random.default_rng(9000 + rep).permutation(remainder))
            control_cost = matched_stage22_cost(scores, edges, order,
                                                np.random.default_rng(5000 + rep))
            if not control_cost <= full["cost"] < control_cost + len(probabilities):
                raise AssertionError("Full-block control failed paired path parity")
            old.append(control_cost)
            for q in qs:
                result = full if q == 1. else block_certificate(
                    scores, edges, np.random.default_rng(4000 + rep), q=q)
                costs[str(q)].append(result["cost"])
                wrong[str(q)] += result["wrong"]
        results[name] = dict(repeats=repeats, stage22_mean=float(np.mean(old)),
                             stage22_costs=old,
                             blocks={str(q): dict(mean=float(np.mean(costs[str(q)])),
                                                  extra_cost_percent=float(100 * (
                                                      np.mean(costs[str(q)]) / np.mean(old) - 1)),
                                                  wrong=wrong[str(q)], costs=costs[str(q)])
                                     for q in qs})
        print(name, "stage22", round(results[name]["stage22_mean"], 2),
              "blocks", {q: (round(v["mean"], 2),
                              round(v["extra_cost_percent"], 2))
                         for q, v in results[name]["blocks"].items()}, flush=True)
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
