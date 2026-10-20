"""Audit the completed dense run without rewriting its failed-run metadata.

This verifies saved metrics, not a frozen-source rerun or a full-curve replay.
"""
from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from ablation import ROOT
from stage9_common import verify_protocol, build_cases

DIRECTORY = ROOT / 'results_reference'
FIELDS = ('mean_queries', 'mse', 'mae', 'residual_mean', 'residual_variance',
          'simultaneous_coverage', 'stopped_absolute_error')


def read(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def close(actual, expected):
    np.testing.assert_allclose(float(actual), expected, rtol=0, atol=1e-12)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    meta = json.loads((DIRECTORY / 'run_metadata.json').read_text())
    metadata_hash = sha(DIRECTORY / 'run_metadata.json')
    _, datasets = verify_protocol()
    cases = build_cases(datasets)
    assert [c for c, _, _ in cases] == meta['cases']
    by_id = {c['case_id']: c for c, _, _ in cases}
    trials = read(DIRECTORY / 'per_trial.csv')
    targets = read(DIRECTORY / 'by_target.csv')
    summary = read(DIRECTORY / 'summary.csv')
    comparisons = read(DIRECTORY / 'comparison.csv')
    assert len(cases) == 117 and len(trials) == 23400
    assert len(targets) == 234 and len(summary) == 24 and len(comparisons) == 3
    groups = defaultdict(list)
    identities = set()
    for row in trials:
        case = by_id[row['case_id']]
        for field in ('scenario', 'language_pair', 'target_system'):
            assert row[field] == case[field]
        assert int(row['n']) == case['n'] and row['arm'] in ('svd', 'no_svd')
        identity = row['case_id'], row['arm'], int(row['repeat'])
        assert identity not in identities
        identities.add(identity)
        assert 1 <= float(row['mean_queries']) <= case['n']
        assert float(row['mean_queries']).is_integer()
        assert float(row['simultaneous_coverage']) in (0, 1)
        assert all(np.isfinite(float(row[field])) for field in FIELDS)
        for field in ('mse', 'mae', 'residual_variance', 'stopped_absolute_error'):
            assert -1e-12 <= float(row[field]) <= 1+1e-12
        assert float(row['mse']) <= float(row['mae'])+1e-12
        assert abs(float(row['residual_mean'])) <= float(row['mae'])+1e-12
        close(row['mse'], float(row['residual_variance'])+float(row['residual_mean'])**2)
        if int(row['simultaneous_coverage']):
            assert float(row['stopped_absolute_error']) <= .05+1e-12
        groups[(row['case_id'], row['arm'])].append(row)
    assert len(groups) == 234
    target_lookup = {}
    for row in targets:
        key = row['case_id'], row['arm']
        assert key not in target_lookup
        target_lookup[key] = row
        group = groups[key]
        assert {int(r['repeat']) for r in group} == set(range(100))
        for field in FIELDS:
            close(row[field], np.mean([float(r[field]) for r in group]))
    reference = {r['case_id']: r for r in read(ROOT.parent / 'stage9/results_reference/by_target.csv')
                 if r['method'] == 'budget_prediction95'}
    assert len(reference) == 117
    for (case_id, arm), row in target_lookup.items():
        if arm == 'svd':
            for field in ('mean_queries', 'simultaneous_coverage'):
                close(row[field], float(reference[case_id][field]))
    summary_lookup = {}
    languages = sorted({c['language_pair'] for c, _, _ in cases})
    for row in summary:
        key = row['scenario'], row['language_pair'], row['arm']
        assert key not in summary_lookup
        summary_lookup[key] = row
        pairs = languages if row['language_pair'] == 'overall' else [row['language_pair']]
        for field in FIELDS:
            close(row[field], np.mean([np.mean([float(r[field]) for r in targets if
                r['scenario'] == row['scenario'] and r['arm'] == row['arm'] and
                r['language_pair'] == pair]) for pair in pairs]))
    independently_computed = []
    for comparison in comparisons:
        scenario = comparison['scenario']
        paired_blocks = np.zeros(100)
        wins, ties, losses = 0, 0, 0
        for pair in languages:
            ids = [c['case_id'] for c, _, _ in cases if c['scenario'] == scenario and c['language_pair'] == pair]
            for case_id in ids:
                arms = {arm: np.array([float(r['mean_queries']) for r in sorted(groups[(case_id, arm)],
                    key=lambda r: int(r['repeat']))]) for arm in ('svd', 'no_svd')}
                diff = arms['svd']-arms['no_svd']
                paired_blocks += diff/(len(languages)*len(ids))
                delta = float(target_lookup[(case_id, 'svd')]['mean_queries'])-float(target_lookup[(case_id, 'no_svd')]['mean_queries'])
                wins += delta < 0; ties += delta == 0; losses += delta > 0
        svd = summary_lookup[(scenario, 'overall', 'svd')]
        no = summary_lookup[(scenario, 'overall', 'no_svd')]
        percent = 100*(float(svd['mean_queries'])/float(no['mean_queries'])-1)
        mcse = float(np.std(paired_blocks, ddof=1)/np.sqrt(100))
        close(comparison['svd_minus_no_svd_labels'], paired_blocks.mean())
        close(comparison['svd_label_change_percent'], percent)
        close(comparison['paired_repeat_block_mcse'], mcse)
        assert int(comparison['target_wins']) == wins
        independently_computed.append(dict(scenario=scenario, labels_difference=float(paired_blocks.mean()),
            label_percent_change=percent, mcse=mcse, wins=int(wins), ties=int(ties), losses=int(losses)))
    changed_sources = []
    unchanged_sources = 0
    for relative, expected in meta['source_sha256'].items():
        path = ROOT.parent / relative
        if not path.exists() or sha(path) != expected:
            changed_sources.append(relative)
            assert relative.replace('\\', '/').startswith('svd_ablation/'), 'Existing engine changed'
        else:
            unchanged_sources += 1
    manifest_count = 0
    for manifest in sorted(ROOT.parent.glob('stage*/MANIFEST_SHA256.json')):
        for relative, expected in json.loads(manifest.read_text()).items():
            assert sha(manifest.parent / relative) == expected
            manifest_count += 1
    assert sha(DIRECTORY / 'run_metadata.json') == metadata_hash
    audit = dict(status='saved_metrics_checks_passed_with_source_provenance_limit',
        original_metadata_status=meta['status'], original_metadata_sha256=metadata_hash,
        current_protocol_matches_start_hash=sha(ROOT / 'PROTOCOL.md') == meta['protocol_sha256'],
        cases=117, arms=2, repeats_per_case_arm=100, trial_records=23400,
        target_records=234, summary_records=24, reference_target_costs_and_coverage_matched=117,
        existing_manifest_files_unchanged=manifest_count, unchanged_recorded_source_files=unchanged_sources,
        changed_recorded_source_files=changed_sources, comparisons=independently_computed,
        artifact_sha256={name: sha(DIRECTORY / name) for name in
            ('per_trial.csv', 'by_target.csv', 'summary.csv', 'comparison.csv')},
        confirmed_failure='Process exited 1 after all 117 cases and CSV writes: AssertionError: Source changed during run',
        not_reverified=['Full confidence curves and raw prediction residuals were not saved.',
            'Per-case ledger equality passed inside the original runner before CSV writes, but actual run ledger hashes were not saved after failure.',
            'This audit does not certify unchanged source or a successful pruned-engine full run.'])
    (ROOT / 'EXISTING_RUN_AUDIT.json').write_text(json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    lines = ['# Audit of the existing dense-engine run', '',
        'All 117 cases and 23,400 arm/repeat records are present. Saved metric checks passed.',
        'The process failed after writing all four CSVs at `AssertionError: Source changed during run`.',
        'Original run_metadata.json is preserved and still says running; it has not been marked complete.', '',
        '| Aligned-history metric | With SVD | Without SVD | SVD relative change |',
        '| --- | ---: | ---: | ---: |']
    svd = summary_lookup[('aligned', 'overall', 'svd')]
    no = summary_lookup[('aligned', 'overall', 'no_svd')]
    for field in ('mean_queries', 'mse', 'mae', 'residual_variance'):
        a, b = float(svd[field]), float(no[field])
        lines.append(f'| {field} | {a:.6f} | {b:.6f} | {100*(a/b-1):+.3f}% |')
    lines += ['', '| History | SVD minus no-SVD labels | Change | MCSE | Target wins / ties / losses |',
        '| --- | ---: | ---: | ---: | --- |']
    for row in independently_computed:
        lines.append(f"| {row['scenario']} | {row['labels_difference']:+.6f} | {row['label_percent_change']:+.6f}% | {row['mcse']:.6f} | {row['wins']} / {row['ties']} / {row['losses']} |")
    lines += ['', 'Checks: unique and complete repeat IDs; finite bounded metrics; valid label costs;',
        'MSE = residual variance + squared residual mean; coverage/error consistency;',
        'all target and equally weighted language/overall aggregates; paired differences and MCSE;',
        'all 117 SVD reference target costs and coverage values; existing release manifests.', '',
        'Interpretation: SVD has a small aligned-history average benefit in this fixed ridge/trust',
        'pipeline, concentrated in Hebrew/Chinese. German has a tiny average label-cost increase.',
        'Permuted/reversed histories show effectively no label-cost benefit. This is development',
        'evidence on previously inspected fixed pools, not new-data confirmation.', '',
        'Provenance limit: wrapper/source files changed during execution. The metric audit cannot',
        'recover unsaved full curves, per-step predictions or the final run ledger-hash dictionary.',
        'Existing engine/data files are unchanged. Keep these outputs as an audited development run,',
        'not a successfully completed frozen-source or full pruned-engine validation run.', '',
        'Next: preserve these files, freeze the current implementation, rerun to a NEW directory',
        'only if a fully reproducible final release is needed, then use report.py on that directory.', '']
    (ROOT / 'EXISTING_RUN_FINDINGS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
