"""Audit Stage 18 inputs, comparison, and deterministic repeat-zero replay."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "stage17"))
from prepare_scores import load_prepared
from run_stage18 import verify_lock
from summarize_stage18 import summarize


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def audit(data_directory, result_directory, stage17_directory, replay_directory=None):
    verify_lock()
    result_directory = Path(result_directory)
    datasets, provenance = load_prepared(data_directory)
    metadata = json.loads((result_directory / "metadata.json").read_text())
    observed = {
        row["language"]: row["matrix_sha256"]
        for row in provenance["reports"]
        if row["included"]
    }
    if metadata["source_sha256"] != provenance["source_sha256"]:
        raise ValueError("Result source hash differs from the frozen source")
    if metadata["matrix_hashes"] != observed or sorted(datasets) != metadata["languages"]:
        raise ValueError("Result matrices differ from prepared data")
    summary = summarize(result_directory, stage17_directory)

    replay_rows = 0
    if replay_directory is not None:
        full = read_rows(result_directory / "replicates.csv")
        replay = read_rows(Path(replay_directory) / "replicates.csv")
        full_zero = [row for row in full if int(row["repeat"]) == 0]
        key = lambda row: (row["language"], float(row["fraction"]))
        if {key(row): row for row in full_zero} != {key(row): row for row in replay}:
            raise ValueError("Repeat-zero replay differs from the frozen full run")
        replay_rows = len(replay)

    verification = dict(
        status="passed",
        implementation_lock_verified=True,
        source_sha256=provenance["source_sha256"],
        languages=len(datasets),
        result_rows=summary["rows"],
        result_grid_and_monotonicity_verified=True,
        stage17_reference_verified=True,
        repeat_zero_replay_rows=replay_rows,
        repeat_zero_exact_match=replay_directory is not None,
        development_gate=summary["development_gate"],
        replicates_sha256=sha256(result_directory / "replicates.csv"),
        metadata_sha256=sha256(result_directory / "metadata.json"),
        summary_sha256=sha256(result_directory / "SUMMARY.json"),
    )
    (result_directory / "VERIFICATION.json").write_text(
        json.dumps(verification, indent=2) + "\n"
    )
    print(json.dumps(verification, indent=2))
    return verification


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--stage17", default="experiments/stage17/results_reference")
    parser.add_argument("--repeat-zero-replay")
    arguments = parser.parse_args()
    audit(
        arguments.data,
        arguments.input,
        arguments.stage17,
        arguments.repeat_zero_replay,
    )
