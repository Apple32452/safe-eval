"""Audit the annotation structure of the frozen, verified WMT25 source.

This is a descriptive audit. It does not estimate sampling uncertainty or
claim that the annotators are a random sample of future annotators.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage16"))
from prepare_wmt25 import (LFS_BYTES, LFS_SHA256, SOURCE_URL, build_matrices,
                           parse_jsonl)

CONTROL_BYTES = 17796659
CONTROL_SHA256 = "bdbf27700af9ec457ae7f81acfd301cd54503b8e5660c6cac5f7c33c9683f9fa"
CONTROL_URL = SOURCE_URL.replace("humeval.jsonl", "humeval_control.jsonl")


def summarize(records, matrices):
    """Count raters, repeated ratings, and within-item cross-system overlap."""
    rows = []
    for language, (matrix, systems, items) in sorted(matrices.items()):
        counts = Counter()
        score_absolute_difference = 0.0
        same_rater_absolute_difference = 0.0
        distinct_rater_absolute_difference = 0.0
        cell_ratings = Counter()
        distinct_cell_raters = Counter()
        rater_cells = defaultdict(set)
        rater_items = defaultdict(set)
        first_scores = np.empty((len(systems), len(items)))
        second_scores = np.empty_like(first_scores)
        for item_index, item in enumerate(items):
            scores = records[language][str(item)]
            rater_sets = []
            for system_index, system in enumerate(systems):
                annotations = scores[str(system)]
                if len(annotations) != 2:
                    raise ValueError("The slot sensitivity requires exactly two ratings per cell")
                first_scores[system_index, item_index] = annotations[0]["score"]
                second_scores[system_index, item_index] = annotations[1]["score"]
                raters = [a.get("annotator") for a in annotations]
                if any(not isinstance(r, str) or not r.strip() for r in raters):
                    counts["cells_missing_annotator"] += 1
                identified = {r for r in raters if isinstance(r, str) and r.strip()}
                rater_sets.append(identified)
                counts["cells"] += 1
                counts["ratings"] += len(annotations)
                counts["cells_with_two_ratings"] += len(annotations) >= 2
                counts["cells_with_two_raters"] += len(identified) >= 2
                counts["cells_with_same_rater_repeated"] += len(raters) != len(set(raters))
                if len(annotations) == 2:
                    gap = abs(annotations[0]["score"] - annotations[1]["score"])
                    score_absolute_difference += gap
                    counts["cells_with_score_disagreement"] += gap > 0
                    if len(identified) == 1:
                        same_rater_absolute_difference += gap
                    elif len(identified) == 2:
                        distinct_rater_absolute_difference += gap
                cell_ratings[len(annotations)] += 1
                distinct_cell_raters[len(identified)] += 1
                for r in identified:
                    rater_cells[r].add((str(system), str(item)))
                    rater_items[r].add(str(item))
            for first in range(len(rater_sets)):
                for second in range(first + 1, len(rater_sets)):
                    counts["pair_items"] += 1
                    counts["pair_items_shared_rater"] += bool(rater_sets[first] & rater_sets[second])
        counts["raters"] = len(rater_cells)
        counts["raters_multiple_cells"] = sum(len(v) >= 2 for v in rater_cells.values())
        counts["raters_multiple_items"] = sum(len(v) >= 2 for v in rater_items.values())
        a, b = np.triu_indices(len(systems), 1)
        first_gap = first_scores.sum(axis=1)[a] - first_scores.sum(axis=1)[b]
        second_gap = second_scores.sum(axis=1)[a] - second_scores.sum(axis=1)[b]
        first_sign = np.sign(first_gap)
        second_sign = np.sign(second_gap)
        mean_sign = np.sign(first_gap + second_gap)
        counts["pair_first_second_opposite"] = int(np.sum(first_sign * second_sign < 0))
        counts["pair_slot_tie"] = int(np.sum((first_sign == 0) | (second_sign == 0)))
        counts["pair_mean_tie"] = int(np.sum(mean_sign == 0))
        counts["pair_one_slot_disagrees_mean"] = int(np.sum(
            (mean_sign != 0) & ((first_sign != mean_sign) | (second_sign != mean_sign))))
        rows.append(dict(language=language, systems=len(systems), items=len(items),
                         pairs=len(systems) * (len(systems) - 1) // 2,
                         **counts,
                         score_absolute_difference=score_absolute_difference,
                         same_rater_absolute_difference=same_rater_absolute_difference,
                         distinct_rater_absolute_difference=distinct_rater_absolute_difference,
                         ratings_per_cell=dict(sorted(cell_ratings.items())),
                         distinct_raters_per_cell=dict(sorted(distinct_cell_raters.items()))))
    total = {k: sum(row.get(k, 0) for row in rows) for k in (
        "systems", "items", "pairs", "cells", "ratings", "cells_with_two_ratings",
        "cells_with_two_raters", "cells_with_same_rater_repeated",
        "cells_with_score_disagreement", "cells_missing_annotator",
        "pair_items", "pair_items_shared_rater", "pair_first_second_opposite",
        "pair_slot_tie", "pair_mean_tie", "pair_one_slot_disagrees_mean",
        "score_absolute_difference",
        "same_rater_absolute_difference", "distinct_rater_absolute_difference")}
    total["languages"] = len(rows)
    # IDs are language-namespaced in this file; aggregate counts by language.
    total["language_rater_ids"] = sum(row["raters"] for row in rows)
    total["language_raters_multiple_cells"] = sum(row["raters_multiple_cells"] for row in rows)
    total["language_raters_multiple_items"] = sum(row["raters_multiple_items"] for row in rows)
    return rows, total


def summarize_control(path, records, matrices):
    path = Path(path)
    if path.stat().st_size != CONTROL_BYTES:
        raise ValueError("Unexpected WMT25 control byte count")
    digest = hashlib.sha256()
    control = defaultdict(lambda: dict(items=0, ratings=0, cells=0,
                                       raters=set(), per_cell=[]))
    with path.open("rb") as stream:
        for line in stream:
            digest.update(line)
            row = json.loads(line)
            language = row["doc_id"].split("_#_", 1)[0]
            if language not in matrices:
                continue
            control[language]["items"] += 1
            for annotations in row["scores"].values():
                ids = set()
                for annotation in annotations:
                    score = annotation["human"]
                    rater = annotation["annotator"]
                    if not isinstance(score, (int, float)) or not 0 <= score <= 100:
                        raise ValueError("Invalid WMT25 control score")
                    if not isinstance(rater, str) or not rater.strip():
                        raise ValueError("Missing WMT25 control annotator")
                    ids.add(rater)
                control[language]["ratings"] += len(annotations)
                control[language]["cells"] += 1
                control[language]["raters"].update(ids)
                control[language]["per_cell"].append(len(ids))
    if digest.hexdigest() != CONTROL_SHA256:
        raise ValueError("Unexpected WMT25 control SHA256")
    rows = []
    for language, (_, systems, items) in sorted(matrices.items()):
        main_ids = {annotation["annotator"] for item in items for system in systems
                    for annotation in records[language][str(item)][str(system)]}
        observed = control[language]
        ids = observed["raters"]
        rows.append(dict(language=language, items=observed["items"],
                         cells=observed["cells"], ratings=observed["ratings"],
                         main_raters=len(main_ids), control_raters=len(ids),
                         main_raters_on_controls=len(main_ids & ids),
                         main_raters_missing_controls=len(main_ids - ids),
                         min_distinct_raters_per_control_cell=min(observed["per_cell"]),
                         max_distinct_raters_per_control_cell=max(observed["per_cell"])))
    return dict(source_url=CONTROL_URL, source_sha256=CONTROL_SHA256,
                source_bytes=CONTROL_BYTES,
                totals={key: sum(row[key] for row in rows) for key in (
                    "items", "cells", "ratings", "main_raters", "control_raters",
                    "main_raters_on_controls", "main_raters_missing_controls")},
                by_language=rows)


def run(source, output, control_source=None):
    records, lines = parse_jsonl(source)  # checks the complete byte count and SHA256
    matrices, report = build_matrices(records)
    rows, total = summarize(records, matrices)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    payload = dict(source_url=SOURCE_URL, source_bytes=LFS_BYTES,
                   source_sha256=LFS_SHA256, jsonl_lines=lines,
                   inclusion="Stage 16 maximum-coverage systems and common items",
                   estimand="Descriptive annotation structure of the fixed WMT25 file",
                   total=total, by_language=rows,
                   excluded=[r for r in report if not r["included"]])
    if control_source is not None:
        payload["shared_controls"] = summarize_control(control_source, records, matrices)
    (output / "RATER_AUDIT.json").write_text(json.dumps(payload, indent=2) + "\n")
    fields = [k for k in rows[0] if k not in ("ratings_per_cell", "distinct_raters_per_cell")]
    with (output / "by_language.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row.get(k, 0) for k in fields} for row in rows)
    print(json.dumps(total, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--control-source")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.source, args.output, args.control_source)
