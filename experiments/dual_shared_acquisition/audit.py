"""Replay the full shared-policy ledger and all matched controls."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from experiment import (ALPHA, HERE, METHODS, SCENARIOS, dual_proposal, edges_for,
                        inputs, one_case, pair_factor, summarize)


def replay_decisions(observed, edges, previous, logs):
    answer = previous.copy()
    totals = np.maximum(observed, 0).sum(axis=1)
    remaining = (observed < 0).sum(axis=1)
    threshold = np.log(2*len(edges)/ALPHA)
    for e, (a, b) in enumerate(edges):
        if answer[e] != 2:
            continue
        low = totals[a]-totals[b]-remaining[b]
        high = totals[a]+remaining[a]-totals[b]
        if low > 0:
            answer[e] = 1
        elif high < 0:
            answer[e] = -1
        elif remaining[a] == remaining[b] == 0:
            answer[e] = int(np.sign(totals[a]-totals[b]))
        elif (logs[e, 0] >= threshold) != (logs[e, 1] >= threshold):
            answer[e] = 1 if logs[e, 0] >= threshold else -1
    return answer


def audit_case(case):
    scores, model, seeds, order, strata = inputs(case['scenario'], case['repeat'])
    if (scores.tolist() != case['scores'] or seeds != case['seeds']
            or order.tolist() != case['order'] or strata.tolist() != case['strata']):
        raise AssertionError('Target or strata changed')
    saved = case['methods']['dual']
    observed = np.full_like(scores, -1)
    edges = edges_for(3, 'star')
    decisions = np.full(2, 2)
    logs = np.zeros((2, 2))
    rng = np.random.default_rng(seeds['acquisition'])
    checked = 0
    maximum = 0.
    for event in saved['trace']:
        predicted = model.predict(observed)
        q = dual_proposal(observed, predicted, edges, decisions)
        chosen = int(rng.choice(scores.size, p=q.ravel()))
        if chosen != event['cell']:
            raise AssertionError('Changed acquisition stream')
        v, item = divmod(chosen, scores.shape[1])
        value = int(scores[v, item])
        if observed[v, item] >= 0 or value != event['value'] or abs(q[v, item]-event['q']) > 1e-12:
            raise AssertionError('Repeated or incorrect acquisition')
        increments = np.zeros_like(logs)
        peak = 0.
        for e, (a, b) in enumerate(edges):
            if decisions[e] != 2:
                continue
            for d, (x, y) in enumerate(((a, b), (b, a))):
                f, bound = pair_factor(observed, predicted, q, x, y)
                if bound > 1+1e-12:
                    raise AssertionError('Null support failed')
                if scores[x].sum() <= scores[y].sum():
                    actual = np.take_along_axis(f, scores[:, :, None], axis=2)[:, :, 0]
                    expectation = float(np.sum(q*actual))
                    maximum = max(maximum, expectation)
                    checked += 1
                    if expectation > 1+1e-12:
                        raise AssertionError('Actual true-null factor failed')
                increments[e, d] = np.log(f[v, item, value])
                peak = max(peak, bound)
        np.testing.assert_allclose(increments, event['increments'], atol=1e-12, rtol=0)
        if abs(peak-event['peak']) > 1e-12:
            raise AssertionError('Saved null bound changed')
        observed[v, item] = value
        logs += increments
        decisions = replay_decisions(observed, edges, decisions, logs)
        if decisions.tolist() != event['decisions']:
            raise AssertionError('Decisions changed')
    if saved['paid'] != len(saved['trace']) or saved['wrong'] != int(any(
            decisions[e] != np.sign(scores[a].sum()-scores[b].sum())
            for e, (a, b) in enumerate(edges))):
        raise AssertionError('Final cost or truth changed')
    fresh = one_case((case['scenario'], case['repeat']))
    for method in METHODS:
        if fresh['methods'][method] != case['methods'][method]:
            raise AssertionError(f'Control changed: {method}')
    return len(saved['trace']), checked, maximum


def audit(folder, workers):
    with gzip.open(folder/'cases.json.gz', 'rt') as stream:
        cases = json.load(stream)
    metadata = json.loads((folder/'metadata.json').read_text())
    if metadata['protocol_sha256'] != hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest():
        raise AssertionError('Protocol changed after freeze')
    grid = [(scenario, r) for scenario in SCENARIOS
            for r in range(1000, 1060 if scenario == 'aligned' else 1020)]
    if [(c['scenario'], c['repeat']) for c in cases] != grid:
        raise AssertionError('Unexpected case grid')
    if json.loads((folder/'summary.json').read_text()) != summarize(cases):
        raise AssertionError('Aggregate changed')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        checks = list(pool.map(audit_case, cases))
    result = dict(status='passed', cases=len(cases), trajectories=len(cases)*len(METHODS),
                  paid_cells_checked=sum(x[0] for x in checks),
                  actual_null_factor_checks=sum(x[1] for x in checks),
                  largest_true_null_expectation=max(x[2] for x in checks),
                  wrong_trajectories=sum(m['wrong'] for c in cases for m in c['methods'].values()),
                  primary_gate=json.loads((folder/'summary.json').read_text())['primary_gate'])
    (folder/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    audit(args.input, args.workers)
