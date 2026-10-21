"""Audit Stage 18 accounting and compare with the frozen Stage 17 candidate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage14"))
from shared_pilot import FRACTIONS
from run_stage18 import METHOD


def read_rows(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def record(row):
    return {
        key: int(row[key])
        for key in (
            "pairs",
            "systems",
            "items",
            "budget",
            "labels",
            "correct",
            "wrong",
            "unresolved",
            "reached_prefix",
            "resolved_pairs",
        )
    }


def stats(values):
    mean = sum(values) / len(values)
    mcse = (
        (sum((value - mean) ** 2 for value in values) / (len(values) - 1) / len(values))
        ** 0.5
        if len(values) > 1
        else None
    )
    return dict(
        mean=mean,
        conditional_repeat_mcse=round(mcse, 12) if mcse is not None else None,
        wins=sum(value > 0 for value in values),
        ties=sum(value == 0 for value in values),
        losses=sum(value < 0 for value in values),
        values=values,
    )


def summarize(directory, stage17_directory):
    directory = Path(directory)
    stage17_directory = Path(stage17_directory)
    payload = (directory / "replicates.csv").read_bytes()
    rows = list(csv.DictReader(payload.decode().splitlines()))
    metadata = json.loads((directory / "metadata.json").read_text())
    stage17_payload = (stage17_directory / "replicates.csv").read_bytes()
    if hashlib.sha256(stage17_payload).hexdigest() != metadata["stage17_replicates_sha256"]:
        raise ValueError("Stage 17 candidate differs from the frozen reference")
    stage17_rows = list(csv.DictReader(stage17_payload.decode().splitlines()))

    baseline = {}
    for row in rows:
        if row["method"] != METHOD:
            raise ValueError("Unexpected Stage 18 method")
        key = (row["language"], int(row["repeat"]), float(row["fraction"]))
        if key in baseline:
            raise ValueError("Duplicate baseline result")
        value = record(row)
        if value["correct"] + value["wrong"] + value["unresolved"] != value["pairs"]:
            raise ValueError("Pair accounting failed")
        if value["resolved_pairs"] != value["correct"] + value["wrong"]:
            raise ValueError("Resolved-pair accounting failed")
        if value["budget"] != int(float(row["fraction"]) * value["systems"] * value["items"]):
            raise ValueError("Budget accounting failed")
        if not 0 <= value["labels"] <= value["budget"]:
            raise ValueError("Label accounting failed")
        baseline[key] = value

    expected = {
        (language, repeat, fraction)
        for language in metadata["languages"]
        for repeat in range(metadata["repeats"])
        for fraction in FRACTIONS
    }
    if set(baseline) != expected:
        raise ValueError("Incomplete Stage 18 grid")

    candidate = {}
    for row in stage17_rows:
        if row["method"] != "frontier_evidence":
            continue
        key = (row["language"], int(row["repeat"]), float(row["fraction"]))
        if key in expected:
            candidate[key] = record(row)
    if set(candidate) != expected:
        raise ValueError("Stage 17 candidate grid does not match Stage 18")
    for key in expected:
        for field in ("pairs", "systems", "items", "budget"):
            if baseline[key][field] != candidate[key][field]:
                raise ValueError("Candidate/control design mismatch: " + field)

    for language in metadata["languages"]:
        for repeat in range(metadata["repeats"]):
            sequence = [baseline[language, repeat, fraction] for fraction in FRACTIONS]
            for field in ("labels", "correct", "wrong", "resolved_pairs", "reached_prefix"):
                values = [value[field] for value in sequence]
                if values != sorted(values):
                    raise ValueError("Nonmonotone baseline " + field)

    result = dict(
        status="passed",
        rows=len(rows),
        languages=metadata["languages"],
        repeats=metadata["repeats"],
        baseline=METHOD,
        replicates_sha256=hashlib.sha256(payload).hexdigest(),
        stage17_replicates_sha256=hashlib.sha256(stage17_payload).hexdigest(),
        aggregate={},
        by_language={},
    )
    for fraction in FRACTIONS:
        candidate_totals = [
            sum(candidate[language, repeat, fraction]["correct"] for language in metadata["languages"])
            for repeat in range(metadata["repeats"])
        ]
        baseline_totals = [
            sum(baseline[language, repeat, fraction]["correct"] for language in metadata["languages"])
            for repeat in range(metadata["repeats"])
        ]
        differences = [a - b for a, b in zip(candidate_totals, baseline_totals)]
        candidate_mean = sum(candidate_totals) / len(candidate_totals)
        baseline_mean = sum(baseline_totals) / len(baseline_totals)
        result["aggregate"][str(fraction)] = dict(
            frontier_evidence=dict(
                mean_correct_total=candidate_mean,
                wrong_count=sum(
                    candidate[key]["wrong"] for key in expected if key[2] == fraction
                ),
            ),
            common_random_items=dict(
                mean_correct_total=baseline_mean,
                wrong_count=sum(
                    baseline[key]["wrong"] for key in expected if key[2] == fraction
                ),
            ),
            frontier_minus_common=stats(differences),
            relative_gain_percent=(
                100 * (candidate_mean - baseline_mean) / baseline_mean
                if baseline_mean
                else math.inf
            ),
        )
    for language in metadata["languages"]:
        result["by_language"][language] = {}
        for fraction in FRACTIONS:
            differences = [
                candidate[language, repeat, fraction]["correct"]
                - baseline[language, repeat, fraction]["correct"]
                for repeat in range(metadata["repeats"])
            ]
            result["by_language"][language][str(fraction)] = stats(differences)

    primary = result["aggregate"]["0.75"]
    comparison = primary["frontier_minus_common"]
    positive_languages = sum(
        result["by_language"][language]["0.75"]["mean"] > 0
        for language in metadata["languages"]
    )
    candidate_wrong = primary["frontier_evidence"]["wrong_count"]
    baseline_wrong = primary["common_random_items"]["wrong_count"]
    mcse = comparison["conditional_repeat_mcse"]
    gate = (
        comparison["mean"] > 0
        and mcse is not None
        and comparison["mean"] > 2 * mcse
        and positive_languages > len(metadata["languages"]) / 2
        and candidate_wrong <= baseline_wrong
    )
    result["development_gate"] = dict(
        passed=gate,
        comparison=comparison,
        exceeds_two_mcse=(mcse is not None and comparison["mean"] > 2 * mcse),
        positive_languages=positive_languages,
        included_languages=len(metadata["languages"]),
        frontier_wrong=candidate_wrong,
        baseline_wrong=baseline_wrong,
    )
    (directory / "SUMMARY.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["development_gate"], indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--stage17", default="experiments/stage17/results_reference"
    )
    arguments = parser.parse_args()
    summarize(arguments.input, arguments.stage17)
