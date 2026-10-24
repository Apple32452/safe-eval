"""Reproduce saved finite-pool paths and paired cost summaries."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("shared_panel_screen", HERE / "run_screen.py")
screen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(screen)


def audit(directory):
    directory = Path(directory)
    meta = json.loads((directory / "metadata.json").read_text())
    digest = hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()
    if (meta["protocol_sha256"] != digest or meta["repeats"] != 40
            or meta["pool"] != 96 or meta["panels"] != 6 or
            meta["pilot"] != 48 or meta["required"] != 11 or
            meta["alpha"] != .05 or
            {k: (float(v[0]), tuple(v[1])) for k, v in
             meta["scenarios"].items()} != screen.SCENARIOS):
        raise AssertionError("Frozen protocol metadata mismatch")
    with (directory / "replicates.csv").open(newline="") as handle:
        raw = list(csv.DictReader(handle))
    if len(raw) != len(screen.SCENARIOS) * screen.REPEATS * len(screen.METHODS):
        raise AssertionError("Missing or excess saved paths")
    rows = {}
    for record in raw:
        key = record["scenario"], int(record["repeat"]), record["method"]
        if (key in rows or key[0] not in screen.SCENARIOS or
                not 0 <= key[1] < screen.REPEATS or key[2] not in screen.METHODS):
            raise AssertionError(f"Bad path key {key}")
        rows[key] = {k: int(v) for k, v in record.items()
                     if k not in ("scenario", "repeat", "method")}
    context_variation = {}
    for scenario, (amplitude, costs) in screen.SCENARIOS.items():
        mixed = 0
        total = 0
        for repeat in range(screen.REPEATS):
            rng = screen.rng_for(scenario, repeat)
            outcome = screen.potential_ledger(rng, amplitude)
            panels, items = rng.random((2, screen.N * screen.K))
            for e in range(len(screen.PAIRS)):
                signs = outcome[screen.EDGE_PANEL[e], :, e]
                mixed += int(np.count_nonzero(np.min(signs, axis=0) <
                                               np.max(signs, axis=0)))
                total += screen.N
            for method in screen.METHODS:
                key = scenario, repeat, method
                calculated = screen.one_path(outcome, panels, items, method, costs)
                calculated.pop("method")
                if rows.get(key) != calculated:
                    raise AssertionError(f"Saved trajectory differs from replay: {key}")
        context_variation[scenario] = mixed / total
    saved = json.loads((directory / "summary.json").read_text())
    for scenario in screen.SCENARIOS:
        for method in screen.METHODS:
            records = [rows[scenario, r, method] for r in range(screen.REPEATS)]
            group = saved[scenario][method]
            if (group["completed"] != sum(r["completed"] for r in records)
                    or group["paths_with_wrong_sign"] !=
                    sum(r["wrong"] > 0 for r in records)
                    or abs(group["mean_capped_tasks"] -
                           sum(r["tasks"] for r in records) / screen.REPEATS) > 1e-9
                    or abs(group["mean_capped_duration"] -
                           sum(r["duration"] for r in records) / screen.REPEATS) > 1e-9):
                raise AssertionError("Saved summary disagrees with rows")
    bootstrap = np.random.default_rng(20261026)
    savings = {}
    for scenario in screen.SCENARIOS:
        savings[scenario] = {}
        candidate = np.array([rows[scenario, r, "adaptive_active"]["duration"]
                              for r in range(screen.REPEATS)])
        for method in screen.METHODS[:3]:
            control = np.array([rows[scenario, r, method]["duration"]
                                for r in range(screen.REPEATS)])
            if any(not rows[scenario, r, m]["completed"] for r in
                   range(screen.REPEATS) for m in ("adaptive_active", method)):
                raise AssertionError("Bootstrap requires complete correct paths")
            idx = bootstrap.integers(0, screen.REPEATS, size=(10000, screen.REPEATS))
            ratios = 1 - candidate[idx].mean(axis=1) / control[idx].mean(axis=1)
            savings[scenario][method] = {
                "relative_saving": float(1 - candidate.mean() / control.mean()),
                "paired_bootstrap_95_percentile": [float(x) for x in
                                                   np.quantile(ratios, [.025, .975])],
            }
    result = {"replayed_paths": len(rows),
              "protocol_sha256": digest,
              "saved_summaries_checked": True,
              "pair_item_with_context_disagreement": context_variation,
              "paired_bootstrap_descriptive": savings,
              "note": "Simulated panel durations and deterministic rankings; no human time or independent validation."}
    (directory / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="experiments/shared_panel_gate/results_reference")
    print(json.dumps(audit(parser.parse_args().input), indent=2))
