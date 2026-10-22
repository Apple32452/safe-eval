"""Exploratory cell-level finite-pool e-process, compared with frozen Stage 22.

This is a diagnostic prototype, not a new contribution or a locked experiment.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "stage22"))
from run_stage22 import make_paths, simulate_graph, star_edges


RHO = np.array([0.02, 0.05, 0.1, 0.2, 0.4, 0.8], dtype=float)


def cell_certificate(scores, edges, rng, alpha=0.05):
    """Single unknown-cell draw, uniform among all active-edge endpoints."""
    systems, items = scores.shape
    seen = np.zeros_like(scores, dtype=bool)
    wealth_plus = np.ones((len(edges), len(RHO)), dtype=float)
    wealth_minus = np.ones_like(wealth_plus)
    decision = np.full(len(edges), 2, dtype=np.int8)
    threshold = 2 * len(edges) / alpha
    cost = 0

    def close_deterministic():
        # Sharp logical bounds are free once their contributing cells are bought.
        for e, (a, b) in enumerate(edges):
            if decision[e] != 2:
                continue
            d = scores[a, seen[a]].sum() - scores[b, seen[b]].sum()
            lo = d - np.count_nonzero(~seen[b])
            hi = d + np.count_nonzero(~seen[a])
            if lo > 0:
                decision[e] = 1
            elif hi < 0:
                decision[e] = -1
            elif lo == hi == 0:
                decision[e] = 0

    while np.any(decision == 2):
        close_deterministic()
        if not np.any(decision == 2):
            break
        active = np.unique(edges[decision == 2].ravel())
        remaining = [(int(v), int(i)) for v in active for i in range(items)
                     if not seen[v, i]]
        if not remaining:
            raise AssertionError("Unresolved edge with no remaining cells")
        # The coin is drawn before the chosen cell's score is read.
        position = int(rng.integers(len(remaining)))
        v, i = remaining[position]
        p = 1 / len(remaining)
        for e, (a, b) in enumerate(edges):
            if decision[e] != 2:
                continue
            a, b = int(a), int(b)
            d = scores[a, seen[a]].sum() - scores[b, seen[b]].sum()
            # For any possible unknown score in [0,1], the next signal lies
            # between these two predictable numbers.
            lo = d - (1 / p if not seen[b].all() else 0)
            hi = d + (1 / p if not seen[a].all() else 0)
            x = d + ((1 if v == a else -1 if v == b else 0)
                     * scores[v, i] / p)
            plus = 1 + RHO * x / max(1.0, -lo)
            minus = 1 - RHO * x / max(1.0, hi)
            if np.min(plus) <= 0 or np.min(minus) <= 0:
                raise AssertionError("Negative betting factor")
            wealth_plus[e] *= plus
            wealth_minus[e] *= minus
        seen[v, i] = True
        cost += 1
        # At full exposure, exact signs take priority over statistical evidence.
        close_deterministic()
        for e in np.flatnonzero(decision == 2):
            if wealth_plus[e].mean() >= threshold:
                decision[e] = 1
            elif wealth_minus[e].mean() >= threshold:
                decision[e] = -1
    truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                    scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
    return cost, int(np.any(decision != truth)), decision


def stage22_cost(scores, edges, rng, alpha=0.05):
    systems, items = scores.shape
    item_path = rng.permutation(items).astype(np.int32)
    paths = np.tile(item_path, (len(edges), 1))
    priority = np.empty((systems, items), dtype=np.int64)
    position = 0
    for i in item_path:
        for v in rng.permutation(systems):
            priority[v, i] = position
            position += 1
    events, _ = make_paths(scores, edges, paths[:, None, :],
                           2 * len(edges) / alpha)
    result = simulate_graph(scores, edges, paths, events[:, 0], priority,
                            "star_pruned")
    return result["completion_cost"]


def audit_conditional_step():
    """Enumerate binary matrices, exposure masks and an adaptive unequal design."""
    from itertools import product

    checks = 0
    edges = ((0, 1), (0, 2))
    for bits in product((0.0, 1.0), repeat=6):
        scores = np.array(bits).reshape(3, 2)
        for exposure in product((False, True), repeat=6):
            seen = np.array(exposure).reshape(3, 2)
            for a, b in edges:
                unknown = [(v, i) for v in (0, 1, 2) for i in range(2)
                           if not seen[v, i]]
                if not unknown or seen[a].all() and seen[b].all():
                    continue
                known = scores[a, seen[a]].sum() - scores[b, seen[b]].sum()
                # All weights depend only on known scores and cell identities.
                weights = np.array([
                    1 + (v + i) % 3 + scores[v, seen[v]].sum()
                    for v, i in unknown
                ], dtype=float)
                probabilities = weights / weights.sum()
                signal = np.array([
                    known + (1 if v == a else -1 if v == b else 0)
                    * scores[v, i] / p
                    for (v, i), p in zip(unknown, probabilities)
                ])
                target = scores[a].sum() - scores[b].sum()
                np.testing.assert_allclose(probabilities @ signal, target,
                                           atol=1e-12)
                low = known - max((1 / p for (v, _), p in zip(unknown, probabilities)
                                   if v == b), default=0)
                high = known + max((1 / p for (v, _), p in zip(unknown, probabilities)
                                    if v == a), default=0)
                assert np.min(1 + 0.8 * signal / max(1.0, -low)) >= 0.2 - 1e-12
                assert np.min(1 - 0.8 * signal / max(1.0, high)) >= 0.2 - 1e-12
                if target <= 0:
                    assert probabilities @ (1 + 0.8 * signal / max(1.0, -low)) <= 1 + 1e-12
                if target >= 0:
                    assert probabilities @ (1 - 0.8 * signal / max(1.0, high)) <= 1 + 1e-12
                checks += 1
    return checks


def main():
    print("exact one-step binary state checks", audit_conditional_step())
    scenarios = {
        "easy-independent": (np.array([0.9, 0.1, 0.2, 0.4, 0.6]), False),
        "weak-independent": (np.array([0.6, 0.5, 0.48, 0.45, 0.42]), False),
        "easy-correlated": (np.array([0.9, 0.1, 0.2, 0.4, 0.6]), True),
    }
    for name, (probabilities, correlated) in scenarios.items():
        old, new, wrong = [], [], 0
        for rep in range(30):
            rng = np.random.default_rng(20261022 + rep + 100 * len(name))
            u = (rng.random((1, 128)) if correlated else
                 rng.random((len(probabilities), 128)))
            scores = (u < probabilities[:, None]).astype(float)
            edges = star_edges(len(probabilities), 0)
            old.append(stage22_cost(scores, edges, np.random.default_rng(1000 + rep)))
            cost, error, _ = cell_certificate(
                scores, edges, np.random.default_rng(2000 + rep)
            )
            new.append(cost)
            wrong += error
        print(name, "stage22", round(np.mean(old), 2), "cell", round(np.mean(new), 2),
              "cell extra cost %", round(100 * (np.mean(new) / np.mean(old) - 1), 2),
              "wrong", wrong, "completions", len(new))


if __name__ == "__main__":
    main()
