"""Replay frozen paths, independently recalculate summaries and decision."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_feasible import (ALPHA, BLOCK, DIAGNOSTICS, GAP_FLOOR, K, METHODS,
                          N, PILOT, REQUIRED, SCENARIOS, one_candidate,
                          one_path, potential_ledger)


def audit(folder: Path) -> dict:
    metadata = json.loads((folder / "metadata.json").read_text())
    digest = hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()
    repeats = int(metadata["repeats"])
    if (metadata["protocol_sha256"] != digest or repeats < 1 or
            metadata["alpha"] != ALPHA or metadata["pilot"] != PILOT or
            metadata["required"] != REQUIRED or metadata["block"] != BLOCK or
            metadata["gap_floor"] != GAP_FLOOR):
        raise ValueError("Frozen metadata mismatch")
    with (folder / "replicates.csv").open(newline="") as handle:
        records = list(csv.DictReader(handle))
    if len(records) != len(SCENARIOS) * repeats * len(METHODS):
        raise ValueError("Wrong path count")
    rows = {}
    for raw in records:
        key = raw["scenario"], int(raw["repeat"]), raw["method"]
        if (key in rows or key[0] not in SCENARIOS or
                not 0 <= key[1] < repeats or key[2] not in METHODS):
            raise ValueError("Bad or duplicate path key")
        rows[key] = {name: int(value) for name, value in raw.items()
                     if name not in ("scenario", "repeat", "method")}
    for scenario, (amplitude, costs) in SCENARIOS.items():
        for repeat in range(repeats):
            seed_bytes = hashlib.sha256(
                f"20261024|panel_gap_feasible|{scenario}|{repeat}".encode()).digest()
            rng = np.random.default_rng(int.from_bytes(seed_bytes[:8], "little"))
            outcome = potential_ledger(rng, amplitude)
            panel_u, item_u = rng.random((2, K * N))
            for method in METHODS:
                path = (one_candidate(outcome, panel_u, item_u, costs)
                        if method == "gap_pilot" else
                        dict(one_path(outcome, panel_u, item_u, method, costs),
                             **{name: 0 for name in DIAGNOSTICS}))
                path.pop("method")
                if rows[scenario, repeat, method] != path:
                    raise ValueError(f"Path replay mismatch: {scenario} {repeat} {method}")
    saved = json.loads((folder / "summary.json").read_text())
    result = {}
    bootstrap = np.random.default_rng(20261025)
    for scenario in SCENARIOS:
        result[scenario] = {}
        for method in METHODS:
            block = [rows[scenario, i, method] for i in range(repeats)]
            group = saved[scenario][method]
            measures = {
                "completed": sum(row["completed"] for row in block),
                "paths_with_wrong_sign": sum(row["wrong"] > 0 for row in block),
                "mean_capped_tasks": sum(row["tasks"] for row in block) / repeats,
                "mean_capped_duration": sum(row["duration"] for row in block) / repeats,
                "infeasible_updates": sum(row["infeasible_updates"] for row in block),
            }
            for metric, expected in measures.items():
                if not np.isclose(group[metric], expected):
                    raise ValueError(f"Summary mismatch: {scenario} {method} {metric}")
            result[scenario][method] = measures
        best = min(METHODS[:3], key=lambda m:
                   result[scenario][m]["mean_capped_duration"])
        c = np.array([rows[scenario, i, "gap_pilot"]["duration"]
                      for i in range(repeats)])
        b = np.array([rows[scenario, i, best]["duration"]
                      for i in range(repeats)])
        draw = bootstrap.integers(repeats, size=(10_000, repeats))
        ci = np.quantile(1 - c[draw].mean(axis=1) / b[draw].mean(axis=1),
                         [.025, .975])
        comparison = saved[scenario]["comparison"]
        saving = 1 - c.mean() / b.mean()
        if (comparison["best_original_control"] != best or
                not np.isclose(comparison["duration_saving_vs_best"], saving) or
                not np.allclose(comparison["paired_bootstrap_95"], ci)):
            raise ValueError("Comparison or bootstrap mismatch")
        result[scenario]["comparison"] = {"best_original_control": best,
            "saving": float(saving), "bootstrap_95": ci.tolist()}
    pass_screen = all(
        result[s]["gap_pilot"]["completed"] == repeats and
        result[s]["gap_pilot"]["paths_with_wrong_sign"] == 0 and
        all(result[s]["gap_pilot"]["completed"] >= result[s][m]["completed"]
            for m in METHODS[:3]) and
        result[s]["comparison"]["saving"] >= .10 and
        result[s]["comparison"]["bootstrap_95"][0] > 0
        for s in ("context_shift", "context_and_cost"))
    if saved["screen_pass"] != pass_screen:
        raise ValueError("Screen decision mismatch")
    return {"status": "passed", "replayed_paths": len(records),
            "protocol_sha256": digest, "screen_pass": pass_screen,
            "scenarios": result,
            "interpretation": "synthetic cost and simulated stopping only; no human time"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = audit(args.input)
    if args.output:
        args.output.write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps(value, indent=2))
