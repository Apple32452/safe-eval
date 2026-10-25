"""Predictable pair-factor rebalancing and exact common-prefix controls."""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'joint_order_gate'))
from joint_order import (DIRECTED, IMPLIED, ORDERS, PAIRS, decide,
                         possible_orders, state_update)
from run_study import ALPHA, GRAPHS, SCENARIOS, record_stop

METHODS = ('rebalanced_pair_order', 'paired_exact_closure',
           'paired_exact_bonferroni')
USE = {g: tuple(tuple(i for i in ids if tuple(sorted(DIRECTED[i])) in
                     {PAIRS[e] for e in edge_ids}) for ids in IMPLIED)
       for g, edge_ids in GRAPHS.items()}


def rebalance(factors, alt):
    """A predictable convex combination; feasibility holds for any weights."""
    f = np.vstack((np.ones(len(alt)), factors))
    if np.allclose(f, 1., rtol=0., atol=1e-12):
        return np.ones(len(alt)), False, True
    k = len(f)
    def objective(w):
        return -float(alt @ np.log(w @ f))
    result = minimize(objective, np.full(k, 1/k),
                      jac=lambda w: -(f @ (alt / (w @ f))),
                      method='SLSQP', bounds=[(0., 1.)]*k,
                      constraints=[{'type': 'eq', 'fun': lambda w: w.sum()-1,
                                    'jac': lambda w: np.ones(k)}],
                      options={'ftol': 1e-10, 'maxiter': 500})
    w = np.maximum(result.x, 0.)
    fallback = not np.isfinite(w).all() or w.sum() <= 0
    if not fallback:
        w /= w.sum()
        combined = w @ f
        fallback = float(alt @ np.log(combined)) < 0
    if fallback:
        combined = f[int(np.argmax(np.log(f) @ alt))].copy()
    return combined, fallback, bool(result.success)


@lru_cache(maxsize=30000)
def rebalanced_update(s_tuple, m_tuple, prior, n, graph):
    old = state_update(s_tuple, m_tuple, prior, n)
    alt = np.column_stack((old['q']*(1-old['pred']),
                           old['q']*old['pred'])).ravel()
    factors, fallback, failed = [], 0, 0
    for ids in USE[graph]:
        f, fb, ok = rebalance(old['pair'][list(ids)], alt)
        factors.append(f); fallback += fb; failed += not ok
    return {'factors': np.array(factors), 'fallbacks': int(fallback),
            'failed_status': int(failed)}


@lru_cache(maxsize=None)
def null_histograms(observed_difference, remaining):
    """Every integer completion, including paired-dependence extremes."""
    return np.asarray([(minus, remaining-minus-plus, plus)
                       for minus in range(remaining+1)
                       for plus in range(remaining-minus+1)
                       if observed_difference+plus-minus <= 0],
                      dtype=int).reshape(-1, 3)


@lru_cache(maxsize=30000)
def paired_update(counts_tuple, prior_pair, n):
    counts = np.asarray(counts_tuple)
    m = n-int(counts.sum())
    if m <= 0:
        raise ValueError('Cannot bet after pair exhaustion')
    d = int(counts[2]-counts[0])
    pa, pb = prior_pair
    prior = np.array([(1-pa)*pb, pa*pb+(1-pa)*(1-pb), pa*(1-pb)])
    alt = (counts+4*prior)/(counts.sum()+4)
    hist = null_histograms(d, m)
    if not len(hist):
        return {'factor': np.ones(3), 'prediction': alt,
                'fallback': False, 'success': True}
    rows = hist/m
    result = minimize(lambda f: -float(alt @ np.log(f)), np.ones(3),
                      jac=lambda f: -alt/f, method='SLSQP',
                      bounds=[(.001, 10000)]*3,
                      constraints=[{'type': 'ineq', 'fun': lambda f: 1-rows@f,
                                    'jac': lambda f: -rows}],
                      options={'ftol': 1e-10, 'maxiter': 500})
    f = result.x
    fallback = not np.isfinite(f).all() or np.any(f <= 0)
    if not fallback:
        f = f/((1+1e-9)*max(1., float(np.max(rows@f))))
        fallback = float(alt @ np.log(f)) < 0
    if fallback:
        f = np.ones(3)
    if np.max(rows@f) > 1+1e-12:
        raise AssertionError('Invalid exact paired factor')
    return {'factor': f, 'prediction': alt, 'fallback': bool(fallback),
            'success': bool(result.success)}


def block_decision(s, m, logs, excluded, previous, graph, method):
    if method == 'paired_exact_closure':
        pooled = np.array([logsumexp(logs[list(ids)])-np.log(len(ids))
                           for ids in USE[graph]])
        excluded = excluded | (pooled >= np.log(1/ALPHA)) | ~possible_orders(s, m)
        current = decide(s, m, excluded, previous)
    else:
        current = decide(s, m, np.ones(len(ORDERS), bool), previous)
        threshold = np.log(2*len(GRAPHS[graph])/ALPHA)
        for edge in GRAPHS[graph]:
            if current[edge] != 2:
                continue
            a, b = PAIRS[edge]
            positive = logs[DIRECTED.index((a, b))] >= threshold
            negative = logs[DIRECTED.index((b, a))] >= threshold
            if positive != negative:
                current[edge] = 1 if positive else -1
    return current, excluded


def run_block(scores, prior, order, graph, method, keep_trace=True):
    scores = np.asarray(scores, int)
    n = scores.shape[1]
    if scores.shape[0] != 3 or not np.isin(scores, (0, 1)).all():
        raise ValueError('Three binary score rows required')
    if sorted(order) != list(range(n)):
        raise ValueError('A full precommitted item permutation is required')
    s, m = np.zeros(3, int), np.full(3, n)
    counts = np.zeros((6, 3), int)
    logs, excluded = np.zeros(6), np.zeros(13, bool)
    decisions = np.full(3, 2, int)
    paid, trace, seen, fallback, failed = 0, [], set(), 0, 0
    for step, item in enumerate(order):
        unresolved = [e for e in GRAPHS[graph] if decisions[e] == 2]
        active = sorted({v for e in unresolved for v in PAIRS[e]})
        if not active:
            break
        directions = [i for i, pair in enumerate(DIRECTED)
                      if tuple(sorted(pair)) in {PAIRS[e] for e in unresolved}]
        # This entire dictionary is computed before reading this item's values.
        updates = {i: paired_update(tuple(counts[i]),
                   (prior[DIRECTED[i][0]], prior[DIRECTED[i][1]]), n)
                   for i in directions}
        values = {v: int(scores[v, item]) for v in active}
        for v, value in values.items():
            if (v, int(item)) in seen:
                raise AssertionError('Duplicate charge')
            seen.add((v, int(item)))
            s[v] += value; m[v] -= 1; paid += 1
        for i, update in updates.items():
            a, b = DIRECTED[i]
            event = values[a]-values[b]+1
            logs[i] += np.log(update['factor'][event])
            counts[i, event] += 1
            fallback += update['fallback']; failed += not update['success']
        decisions, excluded = block_decision(s, m, logs, excluded, decisions,
                                              graph, method)
        if keep_trace:
            trace.append({'item': int(item), 'active': active,
                          'values': [values[v] for v in active],
                          'decisions': decisions[list(GRAPHS[graph])].tolist()})
        if np.all(decisions[list(GRAPHS[graph])] != 2):
            break
    ids = list(GRAPHS[graph])
    if np.any(decisions[ids] == 2):
        raise AssertionError('Unresolved requested edge at exhaustion')
    truth = np.array([np.sign(scores[a].sum()-scores[b].sum()) for a, b in PAIRS])
    result = record_stop(paid, decisions[ids], truth[ids], n)
    result.update(trace=trace, unit_fallbacks=int(fallback),
                  solver_failed_status=int(failed))
    return result


def run_rebalanced(case):
    scores = np.array(case['scores'], int)
    n = scores.shape[1]
    prior = SCENARIOS[case['scenario']][1]
    rng = np.random.default_rng(case['seed'] ^ 0xC0FFEE)
    s, m = np.zeros(3, int), np.full(3, n)
    unseen = [list(range(n)) for _ in range(3)]
    logs = {g: np.zeros(13) for g in GRAPHS}
    excluded = {g: np.zeros(13, bool) for g in GRAPHS}
    decisions = {g: np.full(3, 2, int) for g in GRAPHS}
    stops, trace, fallback, failed = {}, [], 0, 0
    truth = np.array([np.sign(scores[a].sum()-scores[b].sum()) for a, b in PAIRS])
    for t in range(3*n):
        update = state_update(tuple(s), tuple(m), tuple(prior), n)
        new = {g: rebalanced_update(tuple(s), tuple(m), tuple(prior), n, g)
               for g in GRAPHS if g not in stops}
        v = int(rng.choice(3, p=update['q']))
        item = unseen[v].pop(int(rng.integers(len(unseen[v]))))
        value = int(scores[v, item])
        if t < len(case['trace']):
            old = case['trace'][t]
            if (v, item, value) != (old['row'], old['item'], old['value']):
                raise AssertionError('Changed original cell stream')
            np.testing.assert_allclose(update['q'], old['q'], rtol=0, atol=1e-14)
        s[v] += value; m[v] -= 1
        trace.append({'row': v, 'item': item, 'value': value})
        for g, fit in new.items():
            logs[g] += np.log(fit['factors'][:, 2*v+value])
            fallback += fit['fallbacks']; failed += fit['failed_status']
            excluded[g] |= (logs[g] >= np.log(1/ALPHA)) | ~possible_orders(s, m)
            decisions[g] = decide(s, m, excluded[g], decisions[g])
            ids = list(GRAPHS[g])
            if np.all(decisions[g][ids] != 2):
                stops[g] = record_stop(t+1, decisions[g][ids], truth[ids], n)
        if len(stops) == len(GRAPHS):
            break
    if len(stops) != len(GRAPHS):
        raise AssertionError('Rebalanced control did not complete')
    return {'stops': stops, 'trace': trace,
            'extra_prefix_cells': max(0, len(trace)-len(case['trace'])),
            'unit_fallbacks': fallback, 'solver_failed_status': failed}
