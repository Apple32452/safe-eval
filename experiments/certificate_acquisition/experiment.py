"""Frozen certificate-guided query policy and independent synthetic screen."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'peer_cell_scale'))
from engine import (ALPHA, ColumnModel, after_evidence, edges_for, finish,
                    pair_factor, proposal, run_cells)
from study import distribution, run_block, stage22

METHODS = ('certificate', 'row_peer', 'peer_cell', 'paired_exact_closure', 'stage22')
SCENARIOS = ('one_hot', 'independent', 'opposed', 'reversed')


def seed_for(scenario, repeat, purpose):
    message = f'20261026|certificate_acquisition|{scenario}|3|128|star|{repeat}|{purpose}'
    return int.from_bytes(hashlib.sha256(message.encode()).digest()[:8], 'little')


def inputs(scenario, repeat):
    patterns, prior = distribution(scenario, 3)
    seeds = {purpose: seed_for(scenario, repeat, purpose)
             for purpose in ('history', 'target', 'acquisition', 'particle', 'order')}
    rng = np.random.default_rng
    history = patterns[rng(seeds['history']).choice(len(prior), size=2048, p=prior)].T
    scores = patterns[rng(seeds['target']).choice(len(prior), size=128, p=prior)].T
    if scenario == 'reversed':
        history = 1-history
    order = rng(seeds['order']).permutation(128)
    return scores, ColumnModel(history), seeds, order


def certificate_proposal(observed, predicted, edges, decisions):
    """Look ahead under a row-uniform proposal, then recalibrate at actual q."""
    baseline = proposal(observed, predicted, edges, decisions, 'row_peer')
    eligible = baseline > 0
    totals = np.where(observed < 0, predicted, observed).sum(axis=1)
    weight = np.zeros_like(baseline)
    n = observed.shape[1]
    for edge, decision in zip(edges, decisions):
        if decision != 2:
            continue
        a, b = edge
        urgency = 1/max(abs(totals[a]-totals[b])/n, .1)
        for x, y in ((a, b), (b, a)):
            factors, _ = pair_factor(observed, predicted, baseline, x, y)
            expected_log = ((1-predicted)*np.log(factors[:, :, 0])
                            + predicted*np.log(factors[:, :, 1]))
            weight += urgency*np.maximum(expected_log, 0)*eligible
    if weight.sum() <= 0:
        weight = eligible.astype(float)
    q = .2*eligible/eligible.sum() + .8*weight/weight.sum()
    q /= q.sum()
    if not np.all(q[eligible] > 0) or np.any(q[~eligible] != 0):
        raise AssertionError('Acquisition lost positive overlap')
    return q


def run_certificate(scores, model, edges, seed):
    observed = np.full_like(scores, -1)
    decisions = np.full(len(edges), 2, dtype=int)
    logs = np.zeros((len(edges), 2))
    rng = np.random.default_rng(seed)
    trace = []
    for t in range(scores.size):
        predicted = model.predict(observed, peer=True)
        q = certificate_proposal(observed, predicted, edges, decisions)
        updates = {}
        for e, (a, b) in enumerate(edges):
            if decisions[e] == 2:
                updates[e] = (pair_factor(observed, predicted, q, a, b),
                              pair_factor(observed, predicted, q, b, a))
        selected = int(rng.choice(scores.size, p=q.ravel()))
        v, item = divmod(selected, scores.shape[1])
        if observed[v, item] >= 0:
            raise AssertionError('Purchased cell twice')
        value = int(scores[v, item])
        increments = np.zeros_like(logs)
        peak = 0.
        for e, directions in updates.items():
            for d, (factor, bound) in enumerate(directions):
                increments[e, d] = np.log(factor[v, item, value])
                peak = max(peak, bound)
        logs += increments
        observed[v, item] = value
        decisions = after_evidence(observed, edges, decisions, logs)
        trace.append(dict(cell=selected, value=value, q=float(q[v, item]),
                          increments=increments.tolist(), peak=float(peak),
                          decisions=decisions.tolist()))
        if np.all(decisions != 2):
            return finish(scores, edges, decisions, t+1, trace)
    raise AssertionError('Full-pool completion failed')


def one_case(spec):
    scenario, repeat = spec
    scores, model, seeds, order = inputs(scenario, repeat)
    edges = edges_for(3, 'star')
    methods = {}
    for method in METHODS:
        if method == 'certificate':
            result = run_certificate(scores, model, edges, seeds['acquisition'])
        elif method in ('row_peer', 'peer_cell'):
            result = run_cells(scores, model, edges, method,
                               seeds['acquisition'], seeds['particle'])
        elif method == 'paired_exact_closure':
            result = run_block(scores, tuple(model.marginal), order, 'star', method)
        else:
            result = stage22(scores, edges, order)
        methods[method] = result
    return dict(scenario=scenario, repeat=repeat, scores=scores.tolist(),
                seeds=seeds, order=order.tolist(), methods=methods)


def summarize(cases):
    result = {}
    rng = np.random.default_rng(2026102602)
    for scenario in SCENARIOS:
        subset = sorted((c for c in cases if c['scenario'] == scenario),
                        key=lambda c: c['repeat'])
        n = len(subset)
        costs = {m: np.array([c['methods'][m]['charged'] for c in subset]) for m in METHODS}
        ix = rng.integers(n, size=(20000, n))
        tail = .025/(len(METHODS)-1) if scenario == 'one_hot' else .025
        result[scenario] = {'cases': n, 'mean_charged': {m: float(costs[m].mean()) for m in METHODS},
                            'wrong': {m: sum(c['methods'][m]['wrong'] for c in subset) for m in METHODS},
                            'comparisons': {}}
        for base in METHODS[1:]:
            savings = 1-costs['certificate'][ix].mean(axis=1)/costs[base][ix].mean(axis=1)
            result[scenario]['comparisons'][base] = dict(
                relative_saving=float(1-costs['certificate'].mean()/costs[base].mean()),
                labels_saved=float((costs[base]-costs['certificate']).mean()),
                adjusted_interval=np.quantile(savings, [tail, 1-tail]).tolist())
    result['primary_gate'] = all(x['adjusted_interval'][0] > 0
                                 for x in result['one_hot']['comparisons'].values())
    return result


def run(output, workers):
    if output.exists():
        raise ValueError('Output exists; do not overwrite')
    output.mkdir(parents=True)
    specs = [(scenario, r) for scenario in SCENARIOS
             for r in range(1000, 1060 if scenario == 'one_hot' else 1020)]
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one_case, spec): spec for spec in specs}
        cases = [future.result() for future in as_completed(futures)]
    cases.sort(key=lambda c: (SCENARIOS.index(c['scenario']), c['repeat']))
    summary = summarize(cases)
    metadata = dict(protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
                    cases=len(cases), seconds=time.perf_counter()-started,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with gzip.open(output/'cases.json.gz', 'wt') as out:
        json.dump(cases, out, separators=(',', ':'))
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(dict(primary=summary['one_hot'], gate=summary['primary_gate'],
                          metadata=metadata), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    run(args.output, args.workers)
