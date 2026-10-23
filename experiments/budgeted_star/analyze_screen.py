"""Independent saved-row integrity and prespecified gate analysis."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
METHODS = {"pruned", "evidence_first", "footprint"}
SCENARIOS = {"independent_easy", "shared_easy", "independent_mixed", "near_ties"}
EDGES = 7
FULL = 8 * 96


def audit_and_summarize(directory):
    directory = Path(directory)
    metadata = json.loads((directory / "metadata.json").read_text())
    if metadata["protocol_sha256"] != hashlib.sha256(
            (HERE / "PROTOCOL.md").read_bytes()).hexdigest():
        raise ValueError("Protocol differs from the saved run")
    if metadata["pilot"] != 8 or metadata["alpha"] != 0.05:
        raise ValueError("Unexpected pilot or error target")
    rows = list(csv.DictReader((directory / "replicates.csv").open(newline="")))
    groups = defaultdict(dict)
    for row in rows:
        scenario, method, repeat = row["scenario"], row["method"], int(row["repeat"])
        if scenario not in SCENARIOS or method not in METHODS:
            raise ValueError("Unexpected scenario or method")
        if not 0 <= repeat < metadata["repeats"] or method in groups[(scenario, repeat)]:
            raise ValueError("Repeated or out-of-range task")
        values = {name: int(row[name]) for name in
                  ("labels", "budget", "completion_cost", "strict", "wrong",
                   "ties", "unresolved")}
        if values["budget"] != FULL // 2 or not (0 <= values["labels"] <=
                                                values["budget"]):
            raise ValueError("Budget or label accounting failed")
        if not values["labels"] <= values["completion_cost"] <= FULL:
            raise ValueError("Completion cost outside feasible range")
        if values["labels"] < values["budget"] and values["unresolved"]:
            raise ValueError("Stopped without spending budget or resolving")
        if sum(values[name] for name in ("strict", "wrong", "ties", "unresolved")) != EDGES:
            raise ValueError("Comparison categories do not partition edges")
        groups[(scenario, repeat)][method] = values
    if len(groups) != len(SCENARIOS) * metadata["repeats"] or any(
            set(value) != METHODS for value in groups.values()):
        raise ValueError("Saved paired matrix suite is incomplete")
    reports = {}
    for scenario in sorted(SCENARIOS):
        reports[scenario] = {}
        for method in sorted(METHODS):
            current = [groups[(scenario, i)][method]
                       for i in range(metadata["repeats"])]
            reports[scenario][method] = {
                key: sum(row[key] for row in current) / len(current)
                for key in ("strict", "wrong", "ties", "unresolved", "labels",
                            "completion_cost")}
        candidate = reports[scenario]["footprint"]
        baselines = [reports[scenario][control]
                     for control in ("pruned", "evidence_first")]
        reports[scenario]["pass"] = bool(all(
            baseline["strict"] > 0 and
            candidate["strict"] >= 1.1 * baseline["strict"] and
            candidate["labels"] <= baseline["labels"] and
            candidate["wrong"] <= baseline["wrong"]
            for baseline in baselines))
        reports[scenario]["paired_strict_gain"] = {
            control: (candidate["strict"] - reports[scenario][control]["strict"])
            for control in ("pruned", "evidence_first")}
    gate_count = sum(report["pass"] for report in reports.values())
    return dict(repeats=metadata["repeats"], matrices=len(groups),
                rows=len(rows), scenarios=reports, passed_scenarios=gate_count,
                gate_pass=(gate_count >= 3))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    arguments = parser.parse_args()
    result = audit_and_summarize(arguments.input)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        Path(arguments.output).write_text(serialized)
    print(serialized)
