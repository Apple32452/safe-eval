"""Exploratory shared-label pilot; policies only access revealed-label prefixes."""
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
sys.path.insert(0, str(HERE.parent / 'stage13'))
sys.path.insert(0, str(HERE.parent / 'stage7'))
from paired_engine import CAP, Q, binomial_table, raw_evidence
from prepare_wmt23 import load_data

MASTER = 20261022
FRACTIONS = (0.25, 0.5, 0.75)
METHODS = ('round_robin', 'reuse_first', 'evidence_first',
           'focus_first', 'focus_random')


def seed(*parts):
    key = '|'.join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8], 'little')


def precommit_permutations(names, n, language, repeats, master=MASTER):
    pairs = np.asarray(list(combinations(range(len(names)), 2)), dtype=np.int16)
    permutations = np.empty((len(pairs), repeats, n), dtype=np.int16)
    for p, (a, b) in enumerate(pairs):
        for r in range(repeats):
            permutations[p, r] = np.random.default_rng(
                seed(master, language, str(names[a]), str(names[b]), r)
            ).permutation(n)
    return pairs, permutations


def make_paths(scores, pairs, permutations):
    """Offline oracle traces; the scheduler reads only its current prefix."""
    scores = np.asarray(scores)
    p, repeats, n = permutations.shape
    if scores.ndim != 2 or scores.shape[1] != n or len(pairs) != p:
        raise ValueError('Matrix and permutations must align')
    if np.any((scores != 0) & (scores != 1)):
        raise ValueError('Binary recorded outcomes required')
    if not np.array_equal(np.sort(permutations, axis=-1),
                          np.broadcast_to(np.arange(n), permutations.shape)):
        raise ValueError('Each pair must have a complete permutation')
    a, b = pairs.T
    diffs = scores[a[:, None, None], permutations] - scores[b[:, None, None], permutations]
    positive = np.zeros((p, repeats), dtype=np.int64)
    negative = positive.copy()
    equal = positive.copy()
    event = np.full((p, repeats, n), 2, dtype=np.int8)
    evidence = np.zeros((p, repeats, n), dtype=np.int64)
    table = binomial_table(n)
    for t in range(n):
        d = diffs[:, :, t]
        positive += d == 1
        negative += d == -1
        equal += d == 0
        raw = raw_evidence(n, positive.ravel(), negative.ravel(), equal.ravel(), table)
        raw = raw.reshape(2, p, repeats)
        evidence[:, :, t] = np.maximum(raw[0], raw[1])
        forward = raw[0] >= CAP
        reverse = raw[1] >= CAP
        statistical = np.where(forward & ~reverse, 1,
                               np.where(reverse & ~forward, -1, 2))
        remaining = n - t - 1
        observed = positive - negative
        deterministic = np.where(observed > remaining, 1,
                                 np.where(observed < -remaining, -1, 2))
        event[:, :, t] = np.where(deterministic != 2, deterministic, statistical)
        if t == n - 1:
            event[:, :, t] = np.sign(observed)
    return event, evidence


def select_pair(method, cursor, decision, seen, pairs, perm, evidence, pivot,
                priority=None):
    active = np.flatnonzero(decision == 2)
    if not len(active):
        return None
    # All pairs with both next labels known should already have been closed.
    next_item = perm[active, cursor[active]]
    missing = (~seen[pairs[active, 0], next_item]).astype(int)
    missing += (~seen[pairs[active, 1], next_item]).astype(int)
    if np.any(missing == 0):
        raise AssertionError('A free prefix was not consumed')
    if method == 'focus_first':
        return int(active[0])
    if method == 'focus_random':
        if priority is None or len(priority) != len(pairs):
            raise ValueError('A precommitted pair priority is required')
        return int(active[np.argmin(priority[active])])
    if method == 'reuse_first':
        active = active[missing == missing.min()]
    elif method == 'evidence_first':
        strength = np.zeros(len(active), dtype=np.int64)
        observed = cursor[active] > 0
        strength[observed] = evidence[active[observed], cursor[active[observed]] - 1]
        active = active[strength == strength.max()]
    elif method != 'round_robin':
        raise ValueError('Unknown scheduler')
    return int(active[np.argmin((active - pivot) % len(pairs))])


def simulate(scores, pairs, perm, events, evidence, method, fractions=FRACTIONS,
             priority=None):
    """Unique-label acquisition with shared free closure after each annotation."""
    m, n = scores.shape
    p = len(pairs)
    if perm.shape != (p, n) or events.shape != (p, n) or evidence.shape != (p, n):
        raise ValueError('Expected one precommitted path for every pair')
    targets = tuple(int(np.floor(f * m * n)) for f in fractions)
    if not targets or sorted(targets) != list(targets) or targets[-1] > m * n:
        raise ValueError('Invalid annotation checkpoints')
    seen = np.zeros((m, n), dtype=bool)
    cursor = np.zeros(p, dtype=np.int32)
    decision = np.full(p, 2, dtype=np.int8)
    pivot = 0
    spent = 0
    snapshots = []
    acquired = []
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
        while spent < budget:
            chosen = select_pair(method, cursor, decision, seen, pairs, perm,
                                 evidence, pivot, priority)
            if chosen is None:
                break
            item = int(perm[chosen, cursor[chosen]])
            missing = [int(s) for s in pairs[chosen] if not seen[s, item]]
            if not missing:
                raise AssertionError('Closure failed')
            system = missing[0]
            seen[system, item] = True
            acquired.append((system, item))
            spent += 1
            pivot = (chosen + 1) % p
            close_free()
        truth = np.sign(scores[a].sum(axis=1) - scores[b].sum(axis=1))
        correct = int(np.sum((decision != 2) & (decision == truth)))
        wrong = int(np.sum((decision != 2) & (decision != truth)))
        snapshots.append(dict(budget=budget, labels=spent, correct=correct,
                              wrong=wrong, unresolved=p - correct - wrong,
                              reached_prefix=int(cursor.sum()),
                              resolved_pairs=correct + wrong))
    assert spent == int(seen.sum()) == len(set(acquired))
    return snapshots, acquired, cursor, decision


def run(languages, repeats=12, output=None, master=MASTER):
    datasets, provenance = load_data(HERE.parent / 'stage7' / 'data')
    rows = []
    for language in languages:
        scores, names, items = datasets[language]
        pairs, perm = precommit_permutations(names, scores.shape[1], language,
                                              repeats, master)
        events, evidence = make_paths(scores, pairs, perm)
        for repeat in range(repeats):
            random_order = np.random.default_rng(
                seed(master, language, repeat, 'pair_priority')
            ).permutation(len(pairs))
            pair_priority = np.empty(len(pairs), dtype=int)
            pair_priority[random_order] = np.arange(len(pairs))
            for method in METHODS:
                snapshots, acquired, cursor, decision = simulate(
                    scores, pairs, perm[:, repeat], events[:, repeat],
                    evidence[:, repeat], method, priority=pair_priority)
                for budget_fraction, snapshot in zip(FRACTIONS, snapshots):
                    rows.append(dict(language=language, repeat=repeat,
                                     method=method, fraction=budget_fraction,
                                     pairs=len(pairs), systems=len(names),
                                     items=len(items), **snapshot))
            if (repeat + 1) % 4 == 0:
                print(f'{language}: {repeat + 1}/{repeats} schedules analyzed', flush=True)
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        with (output / 'replicates.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        meta = dict(master=master, repeats=repeats, languages=list(languages),
                    threshold_units=CAP // Q, alpha_family=0.05,
                    source_provenance_commit=provenance['pinned_commit'],
                    matrix_hashes={record['language_pair']: record['matrix_sha256']
                                   for record in provenance['datasets']
                                   if record['language_pair'] in languages})
        (output / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
    for language in languages:
        print(f'\n{language}')
        for fraction in FRACTIONS:
            print(f'  budget={fraction:.0%}')
            for method in METHODS:
                subset = [x for x in rows if x['language'] == language
                          and x['fraction'] == fraction and x['method'] == method]
                print(f'    {method:14s} correct={np.mean([x["correct"] for x in subset]):6.2f}'
                      f' wrong={sum(x["wrong"] for x in subset):d}'
                      f' unresolved={np.mean([x["unresolved"] for x in subset]):6.2f}',
                      flush=True)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--languages', nargs='+', default=['en-de'])
    parser.add_argument('--repeats', type=int, default=12)
    parser.add_argument('--output', default='results/stage14_exploratory')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('Positive repeats required')
    run(args.languages, args.repeats, args.output)
