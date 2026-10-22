"""Exploratory fixed-pool arm-level confidence sequence versus Stage 22.

This is a diagnostic of an existing inference pattern, not a novelty claim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "stage22"))
from run_stage22 import star_edges  # noqa: E402

sys.path.insert(0, str(ROOT / "experiments" / "cell_level_gate"))
from cell_probe import stage22_cost  # noqa: E402

RHOS = np.array([.02, .05, .1, .2, .4, .8])
GRID = np.linspace(0., 1., 101)


class Arm:
    """Two-sided fixed-population mean CS with predictable bounded bets."""

    def __init__(self, n: int, alpha: float, systems: int, order: np.ndarray):
        self.n = n
        self.order = order
        self.count = 0
        self.total = 0.
        self.plus = np.zeros((len(GRID), len(RHOS)))
        self.minus = np.zeros_like(self.plus)
        self.threshold = np.log(2 * systems / alpha)

    def update(self, value: float) -> None:
        remaining = self.n - self.count
        if remaining <= 0:
            raise AssertionError("Sampled arm after complete exposure")
        center = (self.n * GRID - self.total) / remaining
        forward = (center > 0) & (center < 1)
        backward = forward.copy()
        self.plus[center < 0] = np.inf
        self.minus[center > 1] = np.inf
        if np.any(forward):
            c = center[forward, None]
            factor = 1 + RHOS[None, :] * (value - c) / c
            if np.any(factor <= 0):
                raise AssertionError("Nonpositive forward bet")
            self.plus[forward] += np.log(factor)
        if np.any(backward):
            c = center[backward, None]
            factor = 1 + RHOS[None, :] * (c - value) / (1 - c)
            if np.any(factor <= 0):
                raise AssertionError("Nonpositive backward bet")
            self.minus[backward] += np.log(factor)
        # At c=0, the null μ≤m requires all remaining scores to be zero.
        # At c=1, the null μ≥m requires all remaining scores to be one.
        if value > 0:
            self.plus[center == 0] = np.inf
        if value < 1:
            self.minus[center == 1] = np.inf
        self.count += 1
        self.total += value

    def interval(self) -> tuple[float, float]:
        if self.count == self.n:
            return self.total / self.n, self.total / self.n
        known_lo = self.total / self.n
        known_hi = (self.total + self.n - self.count) / self.n

        def crossed(log_wealth):
            peak = np.max(log_wealth, axis=1)
            mix = peak.copy()
            finite = np.isfinite(peak)
            mix[finite] += np.log(np.mean(
                np.exp(log_wealth[finite] - peak[finite, None]), axis=1))
            return mix >= self.threshold

        lower_grid = GRID[crossed(self.plus)]
        upper_grid = GRID[crossed(self.minus)]
        lo = max(known_lo, float(lower_grid.max()) if len(lower_grid) else 0.)
        hi = min(known_hi, float(upper_grid.min()) if len(upper_grid) else 1.)
        return lo, hi


def arm_certificate(scores, edges, rng, alpha=.05):
    systems, items = scores.shape
    orders = [rng.permutation(items) for _ in range(systems)]
    arms = [Arm(items, alpha, systems, order) for order in orders]
    decisions = np.full(len(edges), 2, dtype=np.int8)
    cost = 0
    while np.any(decisions == 2):
        intervals = np.array([arm.interval() for arm in arms])
        for index, (a, b) in enumerate(edges):
            if decisions[index] != 2:
                continue
            if intervals[a, 0] > intervals[b, 1]:
                decisions[index] = 1
            elif intervals[b, 0] > intervals[a, 1]:
                decisions[index] = -1
            elif (arms[a].count == items and arms[b].count == items):
                decisions[index] = np.sign(arms[a].total - arms[b].total)
        if not np.any(decisions == 2):
            break
        active = np.unique(edges[decisions == 2])
        available = [int(v) for v in active if arms[v].count < items]
        if not available:
            raise AssertionError("Unresolved comparison with fully exposed endpoints")
        # Sample the active arm with the broadest current uncertainty;
        # break ties with a seed-fixed uniform permutation of system IDs.
        widths = intervals[:, 1] - intervals[:, 0]
        choice = max(available, key=lambda v: (widths[v], -v))
        arm = arms[choice]
        item = int(arm.order[arm.count])
        arm.update(float(scores[choice, item]))
        cost += 1
    truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                    scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
    return cost, int(np.any(decisions != truth))


def run(repeats=30):
    if repeats < 1:
        raise ValueError("Positive repeats required")
    scenarios = {
        "easy-independent": (np.array([.9, .1, .2, .4, .6]), False),
        "weak-independent": (np.array([.6, .5, .48, .45, .42]), False),
        "easy-correlated": (np.array([.9, .1, .2, .4, .6]), True),
        "heterogeneous-star": (np.array([.9, .89, .85, .5, .1]), False),
    }
    results = {}
    for name, (probabilities, correlated) in scenarios.items():
        old, new, wrong = [], [], 0
        for rep in range(repeats):
            rng = np.random.default_rng(20261022 + rep + 100 * len(name))
            u = (rng.random((1, 128)) if correlated else
                 rng.random((len(probabilities), 128)))
            scores = (u < probabilities[:, None]).astype(float)
            edges = star_edges(len(probabilities), 0)
            old.append(stage22_cost(scores, edges, np.random.default_rng(1000 + rep)))
            cost, error = arm_certificate(scores, edges, np.random.default_rng(3000 + rep))
            new.append(cost)
            wrong += error
        results[name] = dict(repeats=repeats, stage22_mean=float(np.mean(old)),
                             arm_mean=float(np.mean(new)),
                             arm_extra_cost_percent=float(
                                 100 * (np.mean(new) / np.mean(old) - 1)),
                             wrong=int(wrong), stage22_costs=old, arm_costs=new)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.repeats)
    for name, entry in result.items():
        print(name, "stage22", round(entry["stage22_mean"], 2),
              "arm", round(entry["arm_mean"], 2),
              "arm extra cost %", round(entry["arm_extra_cost_percent"], 2),
              "wrong", entry["wrong"], flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
