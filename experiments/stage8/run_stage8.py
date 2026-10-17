"""Run the locked, paired Stage 8 mechanism diagnostic."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np
from stage8_common import (METHODS, MIXTURES, build_cases, verify_protocol, pack_curves,
                           decisions, target_record, aggregate, write_csv)
from stage8_engine import evaluate_matched
from wmt_experiment import QueryOracle


def run_case(job):
    case, history, outcomes, repeats, output = job
    runs, diag = evaluate_matched(history, QueryOracle(outcomes, repeats), repeats, seed=case['raw_seed'])
    trace = pack_curves(runs, diag)
    np.savez_compressed(Path(output) / 'curves' / (case['case_id'] + '.npz'), **trace)
    targets, trials = [], []
    truth = float(outcomes.mean())
    for method in METHODS:
        curve = np.stack([runs[method]['lower'], runs[method]['upper']])
        decision = decisions(curve, truth)
        repair = np.zeros(repeats, dtype=int)
        if method in MIXTURES:
            flags = trace['repaired'][MIXTURES.index(method)]
            repair = (flags & (np.arange(case['n'])[:, None] < decision['stop_queries'][None, :])).any(axis=0).astype(int)
        record = target_record(case, method, decision, repair)
        targets.append(record)
        for j in range(repeats):
            trial = {field: record[field] for field in ('case_id', 'scenario', 'language_pair', 'target_system', 'method', 'n')}
            trial.update(repeat=j, true_mean=truth, repair_before_stop=int(repair[j]))
            trial.update({field: float(value[j]) if value.dtype.kind == 'f' else int(value[j]) for field, value in decision.items()})
            trials.append(trial)
    raw_hash = hashlib.sha256(np.asarray(diag['selected'], dtype='<i4').tobytes()).hexdigest()
    return case, targets, trials, raw_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=100)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--output', default='results/stage8_local')
    args = parser.parse_args()
    if min(args.repeats, args.workers) < 1:
        parser.error('repeats and workers must be positive')
    lock, datasets = verify_protocol()
    cases = build_cases(datasets)
    output = Path(args.output).resolve()
    if (output / 'run_metadata.json').exists():
        parser.error('Use a new output directory; existing run metadata must not be overwritten')
    (output / 'curves').mkdir(parents=True, exist_ok=True)
    meta = dict(status='running', repeats=args.repeats, workers=args.workers, cases=[c for c, _, _ in cases],
                methods=METHODS, protocol_lock=lock, python=platform.python_version(), numpy=np.__version__,
                stage7_reference_pairing=args.repeats == 100)
    metadata_path = output / 'run_metadata.json'
    metadata_path.write_text(json.dumps(meta, indent=2))
    jobs = [(c, h, y, args.repeats, str(output)) for c, h, y in cases]
    targets, trials, hashes = [], [], {}
    start = time.perf_counter()

    def collect(result):
        case, target, trial, digest = result
        targets.extend(target)
        trials.extend(trial)
        hashes[case['case_id']] = digest
        cost = {r['method']: r['mean_queries'] for r in target}
        print(f"{case['scenario']:17s} {case['language_pair']} {case['target_system']:28s} "
              f"raw95={cost['published_ppr95']:6.1f} zero={cost['raw_count_grid']:6.1f} "
              f"pred={cost['prediction_count_grid']:6.1f} zero_mix75={cost['raw_reserve75']:6.1f} "
              f"pred_mix75={cost['reserve_mix75']:6.1f}", flush=True)

    if args.workers == 1:
        for job in jobs:
            collect(run_case(job))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for future in as_completed([pool.submit(run_case, job) for job in jobs]):
                collect(future.result())
    order = lambda r: (r['scenario'], r['language_pair'], r['target_system'], r['method'], r.get('repeat', -1))
    targets.sort(key=order)
    trials.sort(key=order)
    write_csv(output / 'by_target.csv', targets)
    write_csv(output / 'per_trial.csv', trials)
    write_csv(output / 'summary.csv', aggregate(targets))
    meta.update(status='complete', completed_cases=len(cases), method_trajectories=len(trials),
                raw_stream_sha256=hashes, runtime_seconds=time.perf_counter() - start)
    metadata_path.write_text(json.dumps(meta, indent=2))
    print(f"Finished {len(cases)} cases and {len(trials)} method trajectories in {meta['runtime_seconds']:.1f}s. Results: {args.output}", flush=True)


if __name__ == '__main__':
    main()
