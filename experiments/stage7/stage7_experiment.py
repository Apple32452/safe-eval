"""Data/seed compatibility adapter; statistical engines remain unchanged."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from prepare_wmt23 import leave_one_out

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('aligned', 'permuted_history', 'reversed_history')
LEGACY_METHODS = ('legacy_trust201', 'legacy_gate201')

def keyed_seed(pair, target, master=20261017):
    return int.from_bytes(hashlib.sha256(f'{master}|{pair}|{target}'.encode()).digest()[:8], 'little')

def transform_history(history, scenario, pair):
    if scenario == 'aligned':
        return history.copy()
    if scenario == 'reversed_history':
        return 1-history
    if scenario == 'permuted_history':
        seed = keyed_seed(pair, 'history_permutation', 20261019)
        permutation = np.random.default_rng(seed).permutation(history.shape[1])
        return history[:, permutation].copy()
    raise ValueError('Unknown historical scenario')

def build_cases(datasets):
    cases = []
    for scenario in SCENARIOS:
        for pair, (scores, names, _) in sorted(datasets.items()):
            for target in names:
                history, background, index = leave_one_out(scores, names, target)
                history = transform_history(history, scenario, pair)
                case_id = hashlib.sha256(f'{scenario}|{pair}|{target}'.encode()).hexdigest()[:16]
                meta = dict(case_id=case_id, scenario=scenario, protocol='leave_one_out', language_pair=pair,
                    target_system=str(target), n=scores.shape[1], raw_seed=keyed_seed(pair, target),
                    background_systems=background.tolist(),
                    history_sha256=hashlib.sha256(np.asarray(history, dtype='<f8').tobytes()).hexdigest())
                cases.append((meta, history, scores[index].copy()))
    return cases

def load_stage6_reference(directory=ROOT):
    directory = Path(directory)
    manifest = json.loads((directory/'STAGE6_REFERENCE.json').read_text())
    path = directory/'stage6_comparison.csv'
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['comparison_sha256']:
        raise ValueError('Stage 6 comparator checksum failed')
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    lookup = {}
    for row in rows:
        key = (row['case_id'], int(row['repeat']))
        if key in lookup:
            raise ValueError('Repeated Stage 6 comparator row')
        lookup[key] = {name: int(row[name+'_stop']) for name in ('raw95','active10','random10')}
    expected = {(c['case_id'],j) for c in manifest['cases'] for j in range(manifest['repeats'])}
    if set(lookup) != expected:
        raise ValueError('Incomplete Stage 6 comparator alignment')
    return manifest, lookup

def pack_curves(runs, selected):
    """Lossless integer count endpoints plus original legacy floating endpoints."""
    from reserve_fallback import METHODS
    n = len(selected)
    count_methods = [name for name in METHODS if name not in LEGACY_METHODS]
    count_dtype = np.int16 if n <= np.iinfo(np.int16).max else np.int32
    counts = []
    for name in count_methods:
        endpoints = np.stack([runs[name]['lower'],runs[name]['upper']])
        encoded = np.rint(endpoints*n).astype(count_dtype)
        if not np.array_equal(encoded/n,endpoints):
            raise RuntimeError('Count-grid interval encoding is not lossless')
        counts.append(encoded)
    legacy = np.stack([np.stack([runs[name]['lower'],runs[name]['upper']]) for name in LEGACY_METHODS])
    return dict(counts=np.stack(counts),legacy=legacy,selected=np.asarray(selected,dtype=np.int32))

def unpack_curves(trace):
    from reserve_fallback import METHODS
    n = len(trace['selected'])
    count_methods = [name for name in METHODS if name not in LEGACY_METHODS]
    curves = {name:trace['counts'][j]/n for j,name in enumerate(count_methods)}
    curves.update({name:trace['legacy'][j] for j,name in enumerate(LEGACY_METHODS)})
    if any(v.shape != (2,n,trace['selected'].shape[1]) for v in curves.values()):
        raise ValueError('Wrong saved interval-curve shape')
    return curves

def nominal_confidence(method,delta=.05):
    weight = int(method.removeprefix('ppr_reserve'))/100 if method.startswith('ppr_reserve') else 1.
    return 1-delta*weight

def write_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def aggregate(rows):
    output=[]
    for scenario in SCENARIOS:
        for pair in sorted({r['language_pair'] for r in rows}):
            for method in sorted({r['method'] for r in rows}):
                selected=[r for r in rows if r['scenario']==scenario and r['language_pair']==pair and r['method']==method]
                record=dict(scenario=scenario,language_pair=pair,method=method,
                    target_systems=len(selected),trajectories=sum(r['paths'] for r in selected),
                    nominal_anytime_confidence=selected[0]['nominal_anytime_confidence'])
                for field in ('mean_queries','simultaneous_coverage','empty_ever_rate','repair_before_stop_rate',
                    'stopped_error_over_epsilon_rate','mean_paired_query_change_vs_raw95',
                    'shared_predictor_strength_at_stop','shared_gate_at_stop'):
                    record[field]=float(np.mean([r[field] for r in selected]))
                output.append(record)
    return output
