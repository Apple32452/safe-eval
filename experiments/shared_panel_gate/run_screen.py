"""Fixed-pool five-way-panel sequential comparison, frozen in PROTOCOL.md."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
N = 96
K = 6
REPEATS = 40
PILOT = 48
ALPHA = .05
REQUIRED = 11
PAIRS = tuple((a, b) for a in range(K) for b in range(a + 1, K))
EDGE_PANEL = np.array([[p not in pair for p in range(K)] for pair in PAIRS], bool)
WEIGHT = 1 / (N * 4)
BET = np.array([.10, .25, .50, .80])
THRESHOLD = math.log(2 * len(PAIRS) / ALPHA)
METHODS = ("uniform_raw", "uniform_centered", "adaptive_all", "adaptive_active")
SCENARIOS = {
    "no_shift": (0., (1, 1, 1, 1, 1, 1)),
    "context_shift": (.75, (1, 1, 1, 1, 1, 1)),
    "context_and_cost": (.75, (1, 1, 2, 2, 3, 3)),
}
BASE = np.array([0., .28, .72, 1.2, 1.9, 2.7])


def rng_for(scenario, repeat):
    digest = hashlib.sha256(f"20261024|{scenario}|{repeat}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def potential_ledger(rng, amplitude):
    """Outcome shape (panel, item, pair); absent edges have zero entries."""
    utilities = rng.normal(0., 1., size=(N, K)) + BASE
    outcome = np.zeros((K, N, len(PAIRS)), dtype=np.int8)
    for p in range(K):
        scores = utilities + amplitude * np.cos((p + 1) *
                                                 (np.arange(K) + 2))
        for e, (a, b) in enumerate(PAIRS):
            if EDGE_PANEL[e, p]:
                outcome[p, :, e] = np.where(scores[:, a] > scores[:, b], 1, -1)
    return outcome


def panel_proposal(remaining, m, certified, cost, method, t):
    total = int(np.sum(remaining))
    if not total:
        raise ValueError("Cannot sample exhausted ledger")
    uniform = remaining / total
    if method in METHODS[:2] or t < PILOT:
        return uniform
    active = (np.ones(len(PAIRS), dtype=bool) if method == "adaptive_all"
              else certified == 0)
    strength = np.sum(EDGE_PANEL * active[:, None] *
                      np.maximum(.1, 1 - m ** 2), axis=0)
    weight = remaining * np.sqrt(strength / cost)
    if not np.any(weight):
        return uniform
    return .2 * uniform + .8 * weight / np.sum(weight)


def score_bounds(remaining, observed, m, q_panel, panel, revealed):
    """Predictable bounded target-unbiased score for all 15 edges."""
    if remaining[panel] <= 0 or q_panel[panel] <= 0:
        raise ValueError("Chosen panel must have remaining positive support")
    base = WEIGHT * (observed + np.sum(EDGE_PANEL *
                                      remaining[None, :] * m, axis=1))
    coeff = np.divide(WEIGHT * remaining, q_panel,
                      out=np.zeros(K), where=q_panel > 0)
    offsets_low = np.where(EDGE_PANEL, coeff[None, :] * (-1 - m), 0.)
    offsets_high = np.where(EDGE_PANEL, coeff[None, :] * (1 - m), 0.)
    low = base + np.minimum(0., np.min(offsets_low, axis=1))
    high = base + np.maximum(0., np.max(offsets_high, axis=1))
    x = base + np.where(EDGE_PANEL[:, panel],
                        coeff[panel] * (revealed - m[:, panel]), 0.)
    return x, low, high


def one_path(outcome, panel_u, item_u, method, costs):
    if method not in METHODS or panel_u.shape != item_u.shape or len(panel_u) != N*K:
        raise ValueError("One paired uniform ledger per fixed-pool cell")
    cost = np.array(costs, dtype=float)
    truth = np.sign(outcome.sum(axis=(0, 1))).astype(int)
    item_ids = [list(range(N)) for _ in range(K)]
    counts = np.zeros((len(PAIRS), K), dtype=int)
    sums = np.zeros((len(PAIRS), K), dtype=int)
    observed = np.zeros(len(PAIRS), dtype=int)
    certified = np.zeros(len(PAIRS), dtype=int)
    wealth = np.zeros((len(PAIRS), 2, len(BET)), dtype=float)
    paid = 0.
    used = set()
    direct = 0
    ambiguous = 0
    for t in range(N*K):
        remaining = np.array([len(a) for a in item_ids], dtype=float)
        m = (np.zeros_like(sums, dtype=float) if method == "uniform_raw" else
             sums / (counts + 4))
        q = panel_proposal(remaining, m, certified, cost, method, t)
        panel = min(K - 1, int(np.searchsorted(np.cumsum(q), panel_u[t],
                                               side="right")))
        if not item_ids[panel]:
            # Guard against cumulative floating-point rounding at one.
            panel = int(np.flatnonzero(remaining > 0)[-1])
        idx = min(len(item_ids[panel]) - 1,
                  int(item_u[t] * len(item_ids[panel])))
        item = item_ids[panel].pop(idx)
        if (panel, item) in used:
            raise AssertionError("Reused a purchased item-panel cell")
        used.add((panel, item))
        y = outcome[panel, item].astype(float)
        x, low, high = score_bounds(remaining, observed, m, q, panel, y)
        if np.any(x < low - 1e-10) or np.any(x > high + 1e-10):
            raise AssertionError("Score escaped predictable bounds")
        included = EDGE_PANEL[:, panel]
        counts[included, panel] += 1
        sums[included, panel] += outcome[panel, item, included]
        observed += outcome[panel, item]
        paid += cost[panel]
        for d, factor in enumerate((1 + BET[None, :] * x[:, None] /
                                    np.maximum(1., -low)[:, None],
                                    1 - BET[None, :] * x[:, None] /
                                    np.maximum(1., high)[:, None])):
            if np.any(factor < .2 - 1e-10):
                raise AssertionError("Negative betting factor")
            wealth[:, d, :] += np.log(factor)
        if t + 1 < PILOT:
            continue
        mix = np.logaddexp.reduce(wealth, axis=2) - math.log(len(BET))
        pos = mix[:, 0] >= THRESHOLD
        neg = mix[:, 1] >= THRESHOLD
        ambiguous += int(np.count_nonzero((certified == 0) & pos & neg))
        newly = (certified == 0) & (pos ^ neg)
        certified[newly] = np.where(pos[newly], 1, -1)
        direct += int(np.count_nonzero(newly))
        if int(np.count_nonzero(certified)) >= REQUIRED:
            break
    tasks = len(used)
    exact = 0
    if tasks == N*K:
        if not np.array_equal(observed, outcome.sum(axis=(0, 1))):
            raise AssertionError("Full evaluation is not exact")
        unresolved = (certified == 0) & (truth != 0)
        exact = int(np.count_nonzero(unresolved))
        certified[unresolved] = truth[unresolved]
    wrong = int(np.count_nonzero((certified != 0) & (certified != truth)))
    completed = int(np.count_nonzero(certified) >= REQUIRED and wrong == 0)
    return dict(method=method, tasks=tasks, duration=int(paid),
                certified=int(np.count_nonzero(certified)), direct=direct,
                exact=exact, wrong=wrong, completed=completed,
                ambiguous=ambiguous, unique=len(used))


def summarize(rows):
    output = {}
    for scenario in SCENARIOS:
        output[scenario] = {}
        for method in METHODS:
            subset = [r for r in rows if r["scenario"] == scenario and
                      r["method"] == method]
            if len(subset) != REPEATS:
                raise AssertionError("Missing prespecified repeats")
            completed = [r for r in subset if r["completed"]]
            output[scenario][method] = {
                "completed": len(completed),
                "paths_with_wrong_sign": sum(r["wrong"] > 0 for r in subset),
                "mean_capped_tasks": float(np.mean([r["tasks"] for r in subset])),
                "mean_capped_duration": float(np.mean([r["duration"] for r in subset])),
                "mean_completed_tasks": (float(np.mean([r["tasks"] for r in completed]))
                                         if completed else None),
                "mean_completed_duration": (float(np.mean([r["duration"] for r in completed]))
                                            if completed else None),
                "full_ledger_paths": sum(r["tasks"] == N*K for r in subset),
            }
    output["screen_pass"] = all(
        output[s]["adaptive_active"]["completed"] >=
        max(output[s][m]["completed"] for m in
            ("uniform_centered", "adaptive_all")) and
        output[s]["adaptive_active"]["paths_with_wrong_sign"] == 0 and
        all(output[s]["adaptive_active"]["mean_completed_duration"] is not None and
            output[s][m]["mean_completed_duration"] is not None and
            output[s]["adaptive_active"]["mean_completed_duration"] <
            output[s][m]["mean_completed_duration"] for m in
            ("uniform_centered", "adaptive_all"))
        for s in ("context_shift", "context_and_cost"))
    return output


def run(output):
    rows = []
    for scenario, (amplitude, costs) in SCENARIOS.items():
        for repeat in range(REPEATS):
            rng = rng_for(scenario, repeat)
            outcome = potential_ledger(rng, amplitude)
            panel_u, item_u = rng.random((2, N*K))
            for method in METHODS:
                rows.append(dict(scenario=scenario, repeat=repeat,
                                 **one_path(outcome, panel_u, item_u,
                                            method, costs)))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {"repeats": REPEATS, "pool": N, "panels": K,
                "alpha": ALPHA, "pilot": PILOT, "required": REQUIRED,
                "scenarios": SCENARIOS,
                "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    summary = summarize(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="experiments/shared_panel_gate/results_reference")
    print(json.dumps(run(parser.parse_args().output), indent=2))
