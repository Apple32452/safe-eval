"""Prospectively frozen fixed-budget reference-star scheduling screen."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "stage22"))
sys.path.insert(0, str(ROOT / "experiments" / "stage17"))
sys.path.insert(0, str(ROOT / "experiments" / "stage14"))
sys.path.insert(0, str(ROOT / "experiments" / "stage18"))
from run_stage22 import simulate_graph, star_edges
from continuous_engine import directional_paths, make_paths
from shared_pilot import simulate as simulate_evidence_first
from run_stage18 import common_design

MASTER = 20261023
REPEATS = 40
PILOT = 8
ALPHA = 0.05
SCENARIOS = {
    "independent_easy": ([.55, .95, .90, .80, .70, .30, .20, .10], False),
    "shared_easy": ([.55, .95, .90, .80, .70, .30, .20, .10], True),
    "independent_mixed": ([.55, .90, .80, .60, .55, .50, .30, .10], False),
    "near_ties": ([.50, .51, .49, .53, .47, .55, .45, .50], False),
}


def _seed(*parts):
    digest = hashlib.sha256("|".join(map(str, (MASTER, *parts))).encode()).digest()
    return int.from_bytes(digest[:8], "little")


def create_matrix(name, repeat, items=96):
    rates, shared = SCENARIOS[name]
    rng = np.random.default_rng(_seed("scores", name, repeat))
    uniforms = rng.random((1 if shared else len(rates), items))
    return (uniforms < np.asarray(rates)[:, None]).astype(float)


def estimate_stopping_prefix(observed_differences, items, threshold):
    """Run the frozen certificate on a *hypothetical* constant continuation."""
    k = len(observed_differences)
    if not 0 < k < items:
        return items
    mu = float(np.mean(observed_differences))
    continuation = np.empty((1, 1, items), dtype=float)
    continuation[0, 0, :k] = observed_differences
    continuation[0, 0, k:] = mu
    events, _ = directional_paths(continuation, threshold)
    future = np.flatnonzero(events[0, 0, k:] != 2)
    return int(k + 1 + future[0]) if len(future) else items


def star_offline_optimum(prefixes, budget):
    """Hindsight-only upper bound for a reference star with strict edges."""
    ordered = sorted(int(value) for value in prefixes)
    running = 0
    count = 0
    for length in ordered:
        running += length
        if running + length <= budget:
            count += 1
        else:
            break
    return count


def simulate_footprint(scores, edges, permutation, events, priority,
                       threshold, budget, pilot=PILOT, trace=False):
    """Read only purchased scores for scheduling; events are read at closed prefixes."""
    scores = np.asarray(scores, dtype=float)
    edges = np.asarray(edges, dtype=int)
    systems, items = scores.shape
    if not (0 <= pilot <= items and 0 <= budget <= systems * items):
        raise ValueError("Invalid pilot or budget")
    if not np.array_equal(np.sort(permutation), np.arange(items)):
        raise ValueError("Item order must be a permutation")
    if events.shape != (len(edges), items) or priority.shape != scores.shape:
        raise ValueError("Paths, events and priorities must align")
    if pilot * systems > budget:
        raise ValueError("Pilot must fit inside the budget")
    seen = np.zeros(scores.shape, dtype=bool)
    revealed = np.full(scores.shape, np.nan)
    cursor = np.zeros(len(edges), dtype=int)
    decision = np.full(len(edges), 2, dtype=np.int8)
    histories = [[] for _ in edges]
    purchased = []
    decisions = []
    forecasts = [items for _ in edges]
    pilots = [tuple(sorted(((v, int(i)) for v in range(systems)),
                           key=lambda cell: int(priority[cell])))
              for i in permutation[:pilot]]
    pilot_queue = list(itertools.chain.from_iterable(pilots))
    pair_queue = []
    snapshot = None

    def close_free():
        changed = []
        while True:
            ready = [e for e, (a, b) in enumerate(edges)
                     if decision[e] == 2 and cursor[e] < items
                     and seen[a, permutation[cursor[e]]]
                     and seen[b, permutation[cursor[e]]]]
            if not ready:
                break
            for e in ready:
                a, b = edges[e]
                i = int(permutation[cursor[e]])
                histories[e].append(float(revealed[a, i] - revealed[b, i]))
                cursor[e] += 1
                decision[e] = events[e, cursor[e] - 1]
                changed.append(e)
        for e in set(changed):
            if decision[e] == 2:
                forecasts[e] = estimate_stopping_prefix(
                    histories[e], items, threshold)

    def purchase(cell):
        v, i = cell
        if seen[v, i]:
            raise AssertionError("A cached label was purchased again")
        seen[v, i] = True
        revealed[v, i] = scores[v, i]
        purchased.append((v, i))
        close_free()

    def record():
        truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                        scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
        return dict(labels=len(purchased),
                    strict=int(np.count_nonzero((decision != 2) &
                                                (decision != 0) &
                                                (decision == truth))),
                    wrong=int(np.count_nonzero((decision != 2) &
                                               (decision != truth))),
                    ties=int(np.count_nonzero(decision == 0)),
                    unresolved=int(np.count_nonzero(decision == 2)),
                    decisions=decision.copy())

    while np.any(decision == 2):
        if len(purchased) == budget and snapshot is None:
            snapshot = record()
        if pilot_queue:
            cell = pilot_queue.pop(0)
        elif pair_queue:
            cell = pair_queue.pop(0)
        else:
            # The acquisition score counts the union of missing cached cells
            # over the predicted required prefix, not just the next pair.
            options = []
            for e, (a, b) in enumerate(edges):
                if decision[e] != 2:
                    continue
                n_hat = max(int(cursor[e]) + 1, forecasts[e])
                missing = sum(not seen[v, int(i)]
                              for v in (a, b) for i in permutation[:n_hat])
                i = int(permutation[cursor[e]])
                next_cells = [(int(v), i) for v in (a, b) if not seen[v, i]]
                if not next_cells:
                    raise AssertionError("A free prefix was not consumed")
                tie = min(int(priority[cell]) for cell in next_cells)
                options.append((missing, tie, e, next_cells))
            if not options:
                raise AssertionError("An unresolved edge has no candidate cells")
            _, _, _, next_cells = min(options, key=lambda row: row[:3])
            pair_queue = sorted(next_cells, key=lambda cell: int(priority[cell]))
            cell = pair_queue.pop(0)
        purchase(cell)
        if trace:
            decisions.append((cell, tuple(map(int, decision)),
                              tuple(map(int, cursor))))
    if snapshot is None:
        snapshot = record()
    if len(purchased) != int(seen.sum()) or len(purchased) != len(set(purchased)):
        raise AssertionError("Unique-label accounting failed")
    truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                    scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
    if not np.array_equal(truth, decision):
        raise AssertionError("Final decisions disagree with exact signs")
    return dict(snapshot=snapshot, completion_cost=len(purchased),
                purchased=purchased, ledger=decisions, final_decisions=decision)


def run(repeats=REPEATS, output=None):
    if not 1 <= repeats <= REPEATS:
        raise ValueError("Expected one to 40 frozen-seed repeats")
    rows = []
    for scenario in SCENARIOS:
        for repeat in range(repeats):
            scores = create_matrix(scenario, repeat)
            systems, items = scores.shape
            edges = star_edges(systems, 0)
            budget = systems * items // 2
            threshold = 40 * len(edges)
            order, priority = common_design(
                systems, items, scenario, repeat, MASTER)
            perm = np.tile(order, (len(edges), 1))
            events, evidence = make_paths(scores, edges, perm[:, None, :],
                                          threshold)
            paths = events[:, 0]
            extra = evidence[:, 0]
            pruned = simulate_graph(scores, edges, perm, paths, priority,
                                    "star_pruned", fractions=(.5,))
            # Stage 14 scheduler is the frozen evidence-first cell control.
            evidence_result = simulate_evidence_first(
                scores, edges, perm, paths, extra, "evidence_first",
                fractions=(.5, 1.0))
            footprint = simulate_footprint(scores, edges, order, paths,
                                           priority, threshold, budget)
            truth = np.sign(scores[edges[:, 0]].sum(axis=1) -
                            scores[edges[:, 1]].sum(axis=1)).astype(np.int8)
            # Reconstruct each baseline's decision vector at the checkpoint
            # from its observed prefix. This cannot use unrevealed outcomes.
            for method, bought, completion, saved in (
                    ("pruned", pruned["acquired"], pruned["completion_cost"],
                     pruned["snapshots"][0]),
                    ("evidence_first", evidence_result[1],
                     evidence_result[0][-1]["labels"], evidence_result[0][0])):
                # The acquired ledger includes post-checkpoint cells for the
                # pruned method: replay only to saved['labels'].
                prefix = bought[:int(saved["labels"])]
                known = np.zeros_like(scores, dtype=bool)
                cursors = np.zeros(len(edges), dtype=int)
                decisions = np.full(len(edges), 2, dtype=np.int8)
                for cell in prefix:
                    known[cell] = True
                    while True:
                        ready = [e for e, (a, b) in enumerate(edges)
                                 if decisions[e] == 2 and cursors[e] < items
                                 and known[a, order[cursors[e]]]
                                 and known[b, order[cursors[e]]]]
                        if not ready:
                            break
                        for e in ready:
                            cursors[e] += 1
                            decisions[e] = paths[e, cursors[e] - 1]
                if int(np.sum(decisions != 2)) != saved["resolved_pairs"]:
                    raise AssertionError("Baseline checkpoint replay failed")
                metrics = dict(labels=len(prefix),
                               strict=int(np.sum((decisions != 2) &
                                                 (decisions != 0) &
                                                 (decisions == truth))),
                               wrong=int(np.sum((decisions != 2) &
                                                (decisions != truth))),
                               ties=int(np.sum(decisions == 0)),
                               unresolved=int(np.sum(decisions == 2)))
                rows.append(dict(scenario=scenario, repeat=repeat, method=method,
                                 budget=budget, completion_cost=completion,
                                 **metrics))
            metrics = {key: footprint["snapshot"][key]
                       for key in ("labels", "strict", "wrong", "ties", "unresolved")}
            rows.append(dict(scenario=scenario, repeat=repeat,
                             method="footprint", budget=budget,
                             completion_cost=footprint["completion_cost"],
                             **metrics))
        print(f"{scenario}: {repeats} paired matrices", flush=True)
    if output is not None:
        target = Path(output)
        target.mkdir(parents=True, exist_ok=False)
        with (target / "replicates.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        metadata = dict(master=MASTER, repeats=repeats, scenarios=list(SCENARIOS),
                        pilot=PILOT, alpha=ALPHA,
                        protocol_sha256=hashlib.sha256((HERE / "PROTOCOL.md")
                                                        .read_bytes()).hexdigest())
        (target / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.repeats, args.output)
