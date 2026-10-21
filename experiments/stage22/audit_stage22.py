"""Independent accounting and repeat-zero replay for Stage 22."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_stage22 import run, verify_lock


def _canonical(row):
    return tuple((key, str(value)) for key, value in sorted(row.items()))


def audit(directory, data_directory):
    directory = Path(directory)
    verify_lock()
    metadata = json.loads((directory / "metadata.json").read_text())
    saved_comparison = list(csv.DictReader((directory / "comparison.csv").open()))
    saved_checkpoints = list(csv.DictReader((directory / "checkpoints.csv").open()))

    seen = set()
    violations = 0
    for row in saved_comparison:
        identity = (row["language"], int(row["repeat"]), row["graph"], row["task_id"])
        if identity in seen:
            raise ValueError("Duplicate saved comparison row")
        seen.add(identity)
        violations += int(row["edge_dominance_violations"])
        if int(row["pruned_cost"]) > int(row["common_cost"]):
            raise ValueError("Saved total-cost dominance failure")
        if int(row["final_decision_disagreements"]):
            raise ValueError("Saved final-decision disagreement")
    if violations:
        raise ValueError("Saved per-edge dominance failure")

    checkpoint_index = {}
    for row in saved_checkpoints:
        identity = (
            row["language"], int(row["repeat"]), row["graph"], row["task_id"],
            row["method"], float(row["fraction"]),
        )
        if identity in checkpoint_index:
            raise ValueError("Duplicate saved checkpoint row")
        values = {key: int(row[key]) for key in
                  ("systems", "items", "edges", "budget", "labels", "correct",
                   "wrong", "unresolved", "reached_prefix", "resolved_pairs")}
        if values["correct"] + values["wrong"] + values["unresolved"] != values["edges"]:
            raise ValueError("Saved checkpoint edge accounting failure")
        expected_budget = int(float(row["fraction"]) * values["systems"] * values["items"])
        if values["budget"] != expected_budget or values["labels"] > values["budget"]:
            raise ValueError("Saved checkpoint budget failure")
        checkpoint_index[identity] = values
    for language, repeat, graph, task_id in seen:
        for fraction in metadata["fractions"]:
            common = checkpoint_index[
                language, repeat, graph, task_id, "star_common", fraction
            ]
            pruned = checkpoint_index[
                language, repeat, graph, task_id, "star_pruned", fraction
            ]
            if pruned["resolved_pairs"] < common["resolved_pairs"]:
                raise ValueError("Saved checkpoint pathwise dominance failure")

    replay_comparison, replay_checkpoints, replay_metadata = run(
        data_directory, repeats=1, languages=metadata["languages"],
        include_diagnostics=metadata["include_diagnostics"]
    )
    expected_comparison = [row for row in saved_comparison if int(row["repeat"]) == 0]
    expected_checkpoints = [row for row in saved_checkpoints if int(row["repeat"]) == 0]
    if sorted(map(_canonical, expected_comparison)) != sorted(
        map(_canonical, replay_comparison)
    ):
        raise ValueError("Repeat-zero comparison replay mismatch")
    if sorted(map(_canonical, expected_checkpoints)) != sorted(
        map(_canonical, replay_checkpoints)
    ):
        raise ValueError("Repeat-zero checkpoint replay mismatch")
    if replay_metadata["matrix_hashes"] != metadata["matrix_hashes"]:
        raise ValueError("Replay matrix hashes changed")

    report = dict(
        status="passed", comparison_rows=len(saved_comparison),
        checkpoint_rows=len(saved_checkpoints),
        replayed_comparison_rows=len(replay_comparison),
        replayed_checkpoint_rows=len(replay_checkpoints),
        edge_dominance_violations=violations,
        comparison_sha256=hashlib.sha256(
            (directory / "comparison.csv").read_bytes()).hexdigest(),
        checkpoints_sha256=hashlib.sha256(
            (directory / "checkpoints.csv").read_bytes()).hexdigest(),
    )
    (directory / "VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--data", required=True)
    arguments = parser.parse_args()
    audit(arguments.input, arguments.data)
