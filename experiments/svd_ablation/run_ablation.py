"""Run all original WMT23 cases with original seeds and 100 paired repeats."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

from ablation import ROOT, evaluate_arm
from stage9_common import verify_protocol, build_cases, write_csv
from stage8_common import decisions
from certify_stage9 import load_certificate

METRICS = ('mean_queries', 'mse', 'mae', 'residual_mean', 'residual_variance',
           'simultaneous_coverage', 'stopped_absolute_error')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(job):
    case, history, y, repeats = job
    certdir = ROOT.parent / 'stage9' / 'certificates_reference'
    cert, raw, cal = load_certificate(certdir, case['n'], verify_runtime=False)
    alpha = Fraction(cert['prediction_error_numerator'], cert['prediction_error_denominator'])
    rows, traces = [], []
    for use_svd in (True, False):
        trace, metrics = evaluate_arm(history, y, repeats, case['raw_seed'], raw, cal,
                                      alpha, use_svd, pruned=True)
        # Both arms generate their queries independently from the identical seed.
        traces.append(trace)
        decision = decisions(trace['prediction_counts'] / case['n'], float(y.mean()))
        for i in range(repeats):
            row = {k: case[k] for k in ('case_id', 'scenario', 'language_pair', 'target_system', 'n')}
            row.update(arm='svd' if use_svd else 'no_svd', repeat=i,
                       mean_queries=int(decision['stop_queries'][i]),
                       simultaneous_coverage=int(decision['simultaneous_coverage'][i]),
                       stopped_absolute_error=float(decision['stopped_absolute_error'][i]))
            row.update({k: float(v[i]) for k, v in metrics.items()})
            rows.append(row)
    np.testing.assert_array_equal(traces[0]['selected'], traces[1]['selected'])
    ledger_hash = hashlib.sha256(np.asarray(traces[0]['selected'], dtype='<i4').tobytes()).hexdigest()
    return case, rows, ledger_hash


def summarize(targets):
    result = []
    for scenario in sorted({r['scenario'] for r in targets}):
        languages = sorted({r['language_pair'] for r in targets})
        for language in languages + ['overall']:
            for arm in ('svd', 'no_svd'):
                groups = [[r for r in targets if r['scenario'] == scenario and
                           r['language_pair'] == pair and r['arm'] == arm]
                          for pair in (languages if language == 'overall' else [language])]
                row = dict(scenario=scenario, language_pair=language, arm=arm)
                row.update({m: float(np.mean([np.mean([r[m] for r in g]) for g in groups]))
                            for m in METRICS})
                result.append(row)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, default=ROOT / 'results_reference')
    p.add_argument('--workers', type=int, default=2)
    args = p.parse_args()
    if args.workers < 1:
        p.error('workers must be positive')
    if args.output.exists():
        p.error('Use a new output directory')
    _, datasets = verify_protocol()
    cases = build_cases(datasets)
    for n in sorted({c['n'] for c, _, _ in cases}):
        load_certificate(ROOT.parent / 'stage9' / 'certificates_reference', n, verify_runtime=True)
    source_paths = sorted((ROOT.parent).glob('stage*/*.py')) + sorted(ROOT.glob('*.py'))
    source_hashes = {str(x.relative_to(ROOT.parent)): digest(x) for x in source_paths}
    reference_meta = json.loads((ROOT.parent / 'stage9/results_reference/run_metadata.json').read_text())
    args.output.mkdir(parents=True)
    start = time.perf_counter()
    meta = dict(status='running', repeats=100, completed_cases=0, method_trajectories=0,
                cases=[c for c, _, _ in cases],
                source_sha256=source_hashes, python=platform.python_version(), numpy=np.__version__,
                base_commit=subprocess.check_output(['git', '-c', 'safe.directory=' +
                    str(ROOT.parents[1]).replace('\\', '/'), 'rev-parse', 'HEAD'], text=True).strip(),
                protocol_sha256=digest(ROOT / 'PROTOCOL.md'),
                threads={k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')})
    (args.output / 'run_metadata.json').write_text(json.dumps(meta, indent=2) + '\n')

    def record_failure(kind, error, traceback):
        meta.update(status='interrupted' if kind is KeyboardInterrupt else 'failed',
                    error_type=kind.__name__, error=str(error))
        (args.output / 'run_metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
        sys.__excepthook__(kind, error, traceback)

    sys.excepthook = record_failure
    trials, hashes = [], {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for case, rows, ledger_hash in pool.map(run_case, [(c, h, y, 100) for c, h, y in cases]):
            if ledger_hash != reference_meta['raw_stream_sha256'][case['case_id']]:
                raise AssertionError('Query stream differs from Stage 9 reference')
            trials.extend(rows)
            hashes[case['case_id']] = ledger_hash
            meta.update(completed_cases=len(hashes), method_trajectories=len(trials),
                        raw_stream_sha256=hashes)
            (args.output / 'run_metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
            print(f"{len(hashes)}/{len(cases)} {case['scenario']} {case['language_pair']} {case['target_system']}", flush=True)
    targets = []
    for case, _, _ in cases:
        for arm in ('svd', 'no_svd'):
            group = [r for r in trials if r['case_id'] == case['case_id'] and r['arm'] == arm]
            row = {k: group[0][k] for k in ('case_id', 'scenario', 'language_pair', 'target_system', 'n', 'arm')}
            row.update({m: float(np.mean([r[m] for r in group])) for m in METRICS})
            targets.append(row)
    # Validate the unmodified arm against all published target-level label costs.
    import csv
    with (ROOT.parent / 'stage9/results_reference/by_target.csv').open(newline='') as handle:
        reference = {r['case_id']: float(r['mean_queries']) for r in csv.DictReader(handle)
                     if r['method'] == 'budget_prediction95'}
    for row in targets:
        if row['arm'] == 'svd':
            np.testing.assert_allclose(row['mean_queries'], reference[row['case_id']], rtol=0, atol=1e-12)
    summary = summarize(targets)
    comparisons = []
    for scenario in sorted({r['scenario'] for r in trials}):
        groups = [r for r in summary if r['scenario'] == scenario and r['language_pair'] == 'overall']
        svd, no = ({r['arm']: r for r in groups}[a] for a in ('svd', 'no_svd'))
        pair_diffs = []
        for language in sorted({r['language_pair'] for r in trials}):
            ids = [c['case_id'] for c, _, _ in cases if c['scenario'] == scenario and c['language_pair'] == language]
            weights = 1 / (3 * len(ids))
            for case_id in ids:
                a = np.array([r['mean_queries'] for r in trials if r['case_id'] == case_id and r['arm'] == 'svd'])
                b = np.array([r['mean_queries'] for r in trials if r['case_id'] == case_id and r['arm'] == 'no_svd'])
                pair_diffs.append(weights * (a - b))
        # Keep shared repeat indices across targets/languages in the MCSE.
        differences = np.sum(pair_diffs, axis=0)
        comparisons.append(dict(scenario=scenario, svd_minus_no_svd_labels=float(differences.mean()),
            svd_label_change_percent=100 * (svd['mean_queries'] / no['mean_queries'] - 1),
            paired_repeat_block_mcse=float(np.std(differences, ddof=1) / 10),
            target_wins=sum(r['mean_queries'] < next(q['mean_queries'] for q in targets if
                q['case_id'] == r['case_id'] and q['arm'] == 'no_svd') for r in targets
                if r['scenario'] == scenario and r['arm'] == 'svd')))
    for name, rows in (('per_trial.csv', trials), ('by_target.csv', targets),
                       ('summary.csv', summary), ('comparison.csv', comparisons)):
        write_csv(args.output / name, rows)
    for path, expected in source_hashes.items():
        assert digest(ROOT.parent / path) == expected, 'Source changed during run'
    meta.update(status='complete', runtime_seconds=time.perf_counter() - start,
                completed_cases=len(cases), trajectories=len(trials), raw_stream_sha256=hashes,
                checks=dict(paired_ledgers=True, original_ledgers=True,
                            original_svd_target_costs=True, sources_unchanged=True),
                artifact_sha256={x.name: digest(x) for x in args.output.glob('*.csv')})
    (args.output / 'run_metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(comparisons, indent=2), flush=True)


if __name__ == '__main__':
    main()
