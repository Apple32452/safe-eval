"""Reconstruct saved ledgers and test integer-completion null expectations."""
import argparse
import hashlib
import json
from functools import lru_cache
from itertools import permutations, product
from pathlib import Path

import numpy as np

from controls import (METHODS, USE, paired_update, rebalanced_update, run_block)
from joint_order import DIRECTED, IMPLIED, ORDERS, PAIRS, state_update
from run_study import ALPHA, GRAPHS, SCENARIOS
from run_controls import summarize


def totals_and_masks(s, m):
    totals = np.asarray(list(product(*(range(int(a), int(a+b+1))
                                      for a, b in zip(s, m)))))
    mask = np.asarray([np.all(np.column_stack([totals[:, DIRECTED[i][0]] <=
                         totals[:, DIRECTED[i][1]] for i in ids]), axis=1)
                       for ids in IMPLIED])
    return totals, mask


@lru_cache(maxsize=10000)
def feasible_orders(s, m):
    return totals_and_masks(np.array(s), np.array(m))[1].any(axis=1)


def independent_decide(s, m, excluded, previous):
    out = previous.copy()
    survivors = np.asarray(ORDERS)[~excluded & feasible_orders(tuple(s), tuple(m))]
    for e, (a, b) in enumerate(PAIRS):
        if out[e] != 2:
            continue
        if s[a] > s[b]+m[b]: out[e] = 1
        elif s[a]+m[a] < s[b]: out[e] = -1
        elif m[a] == m[b] == 0: out[e] = int(np.sign(s[a]-s[b]))
        elif len(survivors):
            signs = set(np.sign(survivors[:, a]-survivors[:, b]).tolist())
            if signs == {1}: out[e] = 1
            elif signs == {-1}: out[e] = -1
    return out


def check_stop(stop, paid, decisions, truth, n):
    wrong = int(np.any(decisions != truth))
    expected = {'paid': paid, 'charged': 3*n if wrong else paid,
                'wrong': wrong, 'correct_completion': 1-wrong,
                'decisions': decisions.tolist()}
    for key, value in expected.items():
        if stop[key] != value:
            raise AssertionError(('Saved stop differs', key, stop[key], value))


def audit_rebalanced(case, row, metrics):
    scores = np.asarray(case['scores'])
    n = scores.shape[1]
    prior = tuple(SCENARIOS[case['scenario']][1])
    rng = np.random.default_rng(case['seed'] ^ 0xC0FFEE)
    unseen = [list(range(n)) for _ in range(3)]
    s, m = np.zeros(3, int), np.full(3, n)
    wealth = {g: np.zeros(13) for g in GRAPHS}
    excluded = {g: np.zeros(13, bool) for g in GRAPHS}
    decisions = {g: np.full(3, 2, int) for g in GRAPHS}
    finished, seen = set(), set()
    fallback = failed = 0
    truth = np.array([np.sign(scores[a].sum()-scores[b].sum()) for a, b in PAIRS])
    for t, entry in enumerate(row['rebalanced_trace']):
        update = state_update(tuple(s), tuple(m), prior, n)
        v = int(rng.choice(3, p=update['q']))
        item = unseen[v].pop(int(rng.integers(len(unseen[v]))))
        if (v, item, int(scores[v, item])) != (entry['row'], entry['item'], entry['value']):
            raise AssertionError('Changed cell acquisition')
        if (v, item) in seen: raise AssertionError('Repurchased a cell')
        seen.add((v, item))
        totals, masks = totals_and_masks(s, m)
        event_law = np.zeros((len(totals), 6))
        for j in range(3):
            if m[j]:
                event_law[:, 2*j+1] = update['q'][j]*(totals[:, j]-s[j])/m[j]
                event_law[:, 2*j] = update['q'][j]-event_law[:, 2*j+1]
        for graph in GRAPHS:
            if graph in finished: continue
            fit = rebalanced_update(tuple(s), tuple(m), prior, n, graph)
            fallback += fit['fallbacks']; failed += fit['failed_status']
            for w, factor in enumerate(fit['factors']):
                expectations = event_law[masks[w]] @ factor
                if len(expectations):
                    largest = float(expectations.max())
                    metrics['largest_null_expectation'] = max(metrics['largest_null_expectation'], largest)
                    metrics['cell_null_expectations'] += len(expectations)
                    if factor.min() < 0 or largest > 1+1e-10:
                        raise AssertionError('Invalid rebalanced factor')
            wealth[graph] += np.log(fit['factors'][:, 2*v+entry['value']])
        s[v] += entry['value']; m[v] -= 1
        for graph, edge_ids in GRAPHS.items():
            if graph in finished: continue
            excluded[graph] |= wealth[graph] >= np.log(1/ALPHA)
            decisions[graph] = independent_decide(s, m, excluded[graph], decisions[graph])
            ids = list(edge_ids)
            if np.all(decisions[graph][ids] != 2):
                check_stop(row['stops'][graph]['rebalanced_pair_order'], t+1,
                           decisions[graph][ids], truth[ids], n)
                finished.add(graph)
    if len(finished) != 2 or t+1 != max(row['stops'][g]['rebalanced_pair_order']['paid'] for g in GRAPHS):
        raise AssertionError('Incomplete or overlong rebalanced trace')
    if (fallback, failed) != (row['rebalanced_fallbacks'], row['rebalanced_failed_status']):
        raise AssertionError('Numerical diagnostic mismatch')


def audit_block(case, row, graph, method, metrics):
    scores = np.asarray(case['scores'])
    n = scores.shape[1]; prior = SCENARIOS[case['scenario']][1]
    saved = row['stops'][graph][method]
    s, m, counts = np.zeros(3, int), np.full(3, n), np.zeros((6, 3), int)
    logs, excluded, decisions = np.zeros(6), np.zeros(13, bool), np.full(3, 2, int)
    seen, paid, fallback, failed = set(), 0, 0, 0
    for step, entry in enumerate(saved['trace']):
        unresolved = [e for e in GRAPHS[graph] if decisions[e] == 2]
        active = sorted({v for e in unresolved for v in PAIRS[e]})
        item = case['stage22_order'][step]
        if not active or entry['active'] != active or entry['item'] != item:
            raise AssertionError('Invalid retirement or item order')
        if entry['values'] != [int(scores[v, item]) for v in active]:
            raise AssertionError('Changed observed score')
        for edge in unresolved:
            a, b = PAIRS[edge]
            for i in (DIRECTED.index((a, b)), DIRECTED.index((b, a))):
                u, v = DIRECTED[i]
                fit = paired_update(tuple(counts[i]), (prior[u], prior[v]), n)
                remaining = n-int(counts[i].sum())
                difference = int(counts[i, 2]-counts[i, 0])
                # Enumerate all possible residual differences and their zero mass.
                for negative in range(remaining+1):
                    for positive in range(remaining-negative+1):
                        if difference+positive-negative <= 0:
                            probabilities = np.array([negative, remaining-negative-positive,
                                                       positive])/remaining
                            expectation = float(probabilities @ fit['factor'])
                            metrics['paired_null_expectations'] += 1
                            metrics['largest_null_expectation'] = max(metrics['largest_null_expectation'], expectation)
                            if expectation > 1+1e-10 or fit['factor'].min() < 0:
                                raise AssertionError('Invalid paired factor')
                event = int(scores[u, item]-scores[v, item])+1
                logs[i] += np.log(fit['factor'][event]); counts[i, event] += 1
                fallback += fit['fallback']; failed += not fit['success']
        for v in active:
            if (v, item) in seen: raise AssertionError('Double charge')
            seen.add((v, item)); paid += 1
            s[v] += int(scores[v, item]); m[v] -= 1
        if method == 'paired_exact_closure':
            for w, ids in enumerate(USE[graph]):
                pooled = np.logaddexp.reduce(logs[list(ids)])-np.log(len(ids))
                excluded[w] |= pooled >= np.log(1/ALPHA)
            decisions = independent_decide(s, m, excluded, decisions)
        else:
            decisions = independent_decide(s, m, np.ones(13, bool), decisions)
            threshold = np.log(2*len(GRAPHS[graph])/ALPHA)
            for e in GRAPHS[graph]:
                if decisions[e] != 2: continue
                a, b = PAIRS[e]
                pos = logs[DIRECTED.index((a, b))] >= threshold
                neg = logs[DIRECTED.index((b, a))] >= threshold
                if pos != neg: decisions[e] = 1 if pos else -1
        if entry['decisions'] != decisions[list(GRAPHS[graph])].tolist():
            raise AssertionError('Saved decisions differ from independent replay')
    ids = list(GRAPHS[graph])
    if np.any(decisions[ids] == 2): raise AssertionError('Unfinished requested comparison')
    truth = np.array([np.sign(scores[a].sum()-scores[b].sum()) for a, b in PAIRS])
    check_stop(saved, paid, decisions[ids], truth[ids], n)
    if (fallback, failed) != (saved['unit_fallbacks'], saved['solver_failed_status']):
        raise AssertionError('Paired numerical diagnostic mismatch')


def small_audit():
    matrices = paths = 0
    largest_error = {g: {method: 0. for method in METHODS[1:]} for g in GRAPHS}
    for bits in product((0, 1), repeat=6):
        scores = np.array(bits).reshape(3, 2)
        matrices += 1
        for graph in GRAPHS:
            for method in METHODS[1:]:
                errors = []
                for order in permutations(range(2)):
                    run = run_block(scores, (.2, .5, .8), order, graph, method)
                    errors.append(run['wrong']); paths += 1
                    if run['paid'] != len({(v, r['item']) for r in run['trace'] for v in r['active']}):
                        raise AssertionError('Small-pool ledger mismatch')
                largest_error[graph][method] = max(largest_error[graph][method], np.mean(errors))
    if any(x > ALPHA+1e-10 for d in largest_error.values() for x in d.values()):
        raise AssertionError('Small exact familywise error failure')
    return {'status': 'passed', 'binary_matrices': matrices,
            'matrix_permutation_graph_method_paths': paths,
            'largest_fixed_matrix_familywise_error': largest_error}


def audit(source, folder):
    original = json.loads(source.read_text())
    rows = json.loads((folder/'cases.json').read_text())
    if len(rows) != len(original): raise AssertionError('Missing result rows')
    metrics = {'status': 'passed', 'matrices': len(rows), 'graph_method_results': 6*len(rows),
               'cell_null_expectations': 0, 'paired_null_expectations': 0,
               'largest_null_expectation': 0.}
    for i, (case, row) in enumerate(zip(original, rows)):
        if (case['scenario'], case['repeat']) != (row['scenario'], row['repeat']):
            raise AssertionError('Changed case pairing')
        audit_rebalanced(case, row, metrics)
        for graph in GRAPHS:
            for method in METHODS[1:]: audit_block(case, row, graph, method, metrics)
        if (i+1) % 20 == 0: print('audited', i+1, flush=True)
    if summarize(original, rows) != json.loads((folder/'summary.json').read_text()):
        raise AssertionError('Saved summary differs from audited costs')
    metadata = json.loads((folder/'metadata.json').read_text())
    if metadata['source_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest():
        raise AssertionError('Changed source archive')
    metrics['small_exact_audit'] = small_audit()
    metrics['original_expansion_gate'] = False
    return metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--small-only', action='store_true')
    args = parser.parse_args()
    report = small_audit() if args.small_only else audit(args.source, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
