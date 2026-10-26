"""Replay prior query paths for a conditional one-step variance diagnostic."""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'peer_cell_scale'))
from engine import ColumnModel, edges_for, proposal
from study import inputs as old_inputs
sys.path.insert(0, str(HERE.parent/'certificate_acquisition'))
from experiment import inputs as new_inputs


def within_row_proxy(a, q):
    """Return row-uniform value and best value keeping the same row masses."""
    eligible = q > 0
    if np.any(a[eligible] <= 0) or np.any(a[~eligible] != 0):
        raise ValueError('Expected positive eligible proxy weights')
    row_value = float(np.sum(a[eligible]/q[eligible]))
    best_value = 0.
    for v in range(q.shape[0]):
        mass = float(q[v].sum())
        if mass > 0:
            best_value += float(np.sqrt(a[v, eligible[v]]).sum()**2/mass)
    return row_value, best_value


def evaluate(path, old):
    with gzip.open(path, 'rt') as stream:
        cases = json.load(stream)
    ratios = []
    counted = 0
    method = 'peer_cell' if old else 'certificate'
    for case in cases:
        if old:
            if tuple(case['spec'][:4]) != ('one_hot', 3, 64, 'star'):
                continue
            scores, history, _, _ = old_inputs(tuple(case['spec']), False)
            model = ColumnModel(history)
        else:
            if case['scenario'] != 'one_hot':
                continue
            scores, model, _, _ = new_inputs(case['scenario'], case['repeat'])
        counted += 1
        observed = np.full_like(scores, -1)
        decisions = np.full(2, 2)
        edges = edges_for(3, 'star')
        for event in case['methods'][method]['trace']:
            predicted = model.predict(observed)
            q = proposal(observed, predicted, edges, decisions, 'row_peer')
            eligible = q > 0
            degree = np.zeros_like(q)
            active_edges = [edge for edge, d in zip(edges, decisions) if d == 2]
            if not active_edges:
                raise AssertionError('Query after all decisions complete')
            for a, b in active_edges:
                degree[a, eligible[a]] += 1/len(active_edges)
                degree[b, eligible[b]] += 1/len(active_edges)
            a = predicted*(1-predicted)*degree
            row_value, best_value = within_row_proxy(a, q)
            ratios.append(best_value/row_value)
            v, item = divmod(event['cell'], scores.shape[1])
            if observed[v, item] >= 0 or scores[v, item] != event['value']:
                raise AssertionError('Saved query path changed')
            observed[v, item] = event['value']
            decisions = np.array(event['decisions'])
    return dict(cases=counted, steps=len(ratios), mean_ratio=float(np.mean(ratios)),
                median_ratio=float(np.median(ratios)),
                p10_ratio=float(np.quantile(ratios, .1)),
                min_ratio=float(np.min(ratios)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--old', type=Path, required=True)
    parser.add_argument('--new', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(dict(previous=evaluate(args.old, True),
                          held_out=evaluate(args.new, False)), indent=2))
