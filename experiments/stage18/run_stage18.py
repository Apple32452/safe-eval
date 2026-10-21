"""Run the frozen Stage 18 common random test-set baseline."""
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
sys.path.insert(0, str(HERE.parent / "stage17"))
sys.path.insert(0, str(HERE.parent / "stage14"))
from continuous_engine import make_paths
from prepare_scores import load_prepared
from run_stage17 import simulate_uniform
from shared_pilot import FRACTIONS, seed

MASTER = 20261025
METHOD = "common_random_items"


def verify_lock():
    lock = json.loads((HERE / "IMPLEMENTATION_LOCK.json").read_text())
    repository = HERE.parent.parent
    for relative, expected in lock["sha256"].items():
        observed = hashlib.sha256((repository / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise ValueError("Locked source changed: " + relative)
    return lock


def common_design(systems, items, language, repeat, master=MASTER):
    """Return a common item path and nested item/system label priorities."""
    item_order = np.random.default_rng(
        seed(master, language, repeat, "common_item_order")
    ).permutation(items)
    priority = np.empty((systems, items), dtype=np.int64)
    position = 0
    for item in item_order:
        system_order = np.random.default_rng(
            seed(master, language, repeat, "common_system_order", int(item))
        ).permutation(systems)
        for system in system_order:
            priority[int(system), int(item)] = position
            position += 1
    if sorted(priority.ravel().tolist()) != list(range(systems * items)):
        raise AssertionError("Common design did not assign unique priorities")
    return item_order.astype(np.int32), priority


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
            snapshots, acquired, _, _ = simulate_uniform(
                scores,
                pairs,
                paths[:, repeat],
                events[:, repeat],
                priorities[repeat],
            )
            if len(acquired) != len(set(acquired)):
                raise AssertionError("A common-test-set label was charged twice")
            for fraction, record in zip(FRACTIONS, snapshots):
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
        print(f"{language}: {repeats}/{repeats} common-item blocks", flush=True)
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        with (output / "replicates.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        stage17 = HERE.parent / "stage17" / "results_reference"
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
            stage17_replicates_sha256=hashlib.sha256(
                (stage17 / "replicates.csv").read_bytes()
            ).hexdigest(),
        )
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--output", default="results/stage18_development")
    arguments = parser.parse_args()
    run(arguments.data, arguments.repeats, arguments.output)
