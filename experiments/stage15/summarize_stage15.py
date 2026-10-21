"""Audit Stage 15 result accounting and calculate matched comparisons."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from frontier_experiment import FRACTIONS, METHODS


def summarize(directory):
    directory = Path(directory)
    payload = (directory/'replicates.csv').read_bytes()
    rows = list(csv.DictReader(payload.decode().splitlines()))
    metadata = json.loads((directory/'metadata.json').read_text())
    indexed = {}
    fields = ('pairs','systems','items','budget','labels','correct','wrong',
              'unresolved','reached_prefix','resolved_pairs')
    for row in rows:
        key = (row['language'], int(row['repeat']), float(row['fraction']),
               row['method'])
        if key in indexed:
            raise ValueError('Duplicate result: '+str(key))
        x = {field:int(row[field]) for field in fields}
        if x['correct']+x['wrong']+x['unresolved'] != x['pairs']:
            raise ValueError('Pair accounting failed')
        expected_budget = int(float(row['fraction'])*x['systems']*x['items'])
        if x['budget'] != expected_budget or x['labels'] != x['budget']:
            raise ValueError('Unique-label budget accounting failed')
        if x['reached_prefix'] < x['resolved_pairs']:
            raise ValueError('Impossible prefix accounting')
        indexed[key] = x
    expected = {(l,r,f,m) for l in metadata['languages']
                for r in range(metadata['repeats'])
                for f in FRACTIONS for m in METHODS}
    if set(indexed) != expected:
        raise ValueError('Incomplete or unexpected result grid')
    for l in metadata['languages']:
        for r in range(metadata['repeats']):
            for m in METHODS:
                path = [indexed[l,r,f,m] for f in FRACTIONS]
                if any(y['correct'] < x['correct'] or y['wrong'] < x['wrong']
                       or y['reached_prefix'] < x['reached_prefix']
                       for x,y in zip(path,path[1:])):
                    raise ValueError('A decision or pair prefix was discarded')

    def stats(values):
        mean = sum(values)/len(values)
        mcse = ((sum((x-mean)**2 for x in values)/(len(values)-1)/len(values))**.5
                if len(values)>1 else None)
        return dict(mean=mean,
                    conditional_repeat_mcse=(round(mcse,12)
                                             if mcse is not None else None),
                    values=values)

    result = dict(status='passed', rows=len(rows), languages=metadata['languages'],
                  repeats=metadata['repeats'], methods=list(METHODS),
                  replicates_sha256=hashlib.sha256(payload).hexdigest(),
                  aggregate={})
    for fraction in FRACTIONS:
        cell = result['aggregate'][str(fraction)] = {}
        for method in METHODS:
            totals = [sum(indexed[l,r,fraction,method]['correct']
                          for l in metadata['languages'])
                      for r in range(metadata['repeats'])]
            wrong = sum(indexed[l,r,fraction,method]['wrong']
                        for l in metadata['languages']
                        for r in range(metadata['repeats']))
            cell[method] = dict(mean_correct_total=stats(totals)['mean'],
                                conditional_repeat_mcse=stats(totals)['conditional_repeat_mcse'],
                                wrong_count=wrong)
        for method in ('frontier_count','frontier_evidence'):
            differences = [sum(indexed[l,r,fraction,method]['correct']-
                               indexed[l,r,fraction,'evidence_first']['correct']
                               for l in metadata['languages'])
                           for r in range(metadata['repeats'])]
            cell[method+'_minus_evidence_first'] = stats(differences)
    (directory/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    primary = result['aggregate']['0.5']['frontier_evidence_minus_evidence_first']
    print(json.dumps({'primary_50pct':primary,
                      'wrong_counts_50pct':{m:result['aggregate']['0.5'][m]['wrong_count']
                                            for m in METHODS}},indent=2))
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    args=parser.parse_args()
    summarize(args.input)
