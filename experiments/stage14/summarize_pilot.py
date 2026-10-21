"""Validate and summarize the saved exploratory pilot, without rerunning it."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from shared_pilot import FRACTIONS, METHODS


def summarize(directory):
    directory = Path(directory)
    raw = (directory / 'replicates.csv').read_bytes()
    meta = json.loads((directory / 'metadata.json').read_text())
    rows = list(csv.DictReader(raw.decode().splitlines()))
    indexed = {}
    for row in rows:
        key = (row['language'], int(row['repeat']), float(row['fraction']), row['method'])
        if key in indexed:
            raise ValueError(f'Duplicate result {key}')
        value = {k: int(row[k]) for k in ('pairs', 'systems', 'items', 'budget',
                 'labels', 'correct', 'wrong', 'unresolved', 'reached_prefix',
                 'resolved_pairs')}
        if value['correct'] + value['wrong'] + value['unresolved'] != value['pairs']:
            raise ValueError('Incorrect pair accounting')
        if value['labels'] != value['budget'] or value['budget'] != int(
            float(row['fraction']) * value['systems'] * value['items']):
            raise ValueError('Incorrect unique-label budget')
        if value['reached_prefix'] < value['resolved_pairs'] or value['labels'] > (
                value['systems'] * value['items']):
            raise ValueError('Impossible query accounting')
        indexed[key] = value
    expected = {(l, r, f, m) for l in meta['languages']
                for r in range(meta['repeats']) for f in FRACTIONS for m in METHODS}
    if set(indexed) != expected:
        raise ValueError('Incomplete experiment or unexpected methods')
    for l in meta['languages']:
        for r in range(meta['repeats']):
            for m in METHODS:
                track = [indexed[l, r, f, m] for f in FRACTIONS]
                if any(y['correct'] < x['correct'] or y['wrong'] < x['wrong'] or
                       y['reached_prefix'] < x['reached_prefix'] for x, y in
                       zip(track, track[1:])):
                    raise ValueError('Decisions or prefixes were discarded')
    result = dict(status='passed', rows=len(rows), languages=meta['languages'],
                  repeats=meta['repeats'], methods=list(METHODS),
                  replicates_sha256=hashlib.sha256(raw).hexdigest(),
                  by_language={}, aggregate={})
    for l in meta['languages']:
        result['by_language'][l] = {}
        for f in FRACTIONS:
            result['by_language'][l][str(f)] = {
                m: dict(mean_correct=sum(indexed[l, r, f, m]['correct']
                                         for r in range(meta['repeats'])) / meta['repeats'],
                        wrong_count=sum(indexed[l, r, f, m]['wrong']
                                        for r in range(meta['repeats'])))
                for m in METHODS}
    for f in FRACTIONS:
        result['aggregate'][str(f)] = {}
        for m in METHODS:
            sums = [sum(indexed[l, r, f, m]['correct'] for l in meta['languages'])
                    for r in range(meta['repeats'])]
            mean = sum(sums) / len(sums)
            mcse = (sum((x-mean)**2 for x in sums) /
                    (len(sums)-1) / len(sums))**.5 if len(sums) > 1 else None
            result['aggregate'][str(f)][m] = dict(
                mean_correct_total=mean,
                conditional_repeat_mcse=round(mcse, 12) if mcse is not None else None,
                wrong_count=sum(indexed[l, r, f, m]['wrong']
                                for l in meta['languages']
                                for r in range(meta['repeats'])))
        for control in ('focus_first', 'focus_random'):
            diffs = [sum(indexed[l, r, f, 'evidence_first']['correct'] -
                         indexed[l, r, f, control]['correct']
                         for l in meta['languages']) for r in range(meta['repeats'])]
            mean = sum(diffs) / len(diffs)
            mcse = (sum((x-mean)**2 for x in diffs) /
                    (len(diffs)-1) / len(diffs))**.5 if len(diffs) > 1 else None
            result['aggregate'][str(f)]['evidence_minus_' + control] = dict(
                mean_correct_pair_gain=mean,
                conditional_repeat_mcse=round(mcse, 12) if mcse is not None else None,
                repeat_differences=diffs)
    (directory / 'SUMMARY.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['aggregate'], indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    args = parser.parse_args()
    summarize(args.input)
