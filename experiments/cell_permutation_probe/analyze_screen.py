"""Read-only audit of the frozen screen and its saved cost table."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from run_screen import ALPHA, HERE, ITEMS, MASTER, SCENARIOS, matrix


def audit(directory):
    directory = Path(directory)
    meta = json.loads((directory / "metadata.json").read_text())
    digest = hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()
    if (meta["protocol_sha256"] != digest or meta["master"] != MASTER or
            meta["items"] != ITEMS or meta["alpha"] != ALPHA or
            meta["scenarios"] != {k: [*v] for k, v in SCENARIOS.items()}):
        raise ValueError("Input does not match the frozen protocol")
    repeats = meta["repeats"]
    if not 0 < repeats <= 50:
        raise ValueError("Unexpected number of repeats")
    with (directory / "replicates.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {(scenario, str(i)) for scenario in SCENARIOS for i in range(repeats)}
    actual = [(row["scenario"], row["repeat"]) for row in rows]
    if len(rows) != len(expected) or set(actual) != expected:
        raise ValueError("Duplicate, missing, or unexpected matrix rows")
    summary = {}
    for scenario in SCENARIOS:
        subset = [row for row in rows if row["scenario"] == scenario]
        for row in subset:
            scores = matrix(scenario, int(row["repeat"]))
            truth = np.sign(scores[0].sum() - scores[1:].sum(axis=1))
            recorded_truth = json.loads(row["truth"])
            if (recorded_truth != truth.astype(int).tolist() or
                    json.loads(row["decision"]) != recorded_truth or
                    not 1 <= int(row["stage22"]) <= 5 * ITEMS or
                    not 1 <= int(row["cells"]) <= 5 * ITEMS):
                raise ValueError("Wrong direction or invalid label count")
        base = np.mean([int(row["stage22"]) for row in subset])
        cells = np.mean([int(row["cells"]) for row in subset])
        summary[scenario] = dict(stage22=base, cells=cells,
                                 saving_percent=100 * (base - cells) / base,
                                 passed=bool(cells <= .9 * base))
    summary["gate_pass"] = sum(item["passed"] for item in summary.values()) >= 3
    saved = json.loads((directory / "summary.json").read_text())
    for scenario, result in summary.items():
        if scenario == "gate_pass":
            if result != saved[scenario]:
                raise ValueError("Saved gate disagrees with rows")
            continue
        for key, value in result.items():
            if key == "passed":
                if saved[scenario][key] != value:
                    raise ValueError("Saved scenario gate disagrees with rows")
            elif not np.isclose(saved[scenario][key], value, rtol=0, atol=1e-9):
                raise ValueError("Saved scenario aggregate disagrees with rows")
    return dict(rows=len(rows), exact_signs=len(rows) * 4,
                passed_scenarios=sum(summary[s]["passed"] for s in SCENARIOS),
                gate_pass=summary["gate_pass"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="experiments/cell_permutation_probe/results_reference")
    args = parser.parse_args()
    print(json.dumps(audit(args.input), indent=2))
