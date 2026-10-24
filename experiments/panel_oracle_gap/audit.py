"""Recreate the frozen ledgers and independently check saved proxy values."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared_panel_gate"))
from run_screen import EDGE_PANEL, K, N, SCENARIOS, potential_ledger


def audit(folder: Path) -> dict:
    records = json.loads((folder / "rows.json").read_text())
    saved = json.loads((folder / "summary.json").read_text())
    metadata = json.loads((folder / "metadata.json").read_text())
    digest = hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()
    if metadata["protocol_sha256"] != digest:
        raise ValueError("Protocol hash mismatch")
    repeats = int(metadata["repeats"])
    if len(records) != repeats * len(SCENARIOS):
        raise ValueError("Missing saved matrices")
    result = {}
    bootrng = np.random.default_rng(20261024)
    for scenario, (amplitude, costs) in SCENARIOS.items():
        cost = np.asarray(costs, float)
        block = [row for row in records if row["scenario"] == scenario]
        if [row["repeat"] for row in block] != list(range(repeats)):
            raise ValueError("Missing, duplicate, or reordered repeats")
        all_values, oracle_values, uniform_values = [], [], []
        for row in block:
            if not (0 < row["feasible_starts"] <= 2 and
                    0 <= row["reported_success_starts"] <= row["feasible_starts"]):
                raise ValueError("Invalid optimizer diagnostics")
            # Do not import the production seed or objective implementations.
            raw = f"20261024|panel_oracle_gap|{scenario}|{row['repeat']}".encode()
            seed = int.from_bytes(hashlib.sha256(raw).digest()[:8], "little")
            outcome = potential_ledger(np.random.default_rng(seed), amplitude)
            mu = outcome.sum(axis=1).T / N
            theta = outcome.sum(axis=(0, 1)) / (4 * N)
            if not np.allclose(theta, row["theta"], atol=1e-12):
                raise ValueError("Wrong target mean")
            var = np.zeros_like(mu, float)
            for edge in range(len(theta)):
                for panel in range(K):
                    if EDGE_PANEL[edge, panel]:
                        ys = outcome[panel, :, edge].astype(float)
                        var[edge, panel] = np.mean((ys - mu[edge, panel]) ** 2)
            strength = np.sum(EDGE_PANEL * np.maximum(.1, 1 - mu * mu), axis=0)
            weight = np.sqrt(strength / cost)
            expected_all = .2 / K + .8 * weight / weight.sum()
            if not np.allclose(row["q"]["all_pair"], expected_all, atol=1e-10):
                raise ValueError("All-pair proposal was not replayed")
            if not np.allclose(row["q"]["uniform"], np.full(K, 1 / K), atol=1e-12):
                raise ValueError("Uniform proposal changed")
            coeff = var / (16 * np.maximum(np.abs(theta), .05)[:, None] ** 2)
            for name, values in (("all_pair", all_values),
                                 ("oracle", oracle_values),
                                 ("uniform", uniform_values)):
                q = np.asarray(row["q"][name], float)
                if abs(q.sum() - 1.) > 1e-9 or min(q) < .2 / K - 1e-9:
                    raise ValueError("Invalid proposal probabilities")
                recomputed = float(np.dot(q, cost) * np.max(np.sum(coeff / q, axis=1)))
                if not np.isclose(recomputed, row["proxy"][name], rtol=1e-9):
                    raise ValueError("Incorrect proxy value")
                values.append(recomputed)
            if oracle_values[-1] > min(all_values[-1], uniform_values[-1]) * (1+1e-7):
                raise ValueError("Optimizer is worse than an initial proposal")
        a = np.asarray(all_values)
        o = np.asarray(oracle_values)
        u = np.asarray(uniform_values)
        ids = bootrng.integers(repeats, size=(10_000, repeats))
        ci = np.quantile(1 - o[ids].mean(axis=1) / a[ids].mean(axis=1),
                         [.025, .975])
        numerical = {
            "mean_uniform_proxy": u.mean(),
            "mean_all_pair_proxy": a.mean(),
            "mean_oracle_proxy": o.mean(),
            "mean_headroom_vs_all_pair": np.mean(1 - o / a),
            "median_headroom_vs_all_pair": np.median(1 - o / a),
            "ratio_of_means_headroom": 1 - o.mean() / a.mean(),
        }
        for metric, value in numerical.items():
            if not np.isclose(float(saved[scenario][metric]), value, rtol=1e-9):
                raise ValueError(f"Summary mismatch: {scenario} {metric}")
        if not np.allclose(ci, saved[scenario]["ratio_of_means_bootstrap_95"]):
            raise ValueError("Bootstrap mismatch")
        if (saved[scenario]["oracle_solver_feasible_starts"] !=
                sum(row["feasible_starts"] for row in block) or
                saved[scenario]["oracle_solver_reported_success_starts"] !=
                sum(row["reported_success_starts"] for row in block)):
            raise ValueError("Solver diagnostics mismatch")
        result[scenario] = {"checked": repeats,
                            "oracle_strictly_better_than_all_pair": int(np.sum(o < a - 1e-7)),
                            "mean_headroom": float(numerical["mean_headroom_vs_all_pair"])}
    expected_screen = any(result[s]["mean_headroom"] >= .10
                          for s in ("context_shift", "context_and_cost"))
    if saved["priority_screen"] != expected_screen:
        raise ValueError("Priority screen mismatch")
    return {"status": "passed", "cases": len(records), "scenarios": result,
            "interpretation": "infeasible population-informed proxy; no stopping-cost result"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.input)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text)
