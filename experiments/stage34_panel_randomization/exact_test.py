"""Exact blocked randomization test for Stage 33's four-rater panel design.

Under the sharp no-companion-effect null, each observed judge/document A/B
preference is fixed as the context labels permute within that document.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path


ALLOCATIONS = tuple(combinations(range(4), 2))


def exact_pvalue(blocks):
    """Exact two-sided randomization tail; every block has four (Y, treated)."""
    blocks = list(blocks)
    if not blocks:
        raise ValueError("At least one document is required")
    distribution = Counter({0: 1})
    observed = 0
    for block in blocks:
        block = list(block)
        if (len(block) != 4 or sorted(int(flag) for _, flag in block) !=
                [0, 0, 1, 1] or any(y not in (-1, 0, 1) for y, _ in block)):
            raise ValueError("Require four outcomes and two judges per context")
        y = [value for value, _ in block]
        total = sum(y)
        treated = sum(value for value, flag in block if flag)
        observed += 2 * treated - total  # 2 * per-document mean difference.
        local = Counter(2 * sum(y[j] for j in chosen) - total
                        for chosen in ALLOCATIONS)
        next_dist = Counter()
        for old, old_count in distribution.items():
            for shift, multiplicity in local.items():
                next_dist[old + shift] += old_count * multiplicity
        distribution = next_dist
    denominator = 6 ** len(blocks)
    if sum(distribution.values()) != denominator:
        raise AssertionError("Some random assignments were lost")
    numerator = sum(count for value, count in distribution.items()
                    if abs(value) >= abs(observed))
    return dict(documents=len(blocks), mean_effect=observed / (2 * len(blocks)),
                two_sided_p=numerator / denominator,
                tail_assignments=str(numerator), total_assignments=str(denominator),
                sharp_null="no companion effect on A/B preference at fixed A/B positions")


def analyze_rows(key, responses):
    if not key or not responses:
        raise ValueError("Assignments and responses must be nonempty")
    task_ids = [row["task_id"] for row in key]
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("Duplicate private-key task ID")
    by_task = {row["task_id"]: row for row in responses}
    if len(by_task) != len(responses) or set(by_task) != set(task_ids):
        raise ValueError("Missing, duplicate or extra responses")
    by_item = defaultdict(list)
    raters = defaultdict(set)
    for assignment in key:
        r = by_task[assignment["task_id"]]
        item = assignment["item_id"]
        context = assignment["context"]
        judge = assignment["rater_id"]
        if context not in ("P0", "P1") or judge != r["rater_id"] or not judge:
            raise ValueError("Wrong panel or rater")
        if judge in raters[item]:
            raise ValueError("A judge saw the same input twice")
        raters[item].add(judge)
        slots = [assignment[f"slot_{i}"] for i in range(1, 6)]
        if len(set(slots)) != 5 or "A" not in slots or "B" not in slots:
            raise ValueError("A/B must appear once in a five-way panel")
        try:
            ranks = [int(r[f"rank_{i}"]) for i in range(1, 6)]
            seconds = float(r["seconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Missing rank or duration") from exc
        if any(x not in (1, 2, 3, 4, 5) for x in ranks) or not 0 < seconds < 3600:
            raise ValueError("Invalid rank or task duration")
        a, b = ranks[slots.index("A")], ranks[slots.index("B")]
        y = int((a < b) - (a > b))
        by_item[item].append((y, context == "P1"))
    if any(len(block) != 4 for block in by_item.values()):
        raise ValueError("Every document needs four distinct judges")
    return exact_pvalue(by_item.values())


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", required=True)
    parser.add_argument("--responses", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = analyze_rows(read_csv(args.key), read_csv(args.responses))
    display = json.dumps(result, indent=2) + "\n"
    if args.output:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(display)
    print(display)
