"""Merge disjoint language shards without changing saved Stage 22 values."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def merge(inputs, output):
    inputs = [Path(path) for path in inputs]
    if len(inputs) < 2:
        raise ValueError("At least two shard directories are required")
    metadata_rows = [json.loads((path / "metadata.json").read_text()) for path in inputs]
    fixed_keys = ("master", "repeats", "include_diagnostics", "methods",
                  "fractions", "protocol_sha256", "source_sha256")
    first = metadata_rows[0]
    for metadata in metadata_rows[1:]:
        if any(metadata[key] != first[key] for key in fixed_keys):
            raise ValueError("Shard metadata disagree")
    languages = [language for metadata in metadata_rows
                 for language in metadata["languages"]]
    if len(languages) != len(set(languages)):
        raise ValueError("Language shards overlap")

    comparison = []
    checkpoints = []
    for path in inputs:
        with (path / "comparison.csv").open() as stream:
            comparison.extend(csv.DictReader(stream))
        with (path / "checkpoints.csv").open() as stream:
            checkpoints.extend(csv.DictReader(stream))
    comparison.sort(key=lambda row: (
        row["language"], int(row["repeat"]), row["graph"], row["task_id"]
    ))
    checkpoints.sort(key=lambda row: (
        row["language"], int(row["repeat"]), row["graph"], row["task_id"],
        row["method"], float(row["fraction"])
    ))
    if len({(row["language"], row["repeat"], row["graph"], row["task_id"])
            for row in comparison}) != len(comparison):
        raise ValueError("Duplicate comparison rows across shards")

    combined = dict(first)
    combined["languages"] = sorted(languages)
    for key in ("matrix_hashes", "systems", "task_counts"):
        combined[key] = {}
        for metadata in metadata_rows:
            overlap = set(combined[key]) & set(metadata[key])
            if overlap:
                raise ValueError("Overlapping shard metadata: " + key)
            combined[key].update(metadata[key])
    combined["execution"] = dict(
        mode="disjoint_language_shards",
        shard_count=len(inputs),
        amendment="experiments/stage22/AMENDMENT_1.md",
    )

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "comparison.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=comparison[0].keys())
        writer.writeheader(); writer.writerows(comparison)
    with (output / "checkpoints.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=checkpoints[0].keys())
        writer.writeheader(); writer.writerows(checkpoints)
    (output / "metadata.json").write_text(json.dumps(combined, indent=2) + "\n")
    print(f"Merged {len(comparison)} graph tasks and {len(checkpoints)} checkpoints "
          f"from {len(inputs)} language shards.")
    return comparison, checkpoints, combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    merge(arguments.inputs, arguments.output)
