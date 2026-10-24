"""Frozen prospective gap-aware panel proposal against matched controls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared_panel_gate"))
sys.path.insert(0, str(HERE.parent / "panel_oracle_gap"))
from run_screen import (ALPHA, BET, EDGE_PANEL, K, N, PAIRS, PILOT, REQUIRED,
                        SCENARIOS, THRESHOLD, WEIGHT, one_path,
                        panel_proposal, potential_ledger, score_bounds)
from run_probe import all_pair, optimize

REPEATS = 100
BLOCK = 24
GAP_FLOOR = .20
METHODS = ("uniform_raw", "uniform_centered", "adaptive_all", "gap_pilot")
DIAGNOSTICS = ("updates", "infeasible_updates", "feasible_starts",
               "reported_success_starts")


def rng_for(scenario: str, repeat: int):
    digest = hashlib.sha256(
        f"20261024|panel_gap_feasible|{scenario}|{repeat}".encode()
    ).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def fitted_proposal(m: np.ndarray, cost: np.ndarray):
    """Use only past-panel shrunken means, never the current outcome."""
    theta = (m * EDGE_PANEL).sum(axis=1) / 4.
    variance = EDGE_PANEL * np.maximum(.1, 1 - m ** 2)
    coefficients = variance / (16 * np.maximum(abs(theta), GAP_FLOOR)[:, None] ** 2)
    candidates = [np.full(K, 1. / K), all_pair(m, cost)]
    return optimize(coefficients, cost, candidates)


def remaining_proposal(remaining: np.ndarray, q_star: np.ndarray) -> np.ndarray:
    weight = remaining * q_star
    if not np.any(weight > 0):
        raise ValueError("Exhausted pool")
    return weight / weight.sum()


def one_candidate(outcome: np.ndarray, panel_u: np.ndarray, item_u: np.ndarray,
                  costs: tuple[int, ...], required: int = REQUIRED,
                  trace: list | None = None) -> dict:
    """Same score, stakes, thresholds, stopping as the published panel path."""
    if panel_u.shape != item_u.shape or len(panel_u) != N * K:
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
    direct = ambiguous = 0
    q_star = np.full(K, 1. / K)
    updates = infeasible = feasible_starts = reported_success_starts = 0
    for t in range(N * K):
        remaining = np.array([len(a) for a in item_ids], dtype=float)
        m = sums / (counts + 4)
        if t >= PILOT and (t - PILOT) % BLOCK == 0:
            q_star, diagnostic = fitted_proposal(m, cost)
            updates += 1
            infeasible += int(diagnostic["feasible_starts"] == 0)
            feasible_starts += diagnostic["feasible_starts"]
            reported_success_starts += diagnostic["reported_success_starts"]
        q = (panel_proposal(remaining, m, certified, cost, "uniform_centered", t)
             if t < PILOT else remaining_proposal(remaining, q_star))
        panel = min(K - 1, int(np.searchsorted(np.cumsum(q), panel_u[t],
                                               side="right")))
        if not item_ids[panel]:
            panel = int(np.flatnonzero(remaining > 0)[-1])
        idx = min(len(item_ids[panel]) - 1,
                  int(item_u[t] * len(item_ids[panel])))
        item = item_ids[panel].pop(idx)
        if trace is not None:
            trace.append((panel, item, q.copy()))
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
        if int(np.count_nonzero(certified)) >= required:
            break
    tasks = len(used)
    exact = 0
    if tasks == N * K:
        if not np.array_equal(observed, outcome.sum(axis=(0, 1))):
            raise AssertionError("Full evaluation is not exact")
        unresolved = (certified == 0) & (truth != 0)
        exact = int(np.count_nonzero(unresolved))
        certified[unresolved] = truth[unresolved]
    wrong = int(np.count_nonzero((certified != 0) & (certified != truth)))
    completed = int(np.count_nonzero(certified) >= required and wrong == 0)
    return dict(method="gap_pilot", tasks=tasks, duration=int(paid),
                certified=int(np.count_nonzero(certified)), direct=direct,
                exact=exact, wrong=wrong, completed=completed,
                ambiguous=ambiguous, unique=len(used), updates=updates,
                infeasible_updates=infeasible, feasible_starts=feasible_starts,
                reported_success_starts=reported_success_starts)


def one_case(scenario: str, repeat: int) -> list[dict]:
    amplitude, costs = SCENARIOS[scenario]
    rng = rng_for(scenario, repeat)
    outcome = potential_ledger(rng, amplitude)
    panel_u, item_u = rng.random((2, N * K))
    rows = []
    for method in METHODS:
        record = (one_candidate(outcome, panel_u, item_u, costs)
                  if method == "gap_pilot" else
                  dict(one_path(outcome, panel_u, item_u, method, costs),
                       **{k: 0 for k in DIAGNOSTICS}))
        rows.append(dict(scenario=scenario, repeat=repeat, **record))
    return rows


def summarize(rows: list[dict], repeats: int = REPEATS) -> dict:
    result = {}
    rng = np.random.default_rng(20261025)
    for scenario in SCENARIOS:
        block = {method: [r for r in rows if r["scenario"] == scenario and
                          r["method"] == method] for method in METHODS}
        if any(len(v) != repeats for v in block.values()):
            raise ValueError("Missing paths")
        result[scenario] = {}
        for method, group in block.items():
            result[scenario][method] = {
                "completed": sum(r["completed"] for r in group),
                "paths_with_wrong_sign": sum(r["wrong"] > 0 for r in group),
                "mean_capped_tasks": float(np.mean([r["tasks"] for r in group])),
                "mean_capped_duration": float(np.mean([r["duration"] for r in group])),
                "infeasible_updates": sum(r["infeasible_updates"] for r in group),
            }
        best = min(METHODS[:3], key=lambda m:
                   result[scenario][m]["mean_capped_duration"])
        candidate = np.array([r["duration"] for r in block["gap_pilot"]])
        control = np.array([r["duration"] for r in block[best]])
        ids = rng.integers(repeats, size=(10_000, repeats))
        bootstrap = 1 - candidate[ids].mean(axis=1) / control[ids].mean(axis=1)
        result[scenario]["comparison"] = {
            "best_original_control": best,
            "duration_saving_vs_best": float(1 - candidate.mean() / control.mean()),
            "paired_bootstrap_95": np.quantile(bootstrap, [.025, .975]).tolist(),
        }
    result["screen_pass"] = all(
        result[scenario]["gap_pilot"]["completed"] == repeats and
        result[scenario]["gap_pilot"]["paths_with_wrong_sign"] == 0 and
        all(result[scenario]["gap_pilot"]["completed"] >=
            result[scenario][m]["completed"] for m in METHODS[:3]) and
        result[scenario]["comparison"]["duration_saving_vs_best"] >= .10 and
        result[scenario]["comparison"]["paired_bootstrap_95"][0] > 0
        for scenario in ("context_shift", "context_and_cost"))
    return result


def run(output: Path, repeats: int = REPEATS) -> dict:
    if repeats < 1 or output.exists():
        raise ValueError("Require positive repeats and a new output directory")
    rows = [row for scenario in SCENARIOS for repeat in range(repeats)
            for row in one_case(scenario, repeat)]
    summary = summarize(rows, repeats)
    output.mkdir(parents=True)
    with (output / "replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "metadata.json").write_text(json.dumps({
        "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
        "repeats": repeats, "alpha": ALPHA, "pilot": PILOT, "required": REQUIRED,
        "block": BLOCK, "gap_floor": GAP_FLOOR,
        "status": "synthetic simulated-duration screen, no human data"
    }, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repeats), indent=2))
