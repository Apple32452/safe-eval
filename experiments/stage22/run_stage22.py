"""Run the frozen Stage 22 requested-graph pruning experiment."""
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

METHODS = ("star_common", "star_pruned")
DIAGNOSTIC_GRAPHS = ("ring1", "ring2", "complete")


def verify_lock():
    lock = json.loads((HERE / "IMPLEMENTATION_LOCK.json").read_text())
    repository = HERE.parent.parent
    for relative, expected in lock["sha256"].items():
        observed = hashlib.sha256((repository / relative).read_bytes()).hexdigest()
        if observed != expected:
            raise ValueError("Locked source changed: " + relative)
    return lock


def star_edges(system_count, reference):
    if not 0 <= reference < system_count:
        raise ValueError("Reference is outside the system set")
    return np.asarray(
        [tuple(sorted((reference, other))) for other in range(system_count)
         if other != reference],
        dtype=np.int16,
    )


def circulant_edges(names, offsets):
    names = np.asarray(names).astype(str)
    system_count = len(names)
    order = np.argsort(names, kind="stable")
    edges = set()
    for position in range(system_count):
        for offset in offsets:
            if not 0 < offset < system_count:
                raise ValueError("Circulant offsets must be in (0, S)")
            a = int(order[position])
            b = int(order[(position + offset) % system_count])
            if a != b:
                edges.add(tuple(sorted((a, b))))
    if not edges:
        raise ValueError("Requested graph has no edges")
    return np.asarray(sorted(edges), dtype=np.int16)


def task_graphs(names, include_diagnostics=True):
    system_count = len(names)
    tasks = [
        dict(graph="star", task_id=f"reference:{reference}",
             reference=reference, edges=star_edges(system_count, reference))
        for reference in range(system_count)
    ]
    if include_diagnostics:
        tasks.extend(
            [
                dict(graph="ring1", task_id="ring1", reference=-1,
                     edges=circulant_edges(names, (1,))),
                dict(graph="ring2", task_id="ring2", reference=-1,
                     edges=circulant_edges(names, (1, 2))),
                dict(graph="complete", task_id="complete", reference=-1,
                     edges=np.asarray(list(combinations(range(system_count), 2)),
                                      dtype=np.int16)),
            ]
        )
    return tasks


def _validate_simulation_inputs(scores, pairs, permutation, events, priority):
    scores = np.asarray(scores, dtype=float)
    pairs = np.asarray(pairs, dtype=np.int16)
    permutation = np.asarray(permutation, dtype=np.int32)
    events = np.asarray(events, dtype=np.int8)
    priority = np.asarray(priority)
    systems, items = scores.shape
    if pairs.ndim != 2 or pairs.shape[1] != 2 or not len(pairs):
        raise ValueError("A nonempty two-column requested edge set is required")
    if len({tuple(map(int, pair)) for pair in pairs}) != len(pairs):
        raise ValueError("Requested edges must be unique")
    if np.any(pairs < 0) or np.any(pairs >= systems) or np.any(pairs[:, 0] >= pairs[:, 1]):
        raise ValueError("Requested edges must be canonical system pairs")
    if permutation.shape != (len(pairs), items):
        raise ValueError("Every requested edge needs a complete item path")
    if not np.all(permutation == permutation[0]):
        raise ValueError("Every requested edge must share the common item path")
    if events.shape != (len(pairs), items):
        raise ValueError("Event paths must align with requested edges")
    if priority.shape != scores.shape or len(np.unique(priority)) != priority.size:
        raise ValueError("Unique common label priorities required")
    return scores, pairs, permutation, events, priority


def simulate_graph(scores, pairs, permutation, events, priority, method,
                   fractions=FRACTIONS):
    """Run a common or active-vertex policy through exact graph completion."""
    scores, pairs, permutation, events, priority = _validate_simulation_inputs(
        scores, pairs, permutation, events, priority
    )
    if method not in METHODS:
        raise ValueError("Unknown Stage 22 method")
    systems, items = scores.shape
    targets = tuple(int(np.floor(fraction * systems * items)) for fraction in fractions)
    if sorted(targets) != list(targets) or targets[-1] > systems * items:
        raise ValueError("Invalid label-budget checkpoints")

    seen = np.zeros_like(scores, dtype=bool)
    cursor = np.zeros(len(pairs), dtype=np.int32)
    decision = np.full(len(pairs), 2, dtype=np.int8)
    resolution_cost = np.full(len(pairs), -1, dtype=np.int64)
    acquired = []
    item_order = permutation[0]
    item_position = 0
    committed = []
    committed_position = 0
    active_sizes = []
    snapshots = []

    def advance_one():
        nonlocal item_position, committed, committed_position
        if not np.any(decision == 2):
            return False
        if committed_position == len(committed):
            if item_position == items:
                raise AssertionError("Unresolved edge exhausted its finite pool")
            item = int(item_order[item_position])
            item_position += 1
            if method == "star_common":
                active_systems = np.arange(systems, dtype=int)
            else:
                active_systems = np.unique(pairs[decision == 2].ravel())
            ordered_systems = sorted(
                map(int, active_systems),
                key=lambda system: int(priority[system, item]),
            )
            committed = [(system, item) for system in ordered_systems]
            committed_position = 0
            active_sizes.append(len(ordered_systems))
            if not committed:
                raise AssertionError("An unresolved graph has no active endpoint")
        chosen = committed[committed_position]
        committed_position += 1
        if seen[chosen]:
            raise AssertionError("A graph policy charged one label twice")
        seen[chosen] = True
        acquired.append(chosen)
        before = decision.copy()
        close_free(seen, cursor, decision, pairs, permutation, events)
        newly_resolved = np.flatnonzero((before == 2) & (decision != 2))
        resolution_cost[newly_resolved] = len(acquired)
        return True

    close_free(seen, cursor, decision, pairs, permutation, events)
    for budget in targets:
        while len(acquired) < budget and np.any(decision == 2):
            advance_one()
        snapshots.append(snapshot(scores, pairs, decision, cursor, len(acquired), budget))
    while np.any(decision == 2):
        advance_one()

    if np.any(resolution_cost < 0):
        raise AssertionError("Every requested edge must have a resolution cost")
    if len(acquired) != len(set(acquired)) or len(acquired) != int(seen.sum()):
        raise AssertionError("Unique-label accounting failed")
    truth = np.sign(
        scores[pairs[:, 0]].sum(axis=1) - scores[pairs[:, 1]].sum(axis=1)
    ).astype(np.int8)
    if not np.array_equal(decision, truth):
        raise AssertionError("Final decisions must equal exact full-pool signs")
    return dict(
        snapshots=snapshots,
        acquired=acquired,
        cursor=cursor,
        decision=decision,
        resolution_cost=resolution_cost,
        active_sizes=active_sizes,
        completion_cost=len(acquired),
    )


def _pair_indices(all_pairs):
    return {tuple(map(int, pair)): index for index, pair in enumerate(all_pairs)}


def _task_rows(language, names, items, repeat, task, common, pruned):
    pairs = task["edges"]
    signs = common["decision"]
    if not np.array_equal(common["decision"], pruned["decision"]):
        raise AssertionError("Paired graph methods returned different decisions")
    if np.any(pruned["resolution_cost"] > common["resolution_cost"]):
        raise AssertionError("Per-edge pathwise cost dominance failed")
    common_cost = common["completion_cost"]
    pruned_cost = pruned["completion_cost"]
    if pruned_cost > common_cost:
        raise AssertionError("Graph pruning used more labels than its control")
    absolute = common_cost - pruned_cost
    comparison = dict(
        language=language,
        repeat=repeat,
        graph=task["graph"],
        task_id=task["task_id"],
        reference=int(task["reference"]),
        reference_name=(str(names[task["reference"]]) if task["reference"] >= 0 else ""),
        systems=len(names),
        items=len(items),
        edges=len(pairs),
        common_cost=common_cost,
        pruned_cost=pruned_cost,
        absolute_saving=absolute,
        relative_saving=absolute / common_cost,
        edge_dominance_violations=int(
            np.sum(pruned["resolution_cost"] > common["resolution_cost"])
        ),
        max_pruned_minus_common_edge_cost=int(
            np.max(pruned["resolution_cost"] - common["resolution_cost"])
        ),
        final_decision_disagreements=int(
            np.sum(common["decision"] != pruned["decision"])
        ),
        positive_edges=int(np.sum(signs == 1)),
        negative_edges=int(np.sum(signs == -1)),
        tied_edges=int(np.sum(signs == 0)),
        mean_active_systems=float(np.mean(pruned["active_sizes"])),
        min_active_systems=int(np.min(pruned["active_sizes"])),
    )
    checkpoints = []
    for method, result in zip(METHODS, (common, pruned)):
        for fraction, record in zip(FRACTIONS, result["snapshots"]):
            checkpoints.append(
                dict(
                    language=language, repeat=repeat, graph=task["graph"],
                    task_id=task["task_id"], reference=int(task["reference"]),
                    method=method, fraction=fraction, systems=len(names),
                    items=len(items), edges=len(pairs), **record,
                )
            )
    return comparison, checkpoints


def run(data_directory, repeats=50, output=None, master=MASTER, languages=None,
        include_diagnostics=True):
    if repeats < 1:
        raise ValueError("Positive repeats required")
    verify_lock()
    datasets, provenance = load_prepared(data_directory)
    if languages is not None:
        requested = list(languages)
        missing = sorted(set(requested) - set(datasets))
        if missing:
            raise ValueError("Unknown requested languages: " + ", ".join(missing))
        datasets = {language: datasets[language] for language in requested}

    comparison_rows = []
    checkpoint_rows = []
    for language, (scores, names, items) in sorted(datasets.items()):
        systems = len(names)
        all_pairs = np.asarray(list(combinations(range(systems), 2)), dtype=np.int16)
        lookup = _pair_indices(all_pairs)
        paths = np.empty((len(all_pairs), repeats, len(items)), dtype=np.int32)
        priorities = []
        for repeat in range(repeats):
            item_order, priority = common_design(
                systems, len(items), language, repeat, master
            )
            paths[:, repeat] = item_order
            priorities.append(priority)
        tasks = task_graphs(names, include_diagnostics=include_diagnostics)
        edge_counts = sorted({len(task["edges"]) for task in tasks})
        event_cache = {
            count: make_paths(scores, all_pairs, paths, 40 * count)[0]
            for count in edge_counts
        }
        for repeat in range(repeats):
            for task in tasks:
                indices = np.asarray(
                    [lookup[tuple(map(int, edge))] for edge in task["edges"]],
                    dtype=np.int32,
                )
                pair_paths = paths[indices, repeat]
                pair_events = event_cache[len(task["edges"])][indices, repeat]
                common = simulate_graph(
                    scores, task["edges"], pair_paths, pair_events,
                    priorities[repeat], "star_common"
                )
                pruned = simulate_graph(
                    scores, task["edges"], pair_paths, pair_events,
                    priorities[repeat], "star_pruned"
                )
                comparison, checkpoints = _task_rows(
                    language, names, items, repeat, task, common, pruned
                )
                comparison_rows.append(comparison)
                checkpoint_rows.extend(checkpoints)
        print(f"{language}: {repeats}/{repeats} repeats, {len(tasks)} graph tasks",
              flush=True)

    metadata = dict(
        master=master, repeats=repeats, languages=sorted(datasets),
        include_diagnostics=include_diagnostics, methods=list(METHODS),
        fractions=list(FRACTIONS),
        protocol_sha256=hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
        source_sha256=provenance["source_sha256"],
        matrix_hashes={
            row["language"]: row["matrix_sha256"]
            for row in provenance["reports"]
            if row["included"] and row["language"] in datasets
        },
        systems={language: len(data[1]) for language, data in datasets.items()},
        task_counts={
            language: len(task_graphs(data[1], include_diagnostics))
            for language, data in datasets.items()
        },
    )
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        with (output / "comparison.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=comparison_rows[0].keys())
            writer.writeheader(); writer.writerows(comparison_rows)
        with (output / "checkpoints.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=checkpoint_rows[0].keys())
            writer.writeheader(); writer.writerows(checkpoint_rows)
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return comparison_rows, checkpoint_rows, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--output", default="results/stage22_development")
    parser.add_argument("--languages", nargs="+")
    parser.add_argument("--primary-only", action="store_true")
    arguments = parser.parse_args()
    run(arguments.data, repeats=arguments.repeats, output=arguments.output,
        languages=arguments.languages,
        include_diagnostics=not arguments.primary_only)
