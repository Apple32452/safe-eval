"""Run the frozen Stage 20 active-system-pruning candidate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage18"))
sys.path.insert(0, str(HERE.parent / "stage17"))
sys.path.insert(0, str(HERE.parent / "stage14"))
from continuous_engine import make_paths
from prepare_scores import load_prepared
from run_stage17 import close_free, snapshot
from run_stage18 import MASTER, common_design
from shared_pilot import FRACTIONS

METHOD = "active_system_pruning"


def verify_lock():
    lock = json.loads((HERE / "IMPLEMENTATION_LOCK.json").read_text())
    repository = HERE.parent.parent
    for relative, expected in lock["sha256"].items():
        observed = hashlib.sha256((repository / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise ValueError("Locked source changed: " + relative)
    return lock


def simulate_pruned(
    scores, pairs, permutation, events, priority, fractions=FRACTIONS
):
    systems, items = scores.shape
    if priority.shape != scores.shape or len(np.unique(priority)) != priority.size:
        raise ValueError("Unique common label priorities required")
    if not np.all(permutation == permutation[0]):
        raise ValueError("Every pair must share the common item path")
    item_order = permutation[0]
    targets = tuple(int(np.floor(fraction * systems * items)) for fraction in fractions)
    seen = np.zeros_like(scores, dtype=bool)
    cursor = np.zeros(len(pairs), dtype=np.int32)
    decision = np.full(len(pairs), 2, dtype=np.int8)
    acquired = []
    item_position = 0
    committed = []
    committed_position = 0
    snapshots = []
    close_free(seen, cursor, decision, pairs, permutation, events)
    for budget in targets:
        while len(acquired) < budget and np.any(decision == 2):
            if committed_position == len(committed):
                if item_position == items:
                    break
                item = int(item_order[item_position])
                item_position += 1
                active_pairs = pairs[decision == 2]
                active_systems = np.unique(active_pairs.ravel())
                ordered_systems = sorted(
                    map(int, active_systems), key=lambda system: int(priority[system, item])
                )
                committed = [(system, item) for system in ordered_systems]
                committed_position = 0
                if not committed:
                    break
            chosen = committed[committed_position]
            committed_position += 1
            if seen[chosen]:
                raise AssertionError("A pruned label was charged twice")
            seen[chosen] = True
            acquired.append(chosen)
            close_free(seen, cursor, decision, pairs, permutation, events)
        snapshots.append(
            snapshot(scores, pairs, decision, cursor, len(acquired), budget)
        )
    if len(acquired) != len(set(acquired)) or len(acquired) != int(seen.sum()):
        raise AssertionError("Unique-label accounting failed")
    return snapshots, acquired, cursor, decision


def run(data_directory, repeats=50, output=None, master=MASTER):
    if repeats < 1:
        raise ValueError("Positive repeats required")
    verify_lock()
    datasets, provenance = load_prepared(data_directory)
    rows = []
    for language, (scores, names, items) in sorted(datasets.items()):
        pairs = np.asarray(list(combinations(range(len(names)), 2)), dtype=np.int16)
        paths = np.empty((len(pairs), repeats, len(items)), dtype=np.int32)
        priorities = []
        for repeat in range(repeats):
            item_order, priority = common_design(
                len(names), len(items), language, repeat, master
            )
            paths[:, repeat] = item_order
            priorities.append(priority)
        threshold = 40 * len(pairs)
        events, _ = make_paths(scores, pairs, paths, threshold)
        for repeat in range(repeats):
            result = simulate_pruned(
                scores,
                pairs,
                paths[:, repeat],
                events[:, repeat],
                priorities[repeat],
            )
            for fraction, record in zip(FRACTIONS, result[0]):
                rows.append(
                    dict(
                        language=language,
                        repeat=repeat,
                        method=METHOD,
                        fraction=fraction,
                        pairs=len(pairs),
                        systems=len(names),
                        items=len(items),
                        threshold=threshold,
                        **record,
                    )
                )
        print(f"{language}: {repeats}/{repeats} pruning blocks", flush=True)
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        with (output / "replicates.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        stage18 = HERE.parent / "stage18" / "results_reference"
        metadata = dict(
            master=master,
            repeats=repeats,
            languages=sorted(datasets),
            method=METHOD,
            fractions=list(FRACTIONS),
            protocol_sha256=hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
            source_sha256=provenance["source_sha256"],
            matrix_hashes={
                row["language"]: row["matrix_sha256"]
                for row in provenance["reports"]
                if row["included"]
            },
            stage18_replicates_sha256=hashlib.sha256(
                (stage18 / "replicates.csv").read_bytes()
            ).hexdigest(),
        )
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--output", default="results/stage20_development")
    arguments = parser.parse_args()
    run(arguments.data, arguments.repeats, arguments.output)
