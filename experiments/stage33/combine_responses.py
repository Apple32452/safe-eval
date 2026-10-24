"""Merge completed private rater CSVs against the frozen response template."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


COLUMNS = ["task_id", "rater_id", "task_order",
           *[f"rank_{i}" for i in range(1, 6)], "seconds"]


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"Unexpected response columns in {path}")
        return list(reader)


def combine(template: Path, response_files: list[Path], output: Path) -> int:
    if not response_files:
        raise ValueError("Provide rater response CSVs")
    expected = read_rows(template)
    keyed = {row["task_id"]: row for row in expected}
    if len(keyed) != len(expected):
        raise ValueError("Duplicate task ID in template")
    collected = {}
    for path in response_files:
        rows = read_rows(path)
        if not rows:
            raise ValueError(f"Empty response file: {path}")
        if len({row["rater_id"] for row in rows}) != 1:
            raise ValueError(f"Rater file contains multiple rater IDs: {path}")
        for row in rows:
            tid = row["task_id"]
            if tid in collected or tid not in keyed:
                raise ValueError(f"Duplicate or unexpected response task: {tid}")
            if (row["rater_id"], row["task_order"]) != (
                    keyed[tid]["rater_id"], keyed[tid]["task_order"]):
                raise ValueError(f"Rater or order disagrees with assignment: {tid}")
            try:
                ranks = [int(row[f"rank_{i}"]) for i in range(1, 6)]
                seconds = float(row["seconds"])
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Missing rank or task time: {tid}") from exc
            if any(rank not in range(1, 6) for rank in ranks) or not (0 < seconds < 3600):
                raise ValueError(f"Invalid rank or task time: {tid}")
            collected[tid] = row
    missing = set(keyed) - set(collected)
    if missing:
        raise ValueError(f"Missing {len(missing)} tasks; no combined output written")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(collected[row["task_id"]] for row in expected)
    return len(expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--responses", required=True, nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(f"Combined {combine(args.template, args.responses, args.output)} complete responses.")
