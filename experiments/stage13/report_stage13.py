"""Summaries of audited decisions; no method or parameter selection."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from paired_engine import METHODS, LEVELS


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def macro(values, languages):
    return np.mean([np.mean(values[languages == language], axis=0) for language in sorted(set(languages))], axis=0)


def mcse(values):
    return float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None


def make_report(directory):
    metadata = json.loads((directory / 'run_metadata.json').read_text())
    verification = json.loads((directory / 'VERIFICATION.json').read_text())
    if verification['status'] != 'passed' or hashlib.sha256((directory / 'decisions.npz').read_bytes()).hexdigest() != verification['decisions_sha256']:
        raise ValueError('Audited decision artifact required')
    with np.load(directory / 'decisions.npz', allow_pickle=False) as z:
        stop, direction, checkpoints, naive = (z[key] for key in ('stop', 'direction', 'checkpoints', 'naive'))
        np.testing.assert_array_equal(z['methods'], METHODS)
        np.testing.assert_array_equal(z['levels'], LEVELS)
        np.testing.assert_array_equal(z['case_ids'], [c['case_id'] for c in metadata['cases']])
    cases = metadata['cases']
    n = np.array([case['n'] for case in cases])
    languages = np.array([case['language_pair'] for case in cases])
    total = np.array([case['full_difference_total'] for case in cases])
    truth = np.sign(total)
    gap = abs(total / n)
    strata = np.where(total == 0, 'exact_tie', np.where(gap <= .02, 'gap_0_to_02',
                       np.where(gap <= .05, 'gap_02_to_05', 'gap_above_05')))
    by_pair, summary, budgets, comparisons, naive_rows, family = [], [], [], [], [], []
    for method, name in enumerate(METHODS):
        for level, risk in enumerate(LEVELS):
            cost = stop[:, method, level]
            answer = direction[:, method, level]
            wrong = answer != truth[:, None]
            early = cost < n[:, None]
            for i, case in enumerate(cases):
                by_pair.append(dict(case_id=case['case_id'], language_pair=case['language_pair'],
                    system_a=case['system_a'], system_b=case['system_b'], n=int(n[i]),
                    full_difference_total=int(total[i]), full_difference=float(total[i]/n[i]), stratum=str(strata[i]),
                    method=name, error_setting=risk, repeats=cost.shape[1], mean_paired_queries=float(cost[i].mean()),
                    mean_target_labels=float(2*cost[i].mean()), mean_fraction_full=float((cost[i]/n[i]).mean()),
                    early_decision_rate=float(early[i].mean()), correct_early_rate=float((early[i]&~wrong[i]).mean()),
                    wrong_decisions=int(wrong[i].sum()), wrong_rate=float(wrong[i].mean())))
            for language in list(sorted(set(languages))) + ['overall']:
                for stratum in ['all'] + list(sorted(set(strata))):
                    keep = (np.ones(len(cases), dtype=bool) if language == 'overall' else languages == language)
                    if stratum != 'all':
                        keep &= strata == stratum
                    if not keep.any():
                        continue
                    def average(values):
                        return macro(values[keep], languages[keep]) if language == 'overall' else values[keep].mean(axis=0)
                    fraction = average(cost / n[:, None])
                    summary.append(dict(language_pair=language, stratum=stratum, method=name, error_setting=risk,
                        system_pairs=int(keep.sum()), trajectories=int(keep.sum()*cost.shape[1]),
                        mean_paired_queries=float(average(cost).mean()), mean_target_labels=float(2*average(cost).mean()),
                        mean_fraction_full=float(fraction.mean()), savings_vs_full_percent=float(100*(1-fraction.mean())),
                        conditional_fraction_mcse=mcse(fraction), early_decision_rate=float(average(early).mean()),
                        correct_early_rate=float(average(early&~wrong).mean()), wrong_decisions=int(wrong[keep].sum()),
                        wrong_rate=float(average(wrong).mean())))
                    if stratum == 'all':
                        for j, fraction_budget in enumerate((.25, .5, .75)):
                            decided = cost <= checkpoints[:, j, None]
                            budgets.append(dict(language_pair=language, method=name, error_setting=risk, budget_fraction=fraction_budget,
                                correct_decision_rate=float(average(decided&~wrong).mean()),
                                wrong_decision_rate=float(average(decided&wrong).mean()),
                                unresolved_rate=float(average(~decided).mean())))
            if len(cases) == 237:
                any_wrong = wrong.any(axis=0)
                family.append(dict(method=name,error_setting=risk,repeats=cost.shape[1],
                                   repeats_with_any_wrong=int(any_wrong.sum()),any_wrong_rate=float(any_wrong.mean())))
    for level, risk in enumerate(LEVELS):
        for method, control in ((3, 2), (3, 1), (2, 1), (4, 2), (5, 2)):
            difference = stop[:, method, level].astype(int) - stop[:, control, level]
            for language in list(sorted(set(languages))) + ['overall']:
                keep = np.ones(len(cases), dtype=bool) if language == 'overall' else languages == language
                aggregate = macro(difference[keep], languages[keep]) if language == 'overall' else difference[keep].mean(axis=0)
                mean_m = macro(stop[keep,method,level],languages[keep]).mean() if language=='overall' else stop[keep,method,level].mean()
                mean_c = macro(stop[keep,control,level],languages[keep]).mean() if language=='overall' else stop[keep,control,level].mean()
                pair_difference = difference[keep].mean(axis=1)
                comparisons.append(dict(language_pair=language,error_setting=risk,method=METHODS[method],control=METHODS[control],
                    method_mean=float(mean_m),control_mean=float(mean_c),paired_mean_difference=float(aggregate.mean()),
                    percent_change=float(100*(mean_m/mean_c-1)),conditional_mcse=mcse(aggregate),
                    pair_mean_wins=int((pair_difference<0).sum()),pair_mean_ties=int((pair_difference==0).sum()),
                    pair_mean_losses=int((pair_difference>0).sum()),largest_extra_queries=int(difference[keep].max())))
    for language in list(sorted(set(languages))) + ['overall']:
        keep = np.ones(len(cases), dtype=bool) if language=='overall' else languages==language
        for j, budget in enumerate((.25,.5,.75)):
            guesses=naive[:,j]
            def average(values):
                return float((macro(values[keep],languages[keep]) if language=='overall' else values[keep].mean(axis=0)).mean())
            naive_rows.append(dict(language_pair=language,budget_fraction=budget,
                correct_direction_rate=average((guesses==truth[:,None])&(guesses!=0)),
                wrong_direction_rate=average((guesses!=truth[:,None])&(guesses!=0)),
                sample_tie_rate=average(guesses==0),note='Uncertified diagnostic; sample tie is not an equivalence conclusion'))
    for filename, rows in [('by_pair.csv',by_pair),('summary.csv',summary),('budgets.csv',budgets),
                           ('comparison.csv',comparisons),('naive_budgets.csv',naive_rows),('family_errors.csv',family)]:
        if rows:
            write_csv(directory/filename,rows)
    report = dict(status='passed',pairs=len(cases),repeats=metadata['repeats'],
                  pair_rows=len(by_pair),summary_rows=len(summary),budget_rows=len(budgets),
                  weighting='equal languages, then equal pairs, then equal query orders; repeat-block MCSE only',
                  source_decisions_sha256=verification['decisions_sha256'],
                  tables_sha256={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in
                    ('by_pair.csv','summary.csv','budgets.csv','comparison.csv','naive_budgets.csv','family_errors.csv') if (directory/name).exists()})
    (directory/'REPORT_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    overall = [r for r in summary if r['language_pair']=='overall' and r['stratum']=='all']
    primary = [r for r in comparisons if r['language_pair']=='overall']
    print(json.dumps(dict(overall=overall,comparisons=primary),indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    args=parser.parse_args()
    make_report(Path(args.input))
