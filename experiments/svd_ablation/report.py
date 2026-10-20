"""Independently aggregate saved per-repeat results and write the findings."""
from __future__ import annotations

import csv
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
DIRECTORY = ROOT / 'results_reference'


def read(name):
    with (DIRECTORY / name).open(newline='') as f:
        return list(csv.DictReader(f))


def main():
    global DIRECTORY
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=DIRECTORY)
    parser.add_argument('--output', type=Path, default=ROOT / 'FINDINGS.md')
    args = parser.parse_args()
    directory = DIRECTORY = args.input
    meta = json.loads((directory / 'run_metadata.json').read_text())
    assert meta['status'] == 'complete'
    for name, expected in meta['artifact_sha256'].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
    trials, targets, summary = read('per_trial.csv'), read('by_target.csv'), read('summary.csv')
    assert len(trials) == 23400 and len(targets) == 234 and len(summary) == 24
    assert len({(r['case_id'], r['arm'], r['repeat']) for r in trials}) == 23400
    fields = ('mean_queries', 'mse', 'mae', 'residual_mean', 'residual_variance',
              'simultaneous_coverage', 'stopped_absolute_error')
    for target in targets:
        group = [r for r in trials if (r['case_id'], r['arm']) == (target['case_id'], target['arm'])]
        assert len(group) == 100
        for field in fields:
            np.testing.assert_allclose(float(target[field]), np.mean([float(r[field]) for r in group]), atol=1e-12, rtol=0)
    for trial in trials:
        assert 1 <= int(trial['mean_queries']) <= int(trial['n'])
        np.testing.assert_allclose(float(trial['mse']), float(trial['residual_variance']) +
                                   float(trial['residual_mean']) ** 2, atol=1e-12, rtol=0)
    for row in summary:
        languages = sorted({r['language_pair'] for r in targets}) if row['language_pair'] == 'overall' else [row['language_pair']]
        for field in fields:
            expected = np.mean([np.mean([float(r[field]) for r in targets if r['scenario'] == row['scenario']
                and r['arm'] == row['arm'] and r['language_pair'] == language]) for language in languages])
            np.testing.assert_allclose(float(row[field]), expected, atol=1e-12, rtol=0)
    lines = ['# SVD ablation findings', '',
             'All 117 original WMT23 cases were evaluated with 100 repeats per arm (23,400 trajectories).',
             'The SVD arm reproduced all 117 published Stage 9 mean label costs; both arms reproduced',
             'the original query-ledger hashes. Exact pruning equivalence was tested against',
             'the original engine in both arms on synthetic and real-pool paths.', '',
             'Means below weight languages equally, then systems equally. Lower MSE, MAE, residual',
             'variance and label cost are better. Prediction metrics use the full shared prequential',
             'path; label cost uses the original first precision stop.', '',
             '| History | Arm | Brier/MSE | MAE | Residual variance | Mean labels |',
             '| --- | --- | ---: | ---: | ---: | ---: |']
    for row in summary:
        if row['language_pair'] == 'overall':
            lines.append(f"| {row['scenario']} | {row['arm']} | {float(row['mse']):.6f} | {float(row['mae']):.6f} | {float(row['residual_variance']):.6f} | {float(row['mean_queries']):.3f} |")
    lines += ['', 'Paired label differences are SVD minus no-SVD. Negative differences favor SVD.', '',
              '| History | Label difference | Relative change | Repeat-block MCSE | Target wins / ties / losses |',
              '| --- | ---: | ---: | ---: | --- |']
    for comp in read('comparison.csv'):
        rows = [r for r in targets if r['scenario'] == comp['scenario'] and r['arm'] == 'svd']
        differences = [float(r['mean_queries']) - float(next(q['mean_queries'] for q in targets if q['case_id'] == r['case_id'] and q['arm'] == 'no_svd')) for r in rows]
        wins, ties, losses = (sum(d < 0 for d in differences), sum(d == 0 for d in differences), sum(d > 0 for d in differences))
        assert wins == int(comp['target_wins'])
        lines.append(f"| {comp['scenario']} | {float(comp['svd_minus_no_svd_labels']):+.3f} | {float(comp['svd_label_change_percent']):+.3f}% | {float(comp['paired_repeat_block_mcse']):.3f} | {wins} / {ties} / {losses} |")
    aligned = {r['arm']: r for r in summary if r['scenario'] == 'aligned' and r['language_pair'] == 'overall'}
    mse_change = 100*(float(aligned['svd']['mse'])/float(aligned['no_svd']['mse'])-1)
    var_change = 100*(float(aligned['svd']['residual_variance'])/float(aligned['no_svd']['residual_variance'])-1)
    cost_change = 100*(float(aligned['svd']['mean_queries'])/float(aligned['no_svd']['mean_queries'])-1)
    lines += ['', f'On aligned history, adding SVD changes Brier/MSE by {mse_change:+.3f}%,',
              f'residual variance by {var_change:+.3f}%, and average label cost by {cost_change:+.3f}%.',
              'These effects isolate adding SVD features within this fixed ridge/trust pipeline.',
              'See summary.csv for each language and coverage diagnostics, and by_target.csv for heterogeneity.', '',
              'This is a development-data ablation, not independent confirmation on a new release.',
              'Trust and stakes use identical update rules but their realized values may differ across arms.',
              'The MCSE measures query randomization on fixed recorded pools, not generalization to new',
              'systems, items or raters. Residual variance excludes bias; residual means and MSE are saved.',
              'Full-path diagnostics include labels after stopping only for analysis. Historical-label',
              'acquisition cost, human annotation time and computational speedup are not measured.', '',
              'Validation: six new ablation tests, all 61 existing stage tests, release-manifest checks,',
              'canonical-arm reference costs, ledger equality, exact pruning equivalence, independent',
              'per-repeat/target/summary aggregation and MSE = variance + squared bias checks.',
              'The saved artifacts contain metrics and hashes; full confidence curves are regenerated',
              'by rerunning the experiment. See TEST_RESULTS.txt and run_metadata.json for evidence.', '']
    args.output.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Audited all 23,400 records, 234 target rows and 24 summaries; wrote {args.output}.')


if __name__ == '__main__':
    main()
