"""Run the frozen Stage 19 common-core adaptive-tail candidate."""
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
sys.path.insert(0, str(HERE.parent / "stage15"))
sys.path.insert(0, str(HERE.parent / "stage14"))
from continuous_engine import make_paths
from frontier_experiment import label_priority
from prepare_scores import load_prepared
from run_stage17 import close_free, frontier_utilities, snapshot
from run_stage18 import MASTER as COMMON_MASTER, common_design
from shared_pilot import FRACTIONS, seed

MASTER = 20261026
METHOD = "common_core_frontier"


def verify_lock():
    lock = json.loads((HERE / "IMPLEMENTATION_LOCK.json").read_text())
    repository = HERE.parent.parent
    for relative, expected in lock["sha256"].items():
        observed = hashlib.sha256((repository / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise ValueError("Locked source changed: " + relative)
    return lock


def hybrid_paths(names, n, language, repeats, master=MASTER):
    pairs = np.asarray(list(combinations(range(len(names)), 2)), dtype=np.int16)
    paths = np.empty((len(pairs), repeats, n), dtype=np.int32)
    common_priorities = []
    core_size = n // 2
    for repeat in range(repeats):
        item_order, common_priority = common_design(
            len(names), n, language, repeat, COMMON_MASTER
        )
        core = item_order[:core_size]
        remaining = item_order[core_size:]
        common_priorities.append(common_priority)
        for pair_index, (a, b) in enumerate(pairs):
            suffix = np.random.default_rng(
                seed(
                    master,
                    language,
                    str(names[a]),
                    str(names[b]),
                    repeat,
                    "pair_suffix",
                )
            ).permutation(remaining)
            paths[pair_index, repeat] = np.concatenate((core, suffix))
    return pairs, paths, common_priorities, core_size


def simulate_hybrid(
    scores,
    pairs,
    permutation,
    events,
    evidence,
    common_priority,
    tail_priority,
    core_size,
    threshold,
    fractions=FRACTIONS,
):
    systems, items = scores.shape
    if not 0 <= core_size <= items:
        raise ValueError("Invalid common core")
    if common_priority.shape != scores.shape or tail_priority.shape != scores.shape:
        raise ValueError("Priority matrices must match scores")
    common_labels = [tuple(map(int, index)) for index in np.ndindex(scores.shape)]
    common_labels.sort(key=lambda label: int(common_priority[label]))
    core_cost = core_size * systems
    common_labels = common_labels[:core_cost]
    targets = tuple(int(np.floor(fraction * systems * items)) for fraction in fractions)
    seen = np.zeros_like(scores, dtype=bool)
    cursor = np.zeros(len(pairs), dtype=np.int32)
    decision = np.full(len(pairs), 2, dtype=np.int8)
    acquired = []
    common_position = 0
    snapshots = []
    close_free(seen, cursor, decision, pairs, permutation, events)
    for budget in targets:
        while len(acquired) < budget and np.any(decision == 2):
            if common_position < len(common_labels):
                chosen = common_labels[common_position]
                common_position += 1
            else:
                utility, active = frontier_utilities(
                    cursor,
                    decision,
                    seen,
                    pairs,
                    permutation,
                    evidence,
                    "frontier_evidence",
                    threshold,
                )
                if not len(active):
                    break
                best = max(utility.values())
                chosen = min(
                    (label for label, value in utility.items() if value == best),
                    key=lambda label: int(tail_priority[label]),
                )
            if seen[chosen]:
                raise AssertionError("A hybrid label was charged twice")
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
        pairs, paths, common_priorities, core_size = hybrid_paths(
            names, len(items), language, repeats, master
        )
        threshold = 40 * len(pairs)
        events, evidence = make_paths(scores, pairs, paths, threshold)
        for repeat in range(repeats):
            tail_priority = label_priority(
                len(names), len(items), language, repeat, master
            )
            result = simulate_hybrid(
                scores,
                pairs,
                paths[:, repeat],
                events[:, repeat],
                evidence[:, repeat],
                common_priorities[repeat],
                tail_priority,
                core_size,
                threshold,
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
                        core_items=core_size,
                        threshold=threshold,
                        **record,
                    )
                )
        print(f"{language}: {repeats}/{repeats} hybrid blocks", flush=True)
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
            common_master=COMMON_MASTER,
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
    parser.add_argument("--output", default="results/stage19_development")
    arguments = parser.parse_args()
    run(arguments.data, arguments.repeats, arguments.output)
