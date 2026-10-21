"""Validate and summarize saved Stage 22 graph comparisons."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def _mean(values):
    return sum(values) / len(values)


def _mcse(values):
    mean = _mean(values)
    return (sum((value - mean) ** 2 for value in values) /
            (len(values) - 1) / len(values)) ** .5 if len(values) > 1 else None


def summarize(directory):
    directory = Path(directory)
    comparison_bytes = (directory / "comparison.csv").read_bytes()
    checkpoint_bytes = (directory / "checkpoints.csv").read_bytes()
    rows = list(csv.DictReader(comparison_bytes.decode().splitlines()))
    checkpoints = list(csv.DictReader(checkpoint_bytes.decode().splitlines()))
    metadata = json.loads((directory / "metadata.json").read_text())

    numeric_int = (
        "repeat", "reference", "systems", "items", "edges", "common_cost",
        "pruned_cost", "absolute_saving", "edge_dominance_violations",
        "max_pruned_minus_common_edge_cost", "final_decision_disagreements",
        "positive_edges", "negative_edges", "tied_edges", "min_active_systems",
    )
    indexed = {}
    for raw in rows:
        row = dict(raw)
        for key in numeric_int:
            row[key] = int(row[key])
        for key in ("relative_saving", "mean_active_systems"):
            row[key] = float(row[key])
        identity = (row["language"], row["repeat"], row["graph"], row["task_id"])
        if identity in indexed:
            raise ValueError("Duplicate graph task result")
        if row["pruned_cost"] > row["common_cost"] or row["absolute_saving"] < 0:
            raise ValueError("Pathwise total-cost dominance failed")
        if row["edge_dominance_violations"] or row["final_decision_disagreements"]:
            raise ValueError("Edge dominance or final agreement failed")
        if row["max_pruned_minus_common_edge_cost"] > 0:
            raise ValueError("A pruned edge resolved later than its control")
        expected_relative = row["absolute_saving"] / row["common_cost"]
        if abs(row["relative_saving"] - expected_relative) > 1e-12:
            raise ValueError("Relative saving does not match saved costs")
        indexed[identity] = row

    checkpoint_index = {}
    for raw in checkpoints:
        row = dict(raw)
        identity = (
            row["language"], int(row["repeat"]), row["graph"], row["task_id"],
            row["method"], float(row["fraction"]),
        )
        if identity in checkpoint_index:
            raise ValueError("Duplicate checkpoint result")
        integers = {key: int(row[key]) for key in
                    ("systems", "items", "edges", "budget", "labels", "correct",
                     "wrong", "unresolved", "reached_prefix", "resolved_pairs")}
        if integers["correct"] + integers["wrong"] + integers["unresolved"] != integers["edges"]:
            raise ValueError("Checkpoint edge accounting failed")
        expected_budget = int(float(row["fraction"]) * integers["systems"] * integers["items"])
        if integers["budget"] != expected_budget or integers["labels"] > integers["budget"]:
            raise ValueError("Checkpoint label budget failed")
        if integers["labels"] < integers["budget"] and integers["unresolved"]:
            raise ValueError("A policy stopped below budget with unresolved edges")
        checkpoint_index[identity] = integers

    expected_rows = sum(
        metadata["repeats"] * metadata["task_counts"][language]
        for language in metadata["languages"]
    )
    if len(rows) != expected_rows or len(checkpoints) != expected_rows * 6:
        raise ValueError("Incomplete task or checkpoint grid")
    for language, repeat, graph, task_id in indexed:
        for fraction in metadata["fractions"]:
            common = checkpoint_index[
                language, repeat, graph, task_id, "star_common", fraction
            ]
            pruned = checkpoint_index[
                language, repeat, graph, task_id, "star_pruned", fraction
            ]
            if pruned["resolved_pairs"] < common["resolved_pairs"]:
                raise ValueError("Checkpoint resolved-edge dominance failed")

    primary = [row for row in indexed.values() if row["graph"] == "star"]
    per_repeat = []
    for repeat in range(metadata["repeats"]):
        language_values = []
        for language in metadata["languages"]:
            values = [row["relative_saving"] for row in primary
                      if row["repeat"] == repeat and row["language"] == language]
            if len(values) != metadata["systems"][language]:
                raise ValueError("Primary reference suite is incomplete")
            language_values.append(_mean(values))
        per_repeat.append(_mean(language_values))

    language_means = {
        language: _mean([row["relative_saving"] for row in primary
                         if row["language"] == language])
        for language in metadata["languages"]
    }
    mean_saving = _mean(per_repeat)
    mcse = _mcse(per_repeat)
    positive_languages = sum(value > 0 for value in language_means.values())

    diagnostics = {}
    for graph in ("ring1", "ring2", "complete"):
        values = [row["relative_saving"] for row in indexed.values()
                  if row["graph"] == graph]
        if values:
            diagnostics[graph] = dict(
                mean_relative_saving=_mean(values),
                minimum_relative_saving=min(values),
                maximum_relative_saving=max(values),
            )

    gate = dict(
        mean_at_least_ten_percent=mean_saving >= .10,
        exceeds_two_mcse=(mcse is not None and mean_saving > 2 * mcse),
        majority_languages_positive=positive_languages > len(language_means) / 2,
        exact_final_agreement=all(
            row["final_decision_disagreements"] == 0 for row in indexed.values()
        ),
        pathwise_edge_dominance=all(
            row["edge_dominance_violations"] == 0 for row in indexed.values()
        ),
    )
    result = dict(
        status="passed", rows=len(rows), checkpoint_rows=len(checkpoints),
        repeats=metadata["repeats"], languages=metadata["languages"],
        primary=dict(
            tasks=len(primary), mean_relative_label_saving=mean_saving,
            conditional_repeat_mcse=mcse,
            positive_language_means=positive_languages,
            total_languages=len(language_means), language_means=language_means,
            repeat_block_means=per_repeat,
            minimum_task_saving=min(row["relative_saving"] for row in primary),
            maximum_task_saving=max(row["relative_saving"] for row in primary),
        ),
        diagnostics=diagnostics, gate=gate,
        development_gate_passed=all(gate.values()),
        comparison_sha256=hashlib.sha256(comparison_bytes).hexdigest(),
        checkpoints_sha256=hashlib.sha256(checkpoint_bytes).hexdigest(),
    )
    (directory / "SUMMARY.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"primary": result["primary"], "gate": gate,
                      "development_gate_passed": result["development_gate_passed"]},
                     indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    summarize(parser.parse_args().input)
