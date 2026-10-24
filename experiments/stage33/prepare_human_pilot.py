"""Blind and allocate two companion panels for repeated human rankings."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


SYSTEMS = ("A", "B", "C", "D", "E", "F", "G", "H")
CONTEXTS = {"P0": ("A", "B", "C", "D", "E"),
            "P1": ("A", "B", "F", "G", "H")}
SEED = 3302


def read_items(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"item_id", "source", "reference", *SYSTEMS}
        if not required <= set(reader.fieldnames or ()):
            raise ValueError(f"item file requires {sorted(required)}")
        rows = list(reader)
    if not rows or len({r["item_id"] for r in rows}) != len(rows):
        raise ValueError("require unique nonempty items")
    if len({r["source"].strip() for r in rows}) != len(rows):
        raise ValueError("the same source cannot be assigned under different item IDs")
    for row in rows:
        if not row["item_id"] or not row["source"]:
            raise ValueError("missing item_id or source")
        if any(not row[s] for s in SYSTEMS):
            raise ValueError("missing system translation")
        if len({row[s].strip() for s in SYSTEMS}) < len(SYSTEMS):
            raise ValueError("duplicate translation text within one item")
    return rows


def read_raters(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if "rater_id" not in (reader.fieldnames or ()):
            raise ValueError("rater file requires rater_id")
        raters = [r["rater_id"] for r in reader]
    if not raters or any(not r for r in raters) or len(set(raters)) != len(raters):
        raise ValueError("require distinct nonempty pseudonymous raters")
    return raters


def build(items: list[dict], raters: list[str], repeats: int,
          seed: int = SEED) -> tuple[list[dict], list[dict]]:
    if repeats < 1 or len(raters) < 2 * repeats:
        raise ValueError("at least two independent rater IDs per repeat")
    if len({r["item_id"] for r in items}) != len(items) or len(
            {r["source"].strip() for r in items}) != len(items):
        raise ValueError("item IDs and source texts must be unique")
    rng = np.random.default_rng(seed)
    tasks, key = [], []
    for item in items:
        selected = rng.choice(raters, size=2 * repeats, replace=False)
        # Each source is seen by each selected rater in exactly one context.
        for context_idx, (context, systems) in enumerate(CONTEXTS.items()):
            for repeat in range(repeats):
                rater_id = str(selected[context_idx * repeats + repeat])
                ordered = [str(x) for x in rng.permutation(systems)]
                # Rater-visible IDs must not encode the companion context.
                identifier = f"{seed}|{item['item_id']}|{context_idx}|{repeat}"
                task_id = "t_" + hashlib.sha256(identifier.encode()).hexdigest()[:24]
                tasks.append({"task_id": task_id, "rater_id": rater_id,
                              "item_id": item["item_id"],
                              "source": item["source"],
                              "reference": item["reference"],
                              **{f"option_{k}": item[s] for k, s in
                                 enumerate(ordered, 1)}})
                key.append({"task_id": task_id, "item_id": item["item_id"],
                            "rater_id": rater_id, "context": context,
                            **{f"slot_{k}": s for k, s in
                               enumerate(ordered, 1)}})
    if len({t["task_id"] for t in tasks}) != len(tasks):
        raise ValueError("Opaque task IDs collided")
    by_rater = defaultdict(list)
    for index, task in enumerate(tasks):
        by_rater[task["rater_id"]].append(index)
    # Independent, pre-judgment order per rater; the presentation CSV is
    # sorted on these recorded orders at export time.
    for indices in by_rater.values():
        for order, at in enumerate(rng.permutation(indices), 1):
            tasks[int(at)]["task_order"] = order
            key[int(at)]["task_order"] = order
    return tasks, key


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--raters", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    items, raters = read_items(args.items), read_raters(args.raters)
    tasks, key = build(items, raters, args.repeats)
    args.output.mkdir(parents=True, exist_ok=True)
    ordered_tasks = sorted(tasks, key=lambda t: (t["rater_id"], t["task_order"]))
    write_csv(args.output / "tasks.csv", ordered_tasks,
              ["task_id", "rater_id", "task_order", "item_id", "source", "reference",
               *[f"option_{k}" for k in range(1, 6)]])
    write_csv(args.output / "private_key.csv", key,
              ["task_id", "item_id", "rater_id", "task_order", "context",
               *[f"slot_{k}" for k in range(1, 6)]])
    write_csv(args.output / "responses_template.csv",
              [{"task_id": t["task_id"], "rater_id": t["rater_id"],
                "task_order": t["task_order"],
                **{f"rank_{k}": "" for k in range(1, 6)}, "seconds": ""}
               for t in ordered_tasks],
              ["task_id", "rater_id", "task_order",
               *[f"rank_{k}" for k in range(1, 6)],
               "seconds"])
    (args.output / "manifest.json").write_text(json.dumps({
        "seed": SEED, "items": len(items), "rater_count": len(raters),
        "repeats_per_context": args.repeats, "task_count": len(tasks),
        "context_panels": CONTEXTS}, indent=2) + "\n")
    print(f"Prepared {len(tasks)} blinded tasks for {len(items)} items.")


if __name__ == "__main__":
    main()
