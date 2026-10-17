"""Shared protocol, frozen imports and result handling for the Stage 8 ablation."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
STAGE7 = ROOT.parent / 'stage7'
if str(STAGE7) not in sys.path:
    sys.path.insert(0, str(STAGE7))

from prepare_wmt23 import load_data
from stage7_experiment import build_cases, write_csv, SCENARIOS

METHODS = ('published_ppr95', 'raw_count_grid', 'prediction_count_grid',
           'raw_reserve75', 'reserve_mix75', 'ppr_reserve75')
MIXTURES = ('raw_reserve75', 'reserve_mix75')
PAIRS = (('reserve_mix75', 'raw_reserve75'),
         ('prediction_count_grid', 'raw_count_grid'))
DELTA, EPSILON, WEIGHT = .05, .05, .75
METRICS = ('mean_queries', 'simultaneous_coverage', 'empty_ever_rate',
           'repair_before_stop_rate', 'stopped_error_over_epsilon_rate')


def read_csv(path):
    with Path(path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def verify_protocol():
    lock = json.loads((ROOT / 'PROTOCOL_LOCK.json').read_text())
    for name, expected in lock['code_sha256'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Locked Stage 8 file changed: ' + name)
    for name, expected in lock['stage7_sha256'].items():
        if hashlib.sha256((STAGE7 / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen Stage 7 file changed: ' + name)
    datasets, provenance = load_data(STAGE7 / 'data')
    if [r['matrix_sha256'] for r in provenance['datasets']] != lock['matrix_sha256']:
        raise ValueError('Locked data differ')
    return lock, datasets


def pack_curves(runs, diag):
    n = len(diag['selected'])
    endpoints = np.stack([np.stack([runs[m]['lower'], runs[m]['upper']]) for m in METHODS])
    dtype = np.int16 if n <= np.iinfo(np.int16).max else np.int32
    counts = np.rint(endpoints * n).astype(dtype)
    if not np.array_equal(counts / n, endpoints):
        raise ValueError('Curve encoding was not lossless')
    return dict(counts=counts, selected=np.asarray(diag['selected'], dtype=np.int32),
                repaired=np.asarray(diag['repaired'], dtype=np.uint8))


def unpack_curves(trace):
    n, repeats = trace['selected'].shape
    if trace['counts'].shape != (len(METHODS), 2, n, repeats):
        raise ValueError('Wrong confidence curve dimensions')
    if trace['repaired'].shape != (2, n, repeats):
        raise ValueError('Wrong repair dimensions')
    return {name: trace['counts'][i] / n for i, name in enumerate(METHODS)}


def decisions(curve, truth):
    lower, upper = curve
    precise = (upper >= lower) & (upper - lower <= 2 * EPSILON + 1e-12)
    if not precise.any(axis=0).all():
        raise ValueError('No valid precision stop')
    stop = precise.argmax(axis=0) + 1
    index = np.arange(len(stop))
    lo, hi = lower[stop - 1, index], upper[stop - 1, index]
    covered = ((lower <= truth + 1e-12) & (truth <= upper + 1e-12)).all(axis=0)
    error = np.abs((lo + hi) / 2 - truth)
    if not np.array_equal(lower[-1], np.full(len(stop), truth)) or not np.array_equal(upper[-1], lower[-1]):
        raise ValueError('Final finite-pool mean is not exact')
    if np.any(error[covered] > EPSILON + 1e-12):
        raise ValueError('Covered precision stop has excessive error')
    return dict(stop_queries=stop, stop_lower=lo, stop_upper=hi,
                simultaneous_coverage=covered.astype(int),
                empty_ever=(lower > upper).any(axis=0).astype(int),
                stopped_absolute_error=error)


def target_record(case, method, decision, repair):
    return dict(case_id=case['case_id'], scenario=case['scenario'],
                language_pair=case['language_pair'], target_system=case['target_system'],
                method=method, paths=len(decision['stop_queries']), n=case['n'],
                nominal_anytime_confidence=1 - DELTA * (WEIGHT if method == 'ppr_reserve75' else 1),
                mean_queries=float(decision['stop_queries'].mean()),
                simultaneous_coverage=float(decision['simultaneous_coverage'].mean()),
                empty_ever_rate=float(decision['empty_ever'].mean()),
                repair_before_stop_rate=float(repair.mean()),
                stopped_error_over_epsilon_rate=float((decision['stopped_absolute_error'] > EPSILON + 1e-12).mean()))


def aggregate(targets):
    output = []
    for scenario in SCENARIOS:
        for pair in sorted({r['language_pair'] for r in targets}):
            for method in METHODS:
                rows = [r for r in targets if (r['scenario'], r['language_pair'], r['method']) == (scenario, pair, method)]
                record = dict(scenario=scenario, language_pair=pair, method=method,
                              target_systems=len(rows), trajectories=sum(r['paths'] for r in rows))
                record.update({field: float(np.mean([r[field] for r in rows])) for field in METRICS})
                output.append(record)
    return output
