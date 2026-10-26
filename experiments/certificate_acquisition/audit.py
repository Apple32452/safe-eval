"""Independent ledger replay and true fixed-null expectation check."""
from __future__ import annotations

import argparse
import gzip
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from experiment import (ALPHA, METHODS, SCENARIOS, certificate_proposal, inputs,
                        one_case, pair_factor, edges_for, summarize)


def decisions_from_ledger(observed, edges, previous, logs):
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
    scenario, repeat = case['scenario'], case['repeat']
    scores, model, seeds, order = inputs(scenario, repeat)
    if scores.tolist() != case['scores'] or seeds != case['seeds'] or order.tolist() != case['order']:
        raise AssertionError('Case inputs changed')
    edges = edges_for(3, 'star')
    saved = case['methods']['certificate']
    observed = np.full_like(scores, -1)
    decisions = np.full(len(edges), 2, int)
    logs = np.zeros((len(edges), 2))
    rng = np.random.default_rng(seeds['acquisition'])
    null_checks = 0
    maximum = 0.
    for row in saved['trace']:
        predicted = model.predict(observed)
        q = certificate_proposal(observed, predicted, edges, decisions)
        selected = int(rng.choice(scores.size, p=q.ravel()))
        if selected != row['cell']:
            raise AssertionError('Selection stream changed')
        v, item = divmod(selected, 128)
        value = int(scores[v, item])
        if observed[v, item] >= 0 or value != row['value'] or abs(q[v, item]-row['q']) > 1e-13:
            raise AssertionError('Paid observation or probability changed')
        increments = np.zeros_like(logs)
        peak = 0.
        for e, (a, b) in enumerate(edges):
            if decisions[e] != 2:
                continue
            for d, (x, y) in enumerate(((a, b), (b, a))):
                factors, bound = pair_factor(observed, predicted, q, x, y)
                if bound > 1+1e-12:
                    raise AssertionError('Null support violated')
                if scores[x].sum() <= scores[y].sum():
                    actual = np.take_along_axis(factors, scores[:, :, None], axis=2)[:, :, 0]
                    expected = float(np.sum(q*actual))
                    maximum = max(maximum, expected)
                    if expected > 1+1e-12:
                        raise AssertionError('True fixed-null expectation exceeded one')
                    null_checks += 1
                increments[e, d] = np.log(factors[v, item, value])
                peak = max(peak, bound)
        np.testing.assert_allclose(increments, row['increments'], atol=1e-12, rtol=0)
        if abs(peak-row['peak']) > 1e-12:
            raise AssertionError('Calibration changed')
        observed[v, item] = value
        logs += increments
        decisions = decisions_from_ledger(observed, edges, decisions, logs)
        if decisions.tolist() != row['decisions']:
            raise AssertionError('Final decision changed')
    if saved['paid'] != len(saved['trace']) or saved['wrong'] != int(any(
            decisions[e] != np.sign(scores[a].sum()-scores[b].sum())
            for e, (a, b) in enumerate(edges))):
        raise AssertionError('Cost or truth changed')
    again = one_case((scenario, repeat))
    for method in METHODS:
        if again['methods'][method] != case['methods'][method]:
            raise AssertionError(f'Control trajectory changed: {method}')
    return len(saved['trace']), null_checks, maximum


def audit(folder, workers):
    import hashlib
    from experiment import HERE
    with gzip.open(folder/'cases.json.gz', 'rt') as inp:
        cases = json.load(inp)
    meta = json.loads((folder/'metadata.json').read_text())
    if meta['protocol_sha256'] != hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest():
        raise AssertionError('Protocol changed after freeze')
    if len(cases) != 120 or [(c['scenario'], c['repeat']) for c in cases] != [
            (scenario, r) for scenario in SCENARIOS
            for r in range(1000, 1060 if scenario=='one_hot' else 1020)]:
        raise AssertionError('Unexpected case grid')
    if json.loads((folder/'summary.json').read_text()) != summarize(cases):
        raise AssertionError('Summary changed')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        checks = list(pool.map(audit_case, cases))
    output = dict(status='passed', cases=len(cases), trajectories=len(cases)*len(METHODS),
                  candidate_paid_cells=sum(x[0] for x in checks),
                  actual_null_factor_checks=sum(x[1] for x in checks),
                  largest_true_null_expectation=max(x[2] for x in checks),
                  wrong_trajectories=sum(m['wrong'] for c in cases for m in c['methods'].values()),
                  primary_gate=json.loads((folder/'summary.json').read_text())['primary_gate'])
    (folder/'audit.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    audit(args.input, args.workers)
