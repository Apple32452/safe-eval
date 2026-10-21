"""Stage 15 annotation-level scheduling on fixed pair-prefix processes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'stage14'))
sys.path.insert(0, str(HERE.parent / 'stage13'))
sys.path.insert(0, str(HERE.parent / 'stage7'))
from paired_engine import CAP, Q
from prepare_wmt23 import load_data
from shared_pilot import (FRACTIONS, make_paths, precommit_permutations,
                          seed, simulate)

MASTER = 20261022
CONTROLS = ('focus_random', 'focus_first', 'evidence_first')
FRONTIER_METHODS = ('frontier_count', 'frontier_evidence')
METHODS = CONTROLS + FRONTIER_METHODS


def verify_lock():
    lock = json.loads((HERE/'IMPLEMENTATION_LOCK.json').read_text())
    repository = HERE.parent.parent
    for relative, expected in lock['sha256'].items():
        actual = hashlib.sha256((repository/relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('Locked input changed: '+relative)
    return lock


def label_priority(systems, items, language, repeat, master=MASTER):
    """Outcome-independent tie order over all unique system-item labels."""
    total = systems * items
    order = np.random.default_rng(
        seed(master, language, repeat, 'unique_label_priority')
    ).permutation(total)
    priority = np.empty(total, dtype=np.int64)
    priority[order] = np.arange(total)
    return priority.reshape(systems, items)


def frontier_utilities(cursor, decision, seen, pairs, perm, evidence, method):
    """Return candidate labels and exact pre-query integer utilities."""
    active = np.flatnonzero(decision == 2)
    if not len(active):
        return {}, active
    item = perm[active, cursor[active]]
    current = np.zeros(len(active), dtype=np.int64)
    observed = cursor[active] > 0
    current[observed] = evidence[active[observed], cursor[active[observed]] - 1]
    weights = np.ones(len(active), dtype=np.int64)
    if method == 'frontier_evidence':
        weights = Q + np.minimum(current, CAP)
    elif method != 'frontier_count':
        raise ValueError('Unknown frontier policy')
    utility = {}
    for row, p in enumerate(active):
        for system in pairs[p]:
            label = (int(system), int(item[row]))
            if not seen[label]:
                utility[label] = utility.get(label, 0) + int(weights[row])
    if not utility:
        raise AssertionError('Free frontiers must be closed before scheduling')
    return utility, active


def simulate_frontier(scores, pairs, perm, events, evidence, method,
                      priority, fractions=FRACTIONS):
    scores = np.asarray(scores)
    systems, items = scores.shape
    pair_count = len(pairs)
    if priority.shape != scores.shape:
        raise ValueError('One tie priority per unique label required')
    if len(np.unique(priority)) != priority.size:
        raise ValueError('Label priorities must be unique')
    targets = tuple(int(np.floor(f * systems * items)) for f in fractions)
    seen = np.zeros_like(scores, dtype=bool)
    cursor = np.zeros(pair_count, dtype=np.int32)
    decision = np.full(pair_count, 2, dtype=np.int8)
    acquired = []
    snapshots = []
    a, b = pairs.T

    def close_free():
        while True:
            active = np.flatnonzero(decision == 2)
            if not len(active):
                return
            item = perm[active, cursor[active]]
            ready = active[seen[a[active], item] & seen[b[active], item]]
            if not len(ready):
                return
            cursor[ready] += 1
            result = events[ready, cursor[ready] - 1]
            resolved = result != 2
            decision[ready[resolved]] = result[resolved]

    close_free()
    for budget in targets:
        while len(acquired) < budget:
            utility, active = frontier_utilities(
                cursor, decision, seen, pairs, perm, evidence, method)
            if not len(active):
                break
            best = max(utility.values())
            candidates = [label for label, value in utility.items() if value == best]
            chosen = min(candidates, key=lambda label: int(priority[label]))
            if seen[chosen]:
                raise AssertionError('A paid label was acquired twice')
            seen[chosen] = True
            acquired.append(chosen)
            close_free()
        truth = np.sign(scores[a].sum(axis=1) - scores[b].sum(axis=1))
        correct = int(np.sum((decision != 2) & (decision == truth)))
        wrong = int(np.sum((decision != 2) & (decision != truth)))
        snapshots.append(dict(
            budget=budget, labels=len(acquired), correct=correct, wrong=wrong,
            unresolved=pair_count-correct-wrong,
            reached_prefix=int(cursor.sum()), resolved_pairs=correct+wrong))
    if len(acquired) != len(set(acquired)) or len(acquired) != int(seen.sum()):
        raise AssertionError('Unique-label accounting failed')
    return snapshots, acquired, cursor, decision


def run(languages, repeats=50, output=None, master=MASTER):
    verify_lock()
    datasets, provenance = load_data(HERE.parent / 'stage7' / 'data')
    rows = []
    for language in languages:
        scores, names, items = datasets[language]
        pairs, perm = precommit_permutations(
            names, scores.shape[1], language, repeats, master)
        events, evidence = make_paths(scores, pairs, perm)
        for repeat in range(repeats):
            random_order = np.random.default_rng(
                seed(master, language, repeat, 'pair_priority')
            ).permutation(len(pairs))
            pair_priority = np.empty(len(pairs), dtype=np.int64)
            pair_priority[random_order] = np.arange(len(pairs))
            unique_priority = label_priority(
                len(names), len(items), language, repeat, master)
            for method in METHODS:
                if method in CONTROLS:
                    result = simulate(
                        scores, pairs, perm[:, repeat], events[:, repeat],
                        evidence[:, repeat], method, priority=pair_priority)
                else:
                    result = simulate_frontier(
                        scores, pairs, perm[:, repeat], events[:, repeat],
                        evidence[:, repeat], method, unique_priority)
                snapshots, acquired, cursor, decision = result
                for fraction, snapshot in zip(FRACTIONS, snapshots):
                    rows.append(dict(
                        language=language, repeat=repeat, method=method,
                        fraction=fraction, pairs=len(pairs), systems=len(names),
                        items=len(items), **snapshot))
            if (repeat + 1) % 10 == 0:
                print(f'{language}: {repeat + 1}/{repeats} blocks', flush=True)
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=False)
        with (output / 'replicates.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        metadata = dict(
            master=master, repeats=repeats, languages=list(languages),
            methods=list(METHODS), fractions=list(FRACTIONS),
            threshold_units=CAP // Q, alpha_family=0.05,
            protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
            source_provenance_commit=provenance['pinned_commit'],
            matrix_hashes={r['language_pair']: r['matrix_sha256']
                           for r in provenance['datasets']
                           if r['language_pair'] in languages})
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--languages', nargs='+',
                        default=['en-de', 'he-en', 'zh-en'])
    parser.add_argument('--repeats', type=int, default=50)
    parser.add_argument('--output', default='results/stage15_development')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('Positive repeats required')
    run(args.languages, args.repeats, args.output)
