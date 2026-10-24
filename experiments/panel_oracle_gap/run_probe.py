"""Fresh-ledger, population-informed panel-allocation headroom diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared_panel_gate"))
from run_screen import EDGE_PANEL, K, N, PAIRS, SCENARIOS, potential_ledger


REPEATS = 100
FLOOR = .2 / K
GAP_FLOOR = .05
BOOT = 10_000


def rng_for(scenario: str, repeat: int):
    digest = hashlib.sha256(
        f"20261024|panel_oracle_gap|{scenario}|{repeat}".encode()
    ).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def oracle_coefficients(outcome: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-edge and panel centered variance scaled by signed target gap."""
    mu = outcome.mean(axis=1).T.astype(float)
    theta = outcome.sum(axis=(0, 1)) / (N * 4)
    var = np.where(EDGE_PANEL, np.maximum(0., 1 - mu ** 2), 0.)
    coefficients = var / (16 * np.maximum(np.abs(theta), GAP_FLOOR)[:, None] ** 2)
    return coefficients, mu, theta


def proxy(q: np.ndarray, coefficients: np.ndarray, cost: np.ndarray) -> float:
    q = np.asarray(q, float)
    if not np.isclose(q.sum(), 1.) or np.min(q) < FLOOR - 1e-8:
        raise ValueError("Proposal violates positive floor or normalization")
    return float(np.dot(q, cost) * np.max(coefficients @ (1. / q)))


def all_pair(mu: np.ndarray, cost: np.ndarray) -> np.ndarray:
    strength = np.sum(EDGE_PANEL * np.maximum(.1, 1 - mu ** 2), axis=0)
    weight = np.sqrt(strength / cost)
    return np.full(K, FLOOR) + .8 * weight / weight.sum()


def optimize(coefficients: np.ndarray, cost: np.ndarray,
             starting: list[np.ndarray]) -> tuple[np.ndarray, dict]:
    """Convex epigraph in per-duration draw rates r=q/(q dot cost)."""
    best = min(starting, key=lambda q: proxy(q, coefficients, cost))
    best_value = proxy(best, coefficients, cost)
    feasible = 0
    reported_success = 0
    # Keep the epigraph height near one even for small target gaps; the
    # constant rescaling changes neither the minimizer nor its constraints.
    scale = max(proxy(q, coefficients, cost) for q in starting)
    scaled = coefficients / max(scale, 1e-12)

    def inequalities(x):
        r, t = x[:K], x[K]
        return np.r_[t - scaled @ (1. / r), r - FLOOR * r.sum()]

    def inequality_jac(x):
        r = x[:K]
        a = np.zeros((len(PAIRS) + K, K + 1))
        a[:len(PAIRS), :K] = scaled / r[None, :] ** 2
        a[:len(PAIRS), K] = 1
        a[len(PAIRS):, :K] = np.eye(K) - FLOOR
        return a

    constraints = [
        {"type": "eq", "fun": lambda x: np.dot(x[:K], cost) - 1.,
         "jac": lambda x: np.r_[cost, 0.]},
        {"type": "ineq", "fun": inequalities, "jac": inequality_jac},
    ]
    for start in starting:
        r0 = start / np.dot(start, cost)
        x0 = np.r_[r0, max(scaled @ (1. / r0)) * (1 + 1e-9)]
        result = minimize(lambda x: x[K], x0, jac=lambda x: np.r_[np.zeros(K), 1.],
                          method="SLSQP", bounds=[(1e-9, None)] * K + [(0., None)],
                          constraints=constraints,
                          options={"ftol": 1e-10, "maxiter": 3000})
        if (np.min(inequalities(result.x)) >= -1e-7 and
                abs(np.dot(result.x[:K], cost) - 1.) <= 1e-8):
            r = result.x[:K]
            q = r / r.sum()
            # Project microscopic solver residuals onto the declared floor.
            slack = np.maximum(q - FLOOR, 0.)
            q = FLOOR + (1. - K * FLOOR) * slack / slack.sum()
            value = proxy(q, coefficients, cost)
            feasible += 1
            reported_success += int(result.success)
            if value < best_value:
                best, best_value = q, value
    return best, {"feasible_starts": feasible,
                  "reported_success_starts": reported_success,
                  "value": best_value}


def evaluate(scenario: str, repeat: int) -> dict:
    amplitude, costs = SCENARIOS[scenario]
    cost = np.asarray(costs, float)
    outcome = potential_ledger(rng_for(scenario, repeat), amplitude)
    coefficients, mu, theta = oracle_coefficients(outcome)
    proposals = {"uniform": np.full(K, 1. / K),
                 "all_pair": all_pair(mu, cost)}
    proposals["oracle"], diagnostic = optimize(
        coefficients, cost, list(proposals.values()))
    objectives = {name: proxy(q, coefficients, cost)
                  for name, q in proposals.items()}
    if objectives["oracle"] > min(objectives["uniform"], objectives["all_pair"]) * (1 + 1e-7):
        raise AssertionError("Optimized proposal exceeded a starting proposal")
    return {"scenario": scenario, "repeat": repeat,
            "theta": theta.tolist(),
            "q": {name: q.tolist() for name, q in proposals.items()},
            "proxy": objectives,
            "feasible_starts": diagnostic["feasible_starts"],
            "reported_success_starts": diagnostic["reported_success_starts"]}


def summarize(rows: list[dict]) -> dict:
    result = {}
    rng = np.random.default_rng(20261024)
    for scenario in SCENARIOS:
        records = [r for r in rows if r["scenario"] == scenario]
        all_r = np.array([r["proxy"]["all_pair"] for r in records])
        oracle_r = np.array([r["proxy"]["oracle"] for r in records])
        uniform_r = np.array([r["proxy"]["uniform"] for r in records])
        ids = rng.integers(len(records), size=(BOOT, len(records)))
        boot = 1. - oracle_r[ids].mean(axis=1) / all_r[ids].mean(axis=1)
        result[scenario] = {
            "mean_uniform_proxy": float(uniform_r.mean()),
            "mean_all_pair_proxy": float(all_r.mean()),
            "mean_oracle_proxy": float(oracle_r.mean()),
            "mean_headroom_vs_all_pair": float(np.mean(1. - oracle_r / all_r)),
            "median_headroom_vs_all_pair": float(np.median(1. - oracle_r / all_r)),
            "ratio_of_means_headroom": float(1. - oracle_r.mean() / all_r.mean()),
            "ratio_of_means_bootstrap_95": np.quantile(boot, [.025, .975]).tolist(),
            "oracle_solver_feasible_starts": int(sum(r["feasible_starts"]
                                                     for r in records)),
            "oracle_solver_reported_success_starts": int(sum(
                r["reported_success_starts"] for r in records)),
        }
    result["priority_screen"] = any(
        result[s]["mean_headroom_vs_all_pair"] >= .10
        for s in ("context_shift", "context_and_cost"))
    return result


def run(output: Path, repeats: int = REPEATS) -> dict:
    if repeats < 1 or output.exists():
        raise ValueError("Require positive repeats and a new output directory")
    rows = [evaluate(scenario, repeat) for scenario in SCENARIOS
            for repeat in range(repeats)]
    if any(row["feasible_starts"] == 0 for row in rows):
        raise RuntimeError("SLSQP found no feasible candidate on a frozen ledger")
    summary = summarize(rows)
    output.mkdir(parents=True)
    (output / "rows.json").write_text(json.dumps(rows, indent=2) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "metadata.json").write_text(json.dumps({
        "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
        "repeats": repeats, "status": "population-informed synthetic proxy only"
    }, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repeats), indent=2))
