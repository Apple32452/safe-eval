"""Prespecified path-overhead reporting after the frozen full-curve audit.

This read-only reporting addition does not alter inference or the frozen audit.
It records worst paths and within-language paired fractions from audited rows.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from stage8_common import PAIRS, SCENARIOS, read_csv, write_csv


def report(directory):
    directory = Path(directory)
    audit = json.loads((directory / 'VERIFICATION.json').read_text())
    if not audit['all_checks_passed']:
        raise ValueError('Run the frozen analyzer successfully first')
    rows = read_csv(directory / 'per_trial.csv')
    grouped = defaultdict(dict)
    for row in rows:
        key = row['case_id'], int(row['repeat'])
        if row['method'] in grouped[key]:
            raise ValueError('Repeated path identifier')
        grouped[key][row['method']] = row
    comparisons = read_csv(directory / 'comparison.csv')
    lookup = {(r['scenario'], r['language_pair'], r['family']): r for r in comparisons}
    records, worst = [], []
    for scenario in SCENARIOS:
        for predicted, control in PAIRS:
            family = 'reserve75' if predicted == 'reserve_mix75' else 'standalone'
            language_records = []
            for pair in ('en-de', 'he-en', 'zh-en'):
                selected = [g for g in grouped.values() if g[predicted]['scenario'] == scenario and g[predicted]['language_pair'] == pair]
                raw, zero, pred = [np.array([int(g[m]['stop_queries']) for g in selected]) for m in ('published_ppr95', control, predicted)]
                expected = lookup[(scenario, pair, family)]
                for actual, field in zip((raw.mean(), zero.mean(), pred.mean()), ('raw95_mean_queries', 'zero_mean_queries', 'prediction_mean_queries')):
                    if not np.isclose(actual, float(expected[field]), rtol=1e-12, atol=1e-12):
                        raise ValueError('Overhead report differs from the audited comparison')
                by_target = defaultdict(list)
                for g, difference in zip(selected, pred - zero):
                    by_target[g[predicted]['target_system']].append(int(difference))
                record = dict(scenario=scenario, language_pair=pair, family=family,
                              target_means_improved=sum(np.mean(v) < 0 for v in by_target.values()),
                              targets=len(by_target), paired_paths=len(pred),
                              fraction_paths_fewer_than_zero=float((pred < zero).mean()),
                              fraction_paths_more_than_zero=float((pred > zero).mean()),
                              max_extra_vs_zero=int((pred - zero).max()),
                              max_extra_vs_raw95=int((pred - raw).max()))
                records.append(record)
                language_records.append(record)
                for comparator, value, differences in (('matched_zero', zero, pred - zero), ('raw95', raw, pred - raw)):
                    j = int(differences.argmax())
                    row = selected[j][predicted]
                    worst.append(dict(scenario=scenario, language_pair=pair, family=family,
                                      comparator=comparator, target_system=row['target_system'], repeat=int(row['repeat']),
                                      prediction_queries=int(pred[j]), comparator_queries=int(value[j]),
                                      extra_queries=int(differences[j]),
                                      prediction_full_path_coverage=int(row['simultaneous_coverage']),
                                      comparator_full_path_coverage=int(selected[j][control if comparator == 'matched_zero' else 'published_ppr95']['simultaneous_coverage'])))
            records.append(dict(scenario=scenario, language_pair='equal_language_overall', family=family,
                                target_means_improved=sum(r['target_means_improved'] for r in language_records),
                                targets=sum(r['targets'] for r in language_records),
                                paired_paths=sum(r['paired_paths'] for r in language_records),
                                fraction_paths_fewer_than_zero=float(np.mean([r['fraction_paths_fewer_than_zero'] for r in language_records])),
                                fraction_paths_more_than_zero=float(np.mean([r['fraction_paths_more_than_zero'] for r in language_records])),
                                max_extra_vs_zero=max(r['max_extra_vs_zero'] for r in language_records),
                                max_extra_vs_raw95=max(r['max_extra_vs_raw95'] for r in language_records)))
    write_csv(directory / 'path_overheads.csv', records)
    write_csv(directory / 'worst_paths.csv', worst)
    print('Wrote paired path overheads and worst-path records from audited decisions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='results/stage8_local')
    report(parser.parse_args().input)
