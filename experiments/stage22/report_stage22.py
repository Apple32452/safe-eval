"""Create compact post-run Stage 22 tables from audited full outputs."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def mean(values):
    return sum(values) / len(values)


def write_rows(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)


def aggregate(directory, output):
    directory = Path(directory)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows = list(csv.DictReader((directory / "comparison.csv").open()))
    checkpoints = list(csv.DictReader((directory / "checkpoints.csv").open()))
    summary = json.loads((directory / "SUMMARY.json").read_text())
    primary = [row for row in rows if row["graph"] == "star"]

    by_language = []
    for language in sorted({row["language"] for row in primary}):
        selected = [row for row in primary if row["language"] == language]
        relative = [float(row["relative_saving"]) for row in selected]
        by_language.append(dict(
            language=language, tasks=len(selected),
            mean_common_cost=mean([float(row["common_cost"]) for row in selected]),
            mean_pruned_cost=mean([float(row["pruned_cost"]) for row in selected]),
            mean_absolute_saving=mean([float(row["absolute_saving"]) for row in selected]),
            mean_relative_saving=mean(relative),
            minimum_relative_saving=min(relative),
            maximum_relative_saving=max(relative),
        ))
    write_rows(output / "primary_by_language.csv", by_language)

    by_reference = []
    keys = sorted({(row["language"], row["reference"], row["reference_name"])
                   for row in primary})
    for language, reference, reference_name in keys:
        selected = [row for row in primary if
                    (row["language"], row["reference"], row["reference_name"]) ==
                    (language, reference, reference_name)]
        relative = [float(row["relative_saving"]) for row in selected]
        by_reference.append(dict(
            language=language, reference=int(reference), reference_name=reference_name,
            repeats=len(selected),
            mean_common_cost=mean([float(row["common_cost"]) for row in selected]),
            mean_pruned_cost=mean([float(row["pruned_cost"]) for row in selected]),
            mean_absolute_saving=mean([float(row["absolute_saving"]) for row in selected]),
            mean_relative_saving=mean(relative),
            minimum_relative_saving=min(relative),
            maximum_relative_saving=max(relative),
        ))
    write_rows(output / "primary_by_reference.csv", by_reference)

    checkpoint_summary = []
    for fraction in ("0.25", "0.5", "0.75"):
        for method in ("star_common", "star_pruned"):
            selected = [row for row in checkpoints if row["graph"] == "star" and
                        row["fraction"] == fraction and row["method"] == method]
            language_repeat = defaultdict(list)
            for row in selected:
                language_repeat[int(row["repeat"]), row["language"]].append(row)
            record = dict(fraction=float(fraction), method=method,
                          blocks=len(language_repeat))
            for field in ("labels", "correct", "wrong", "unresolved"):
                record["mean_" + field] = mean([
                    mean([float(row[field]) for row in block])
                    for block in language_repeat.values()
                ])
            checkpoint_summary.append(record)
    write_rows(output / "checkpoint_summary.csv", checkpoint_summary)

    diagnostics = [dict(graph=graph, **values)
                   for graph, values in summary["diagnostics"].items()]
    write_rows(output / "diagnostics.csv", diagnostics)
    repeat_rows = [dict(repeat=index, mean_relative_saving=value)
                   for index, value in enumerate(
                       summary["primary"]["repeat_block_means"])]
    write_rows(output / "primary_repeat_blocks.csv", repeat_rows)

    for name in ("SUMMARY.json", "VERIFICATION.json", "metadata.json"):
        (output / name).write_bytes((directory / name).read_bytes())
    print(f"Wrote {len(by_language)} language, {len(by_reference)} reference, "
          f"{len(checkpoint_summary)} checkpoint, and {len(diagnostics)} diagnostic rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    aggregate(arguments.input, arguments.output)
