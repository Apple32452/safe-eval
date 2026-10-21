"""Frozen small synthetic experiment. Never imports or loads a WMT dataset."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ[key] = '1'
import csv
import hashlib
from itertools import combinations
import json
from pathlib import Path
import platform
import subprocess
import time
import numpy as np
from joint import run, uniform_path
from baselines import stage22, per_system

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'results_reference'
MASTER = 20261029
METHODS = ('stage22', 'per_system', 'joint_diagonal', 'joint_covariance', 'joint_adaptive')


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    return {p.name:digest(p) for p in sorted(ROOT.iterdir()) if p.suffix in ('.py', '.md')}


def prior_sources():
    return {p.relative_to(ROOT.parents[1]).as_posix():digest(p) for directory in ROOT.parent.iterdir()
            if directory.is_dir() and directory.name.startswith('stage') and directory != ROOT
            for p in directory.iterdir() if p.is_file()}


def dump(path, value): path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def prepare():
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(MASTER); fixtures = {}; cases = []
    for m, n in ((4, 8), (3, 24)):
        for family in ('correlated_strong', 'independent_strong', 'correlated_weak', 'antagonistic'):
            u = rng.random(n); probabilities = np.linspace(.9, .1, m)
            if family == 'correlated_weak': probabilities = np.linspace(.6, .4, m)
            if family == 'independent_strong': x = rng.random((n, m)) < probabilities
            elif family == 'antagonistic': x = np.stack([(u if v%2==0 else 1-u)<probabilities[v] for v in range(m)], axis=1)
            else: x = u[:, None] < probabilities
            aux = np.clip(.15+.7*x+.25*rng.normal(size=(n, m)), 0, 1)
            name = f'{m}x{n}_{family}'; fixtures[name] = x.astype(np.int64); fixtures[name+'_aux'] = aux
            for graph in (('star', 'ring', 'complete') if m==4 else ('star', 'complete')):
                if graph=='star': edges = [(0, v) for v in range(1, m)]
                elif graph=='complete': edges = list(combinations(range(m), 2))
                else: edges = sorted({tuple(sorted((v, (v+1)%m))) for v in range(m)})
                for history in ('aligned', 'uninformative', 'reversed'):
                    cases.append(dict(matrix=name, graph=graph, history=history, edges=edges, systems=m, items=n))
    np.savez_compressed(OUT/'fixtures.npz', **fixtures)
    lock = dict(master_seed=MASTER, repeats=20, cases=cases, fixtures_sha256=digest(OUT/'fixtures.npz'),
                source_sha256=sources(), previous_stage_sha256=prior_sources(),
                python=platform.python_version(), numpy=np.__version__)
    dump(OUT/'LOCK.json', lock)
    print(f'Prepared {len(cases)} cells, 20 paired paths per cell, all fixtures frozen.', flush=True)
    return lock


def key_hash(result):
    h = hashlib.sha256()
    for key in sorted(result):
        a = np.asarray(result[key]); h.update(key.encode()); h.update(str(a.dtype).encode()); h.update(a.tobytes())
    return h.hexdigest()


def main():
    if not (OUT/'LOCK.json').exists(): lock = prepare()
    else: lock = json.loads((OUT/'LOCK.json').read_text())
    assert sources() == lock['source_sha256'], 'Frozen source differs'
    assert prior_sources() == lock['previous_stage_sha256']
    assert digest(OUT/'fixtures.npz') == lock['fixtures_sha256']
    started = time.perf_counter(); rows = []; uniform_cache = {}; replay = []
    with np.load(OUT/'fixtures.npz') as fixtures:
        for ci, case in enumerate(lock['cases']):
            x = fixtures[case['matrix']]; aux = fixtures[case['matrix']+'_aux']; edges = np.array(case['edges'])
            n, m = x.shape
            history = aux if case['history']=='aligned' else 1-aux if case['history']=='reversed' else np.full_like(aux, .5)
            for repeat in range(lock['repeats']):
                seed_material = f'{MASTER}|{case["matrix"]}|{case["graph"]}|{repeat}'
                seed = int.from_bytes(hashlib.sha256(seed_material.encode()).digest()[:8], 'little')
                rng = np.random.default_rng(seed); uniforms = rng.random(n); path = uniform_path(uniforms, n)
                orders = np.array([rng.permutation(m) for _ in range(n)])
                truth = np.sign(x.sum(axis=0)[edges[:, 0]]-x.sum(axis=0)[edges[:, 1]])
                for method in METHODS:
                    cache_key = (case['matrix'], case['graph'], repeat, method)
                    if method!='joint_adaptive' and cache_key in uniform_cache:
                        row = dict(uniform_cache[cache_key], history=case['history']); rows.append(row); continue
                    if method in ('stage22', 'per_system'):
                        result = (stage22 if method=='stage22' else per_system)(x, edges, path, orders)
                        cost, decision = result['completion_cost'], result['decision']
                        covered = None
                        trace_hash = hashlib.sha256(repr(result['acquired']).encode()).hexdigest()
                    else:
                        result = run(n, m, lambda i:x[i], history, uniforms, edges,
                                     covariance=method!='joint_diagonal', adaptive=method=='joint_adaptive')
                        cost, decision = result['cost'], result['decisions']
                        idx = int(np.ravel_multi_index(tuple(x.sum(axis=0)), (n+1,)*m))
                        covered = bool(np.unpackbits(result['masks'], axis=1)[:, idx].all())
                        trace_hash = key_hash(result)
                        if repeat==0 and case['history']=='aligned':
                            duplicate = run(n, m, lambda i:x[i], history, uniforms, edges,
                                            covariance=method!='joint_diagonal', adaptive=method=='joint_adaptive')
                            assert key_hash(duplicate) == trace_hash
                            replay.append(f'{case["matrix"]}|{case["graph"]}|{method}')
                    row = dict(matrix=case['matrix'], graph=case['graph'], history=case['history'], systems=m, items=n,
                               repeat=repeat, method=method, cost=int(cost), fraction=float(cost/(n*m)),
                               any_wrong=int(np.any(decision!=truth)), joint_covered='' if covered is None else int(covered),
                               trace_hash=trace_hash)
                    rows.append(row)
                    if method!='joint_adaptive': uniform_cache[cache_key] = row
            print(f'{ci+1}/{len(lock["cases"])} {case["matrix"]} {case["graph"]} {case["history"]}', flush=True)
    assert sources() == lock['source_sha256']
    assert prior_sources() == lock['previous_stage_sha256']
    with (OUT/'trials.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    dump(OUT/'VERIFICATION.json', dict(status='complete', rows=len(rows), seconds=time.perf_counter()-started,
         source_lock_verified=True, previous_stage_files_unchanged=True, independently_recomputed_traces=replay,
         any_wrong=sum(r['any_wrong'] for r in rows),
         joint_coverage_failures=sum(r['joint_covered']==0 for r in rows),
         warning='History duplicates of uniform methods are not independent replications; small synthetic checks do not prove coverage.'))
    print('Complete',len(rows),'rows', flush=True)


if __name__ == '__main__': main()
