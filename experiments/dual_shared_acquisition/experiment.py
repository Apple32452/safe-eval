"""Frozen shared-comparison allocation and stratified finite-matrix screen."""
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
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'peer_cell_scale'))
from engine import (ALPHA, ColumnModel, after_evidence, edges_for, finish,
                    pair_factor, run_cells)
from study import distribution, run_block, stage22

SCENARIOS = ('aligned', 'homogeneous', 'reversed')
METHODS = ('dual', 'row_peer', 'peer_cell', 'ec2_weighted',
           'paired_exact_closure', 'stage22')
PATTERNS, HIGH = distribution('one_hot', 3)
LOW = .05*np.ones(8)/8
LOW[0] += .95


class StratifiedModel:
    def __init__(self, history, historical_strata, target_strata):
        self.models = [ColumnModel(history[:, historical_strata == s]) for s in (0, 1)]
        self.target_strata = np.asarray(target_strata)
        self.marginal = .75*self.models[0].marginal+.25*self.models[1].marginal

    def predict(self, observed, peer=True):
        prediction = np.empty(observed.shape, float)
        for s in (0, 1):
            mask = self.target_strata == s
            prediction[:, mask] = self.models[s].predict(observed[:, mask], peer=peer)
        return prediction

    def particles(self, observed, rng, count=256):
        result = np.empty((count,)+observed.shape, dtype=np.int8)
        for s in (0, 1):
            mask = self.target_strata == s
            result[:, :, mask] = self.models[s].particles(observed[:, mask], rng, count)
        return result


def seed_for(scenario, repeat, purpose):
    key = f'20261026|dual_shared_acquisition|{scenario}|{repeat}|{purpose}'
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'little')


def inputs(scenario, repeat, n=128):
    seeds = {p: seed_for(scenario, repeat, p) for p in
             ('history', 'target', 'strata', 'acquisition', 'particle', 'order')}
    strata = np.zeros(n, dtype=int)
    strata[np.random.default_rng(seeds['strata']).permutation(n)[:n//4]] = 1
    historical_strata = np.r_[np.zeros(1536, dtype=int), np.ones(512, dtype=int)]
    rng = np.random.default_rng
    historical = np.empty((3, 2048), int)
    target = np.empty((3, n), int)
    for s in (0, 1):
        hist_prior = (HIGH if s else LOW)
        if scenario == 'reversed':
            hist_prior = (LOW if s else HIGH)
        target_prior = HIGH if (s or scenario == 'homogeneous') else LOW
        historical[:, historical_strata == s] = PATTERNS[
            rng(seeds['history'] ^ (s+1)).choice(8, size=sum(historical_strata == s), p=hist_prior)].T
        target[:, strata == s] = PATTERNS[
            rng(seeds['target'] ^ (s+1)).choice(8, size=sum(strata == s), p=target_prior)].T
    if scenario == 'homogeneous':
        # The stratum labels still exist, but both historical and target
        # distributions are the same exchangeable one-hot generator.
        historical[:, historical_strata == 0] = PATTERNS[
            rng(seeds['history'] ^ 1).choice(8, size=sum(historical_strata == 0), p=HIGH)].T
    model = StratifiedModel(historical, historical_strata, strata)
    order = rng(seeds['order']).permutation(n)
    return target, model, seeds, order, strata


def dual_proposal(observed, predicted, edges, decisions):
    eligible = observed < 0
    active_edges = [e for e, d in zip(edges, decisions) if d == 2]
    active = np.zeros(observed.shape[0], bool)
    for a, b in active_edges:
        active[a] = active[b] = True
    eligible &= active[:, None]
    if not eligible.any():
        raise AssertionError('No eligible active cell')
    variance = predicted*(1-predicted)
    pieces = []
    for a, b in active_edges:
        piece = np.zeros(observed.shape, float)
        piece[a] = variance[a]*eligible[a]
        piece[b] = variance[b]*eligible[b]
        pieces.append(piece)
    if len(pieces) == 1:
        weighted = pieces[0]
    elif len(pieces) == 2:
        def objective(z):
            return -float(np.sqrt(z*pieces[0]+(1-z)*pieces[1]).sum()**2)
        optimum = minimize_scalar(objective, bounds=(0., 1.), method='bounded',
                                  options={'xatol': 1e-5})
        choices = (0., float(optimum.x), 1.)
        z = min(choices, key=objective)
        weighted = z*pieces[0]+(1-z)*pieces[1]
    else:
        raise AssertionError('The frozen screen has at most two comparisons')
    root = np.sqrt(weighted)
    if root.sum() <= 0:
        root = eligible.astype(float)
    q = .2*eligible/eligible.sum()+.8*root/root.sum()
    q /= q.sum()
    if np.any(q[eligible] <= 0) or np.any(q[~eligible] != 0):
        raise AssertionError('Failed predictable overlap')
    return q


def run_dual(scores, model, edges, seed):
    observed = np.full_like(scores, -1)
    decisions = np.full(len(edges), 2, int)
    logs = np.zeros((len(edges), 2))
    rng = np.random.default_rng(seed)
    trace = []
    for step in range(scores.size):
        predicted = model.predict(observed)
        q = dual_proposal(observed, predicted, edges, decisions)
        factors = {}
        for e, (a, b) in enumerate(edges):
            if decisions[e] == 2:
                factors[e] = (pair_factor(observed, predicted, q, a, b),
                              pair_factor(observed, predicted, q, b, a))
        selected = int(rng.choice(scores.size, p=q.ravel()))
        v, item = divmod(selected, scores.shape[1])
        value = int(scores[v, item])
        if observed[v, item] >= 0:
            raise AssertionError('Repurchased cell')
        increment = np.zeros_like(logs)
        peak = 0.
        for e, directions in factors.items():
            for d, (factor, bound) in enumerate(directions):
                increment[e, d] = np.log(factor[v, item, value])
                peak = max(peak, bound)
        observed[v, item] = value
        logs += increment
        decisions = after_evidence(observed, edges, decisions, logs)
        trace.append(dict(cell=selected, value=value, q=float(q[v, item]),
                          increments=increment.tolist(), peak=float(peak),
                          decisions=decisions.tolist()))
        if np.all(decisions != 2):
            return finish(scores, edges, decisions, step+1, trace)
    raise AssertionError('Full-pool completion failed')


def one_case(spec):
    scenario, repeat = spec
    scores, model, seeds, order, strata = inputs(scenario, repeat)
    edges = edges_for(3, 'star')
    outcomes = {}
    for method in METHODS:
        if method == 'dual':
            result = run_dual(scores, model, edges, seeds['acquisition'])
        elif method in ('row_peer', 'peer_cell', 'ec2_weighted'):
            result = run_cells(scores, model, edges, method,
                               seeds['acquisition'], seeds['particle'])
        elif method == 'paired_exact_closure':
            result = run_block(scores, tuple(model.marginal), order, 'star', method)
        else:
            result = stage22(scores, edges, order)
        outcomes[method] = result
    return dict(scenario=scenario, repeat=repeat, scores=scores.tolist(),
                seeds=seeds, order=order.tolist(), strata=strata.tolist(), methods=outcomes)


def summarize(cases):
    output = {}
    rng = np.random.default_rng(2026102603)
    for scenario in SCENARIOS:
        subset = sorted((c for c in cases if c['scenario'] == scenario),
                        key=lambda c: c['repeat'])
        count = len(subset)
        costs = {m: np.array([c['methods'][m]['charged'] for c in subset]) for m in METHODS}
        draw = rng.integers(count, size=(20000, count))
        tail = .025/(len(METHODS)-1) if scenario == 'aligned' else .025
        output[scenario] = dict(cases=count,
                                means={m: float(costs[m].mean()) for m in METHODS},
                                wrong={m: sum(c['methods'][m]['wrong'] for c in subset) for m in METHODS},
                                comparisons={})
        for base in METHODS[1:]:
            boot = 1-costs['dual'][draw].mean(axis=1)/costs[base][draw].mean(axis=1)
            output[scenario]['comparisons'][base] = dict(
                relative_saving=float(1-costs['dual'].mean()/costs[base].mean()),
                labels_saved=float((costs[base]-costs['dual']).mean()),
                interval=np.quantile(boot, [tail, 1-tail]).tolist())
    output['primary_gate'] = all(x['interval'][0] > 0 for x in output['aligned']['comparisons'].values())
    return output


def run(folder, workers):
    if folder.exists():
        raise ValueError('Results directory already exists')
    folder.mkdir(parents=True)
    specs = [(scenario, r) for scenario in SCENARIOS
             for r in range(1000, 1060 if scenario == 'aligned' else 1020)]
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one_case, spec): spec for spec in specs}
        cases = [f.result() for f in as_completed(futures)]
    cases.sort(key=lambda c: (SCENARIOS.index(c['scenario']), c['repeat']))
    summary = summarize(cases)
    meta = dict(protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                seconds=time.perf_counter()-start, cases=len(cases))
    with gzip.open(folder/'cases.json.gz', 'wt') as stream:
        json.dump(cases, stream, separators=(',', ':'))
    (folder/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (folder/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(json.dumps(dict(primary=summary['aligned'], gate=summary['primary_gate'], metadata=meta), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    run(args.output, args.workers)
