"""Analyze recorded five-way panel judgments after all responses are complete."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from audit_legacy_panels import interval


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def analyze(key: list[dict], responses: list[dict], draws: int = 2000) -> dict:
    if not key or not responses:
        raise ValueError("no assignments or responses")
    task_ids = [k["task_id"] for k in key]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("duplicate private-key task")
    by_id = {r["task_id"]: r for r in responses}
    if len(by_id) != len(responses) or set(by_id) != set(task_ids):
        raise ValueError("missing, duplicate, or extra responses")
    grouped = defaultdict(lambda: defaultdict(list))
    rater_by_item = defaultdict(set)
    time_by_context = defaultdict(list)
    for assignment in key:
        r = by_id[assignment["task_id"]]
        item, context = assignment["item_id"], assignment["context"]
        if context not in ("P0", "P1") or r["rater_id"] != assignment["rater_id"]:
            raise ValueError("wrong rater or companion context")
        if r["rater_id"] in rater_by_item[item]:
            raise ValueError("rater saw the same source twice")
        rater_by_item[item].add(r["rater_id"])
        slots = [assignment[f"slot_{i}"] for i in range(1, 6)]
        if len(set(slots)) != 5 or "A" not in slots or "B" not in slots:
            raise ValueError("invalid five-way panel")
        try:
            ranks = [int(r[f"rank_{i}"]) for i in range(1, 6)]
            seconds = float(r["seconds"])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("incomplete ranking or duration") from exc
        if any(v not in (1, 2, 3, 4, 5) for v in ranks) or not 0 < seconds < 3600:
            raise ValueError("ranks must be 1..5; duration must be 0..3600 seconds")
        ra, rb = ranks[slots.index("A")], ranks[slots.index("B")]
        grouped[item][context].append((rb > ra) - (rb < ra))
        time_by_context[context].append(seconds)
    cells = []
    for item, contexts in grouped.items():
        if set(contexts) != {"P0", "P1"}:
            raise ValueError("each item requires both contexts")
        mean = lambda xs: sum(xs) / len(xs)
        cells.append((("pilot", "pilot", item),
                      mean(contexts["P1"]) - mean(contexts["P0"])))
    result = interval(cells, draws=draws)
    return {"contrast": "P1 minus P0 in A-over-B signed rank",
            "items": len(grouped), "judgments": len(key),
            "effect": result, "mean_task_seconds": {
                c: sum(t) / len(t) for c, t in time_by_context.items()},
            "status": "complete response file; verify human provenance and recruitment separately"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--responses", required=True, type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(read_csv(args.key), read_csv(args.responses))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
