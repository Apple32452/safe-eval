"""Audit Stage 17 result accounting and evaluate its frozen gate."""
from __future__ import annotations

import argparse,csv,hashlib,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage14'))
from shared_pilot import FRACTIONS
from run_stage17 import METHODS


def summarize(directory):
    directory=Path(directory); payload=(directory/'replicates.csv').read_bytes()
    rows=list(csv.DictReader(payload.decode().splitlines())); metadata=json.loads((directory/'metadata.json').read_text())
    indexed={}
    for row in rows:
        key=(row['language'],int(row['repeat']),float(row['fraction']),row['method'])
        if key in indexed: raise ValueError('Duplicate result')
        record={k:int(row[k]) for k in ('pairs','systems','items','budget','labels','correct','wrong','unresolved','reached_prefix','resolved_pairs')}
        if record['correct']+record['wrong']+record['unresolved']!=record['pairs'] or record['resolved_pairs']!=record['correct']+record['wrong']:
            raise ValueError('Pair accounting failed')
        if record['budget']!=int(float(row['fraction'])*record['systems']*record['items']) or not 0<=record['labels']<=record['budget']:
            raise ValueError('Budget accounting failed')
        indexed[key]=record
    expected={(language,repeat,fraction,method) for language in metadata['languages']
              for repeat in range(metadata['repeats']) for fraction in FRACTIONS for method in METHODS}
    if set(indexed)!=expected: raise ValueError('Incomplete result grid')
    for language in metadata['languages']:
        for repeat in range(metadata['repeats']):
            for method in METHODS:
                sequence=[indexed[language,repeat,fraction,method] for fraction in FRACTIONS]
                for field in ('labels','correct','wrong','resolved_pairs','reached_prefix'):
                    values=[record[field] for record in sequence]
                    if values!=sorted(values): raise ValueError('Nonmonotone '+field)

    def stats(values):
        mean=sum(values)/len(values)
        mcse=(sum((x-mean)**2 for x in values)/(len(values)-1)/len(values))**.5 if len(values)>1 else None
        return dict(mean=mean,conditional_repeat_mcse=round(mcse,12) if mcse is not None else None,
                    wins=sum(x>0 for x in values),ties=sum(x==0 for x in values),
                    losses=sum(x<0 for x in values),values=values)

    result=dict(status='passed',rows=len(rows),languages=metadata['languages'],repeats=metadata['repeats'],
                methods=list(METHODS),replicates_sha256=hashlib.sha256(payload).hexdigest(),aggregate={},by_language={})
    for fraction in FRACTIONS:
        cell=result['aggregate'][str(fraction)]={}
        for method in METHODS:
            totals=[sum(indexed[language,repeat,fraction,method]['correct'] for language in metadata['languages'])
                    for repeat in range(metadata['repeats'])]
            cell[method]=dict(mean_correct_total=stats(totals)['mean'],
                              conditional_repeat_mcse=stats(totals)['conditional_repeat_mcse'],
                              wrong_count=sum(indexed[language,repeat,fraction,method]['wrong']
                                              for language in metadata['languages'] for repeat in range(metadata['repeats'])))
        for control in ('evidence_first','uniform_labels'):
            differences=[sum(indexed[language,repeat,fraction,'frontier_evidence']['correct']-
                             indexed[language,repeat,fraction,control]['correct']
                             for language in metadata['languages']) for repeat in range(metadata['repeats'])]
            cell['frontier_minus_'+control]=stats(differences)
    for language in metadata['languages']:
        result['by_language'][language]={}
        for fraction in FRACTIONS:
            differences=[indexed[language,repeat,fraction,'frontier_evidence']['correct']-
                         indexed[language,repeat,fraction,'evidence_first']['correct']
                         for repeat in range(metadata['repeats'])]
            result['by_language'][language][str(fraction)]=stats(differences)
    primary=result['aggregate']['0.75']; positive_languages=sum(
        result['by_language'][language]['0.75']['mean']>0 for language in metadata['languages'])
    frontier_wrong=primary['frontier_evidence']['wrong_count']
    controls={control:primary['frontier_minus_'+control] for control in ('evidence_first','uniform_labels')}
    control_wrong={control:primary[control]['wrong_count'] for control in ('evidence_first','uniform_labels')}
    gate=(all(value['mean']>0 for value in controls.values()) and
          positive_languages>len(metadata['languages'])/2 and
          all(frontier_wrong<=value for value in control_wrong.values()))
    result['development_gate']=dict(passed=gate,comparisons=controls,positive_languages=positive_languages,
                                    included_languages=len(metadata['languages']),frontier_wrong=frontier_wrong,
                                    control_wrong=control_wrong)
    (directory/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['development_gate'],indent=2)); return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--input',required=True)
    arguments=parser.parse_args(); summarize(arguments.input)
