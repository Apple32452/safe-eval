"""Audit accounting and evaluate the frozen Stage 16 external gate."""
from __future__ import annotations

import argparse,csv,hashlib,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage14'))
from run_stage16 import METHODS
from shared_pilot import FRACTIONS


def summarize(directory):
    directory=Path(directory); payload=(directory/'replicates.csv').read_bytes()
    rows=list(csv.DictReader(payload.decode().splitlines())); meta=json.loads((directory/'metadata.json').read_text())
    indexed={}
    for row in rows:
        key=(row['language'],int(row['repeat']),float(row['fraction']),row['method'])
        if key in indexed: raise ValueError('Duplicate result')
        x={k:int(row[k]) for k in ('pairs','systems','items','budget','labels','correct','wrong','unresolved','reached_prefix','resolved_pairs')}
        if x['correct']+x['wrong']+x['unresolved']!=x['pairs']: raise ValueError('Pair accounting failed')
        if x['budget']!=int(float(row['fraction'])*x['systems']*x['items']) or not 0<=x['labels']<=x['budget']:
            raise ValueError('Budget accounting failed')
        indexed[key]=x
    expected={(l,r,f,m) for l in meta['languages'] for r in range(meta['repeats']) for f in FRACTIONS for m in METHODS}
    if set(indexed)!=expected: raise ValueError('Incomplete result grid')
    for language in meta['languages']:
        for repeat in range(meta['repeats']):
            for method in METHODS:
                sequence=[indexed[language,repeat,f,method] for f in FRACTIONS]
                for field in ('labels','correct','wrong','resolved_pairs','reached_prefix'):
                    values=[row[field] for row in sequence]
                    if values!=sorted(values):
                        raise ValueError(f'Nonmonotone {field}: {language}/{repeat}/{method}')

    def stats(values):
        mean=sum(values)/len(values)
        mcse=((sum((x-mean)**2 for x in values)/(len(values)-1)/len(values))**.5 if len(values)>1 else None)
        return dict(mean=mean,conditional_repeat_mcse=round(mcse,12) if mcse is not None else None,
                    wins=sum(x>0 for x in values),ties=sum(x==0 for x in values),losses=sum(x<0 for x in values),values=values)

    result=dict(status='passed',rows=len(rows),languages=meta['languages'],repeats=meta['repeats'],methods=list(METHODS),
                replicates_sha256=hashlib.sha256(payload).hexdigest(),aggregate={},by_language={})
    for f in FRACTIONS:
        cell=result['aggregate'][str(f)]={}
        for m in METHODS:
            totals=[sum(indexed[l,r,f,m]['correct'] for l in meta['languages']) for r in range(meta['repeats'])]
            cell[m]=dict(mean_correct_total=stats(totals)['mean'],conditional_repeat_mcse=stats(totals)['conditional_repeat_mcse'],
                         wrong_count=sum(indexed[l,r,f,m]['wrong'] for l in meta['languages'] for r in range(meta['repeats'])))
        diffs=[sum(indexed[l,r,f,'frontier_evidence']['correct']-indexed[l,r,f,'evidence_first']['correct'] for l in meta['languages']) for r in range(meta['repeats'])]
        cell['frontier_minus_evidence']=stats(diffs)
    for l in meta['languages']:
        result['by_language'][l]={}
        for f in FRACTIONS:
            diffs=[indexed[l,r,f,'frontier_evidence']['correct']-indexed[l,r,f,'evidence_first']['correct'] for r in range(meta['repeats'])]
            result['by_language'][l][str(f)]=stats(diffs)
    primary=result['aggregate']['0.75']['frontier_minus_evidence']
    positive_languages=sum(result['by_language'][l]['0.75']['mean']>0 for l in meta['languages'])
    frontier_wrong=result['aggregate']['0.75']['frontier_evidence']['wrong_count']
    evidence_wrong=result['aggregate']['0.75']['evidence_first']['wrong_count']
    gate=(primary['mean']>0 and positive_languages>len(meta['languages'])/2 and frontier_wrong<=evidence_wrong)
    result['external_gate']=dict(passed=gate,primary=primary,positive_languages=positive_languages,
                                 included_languages=len(meta['languages']),frontier_wrong=frontier_wrong,evidence_wrong=evidence_wrong)
    (directory/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['external_gate'],indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--input',required=True); args=parser.parse_args(); summarize(args.input)
