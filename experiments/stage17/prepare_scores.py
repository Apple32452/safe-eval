"""Prepare WMT25 mean recorded human scores under the Stage 16 alignment."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage16'))
from prepare_wmt25 import (LFS_BYTES,LFS_SHA256,SOURCE_URL,UPSTREAM_COMMIT,
                           parse_jsonl)


def mean_score(annotations):
    if not isinstance(annotations,list) or not annotations:
        raise ValueError('A nonempty annotation list is required')
    values=[]
    for annotation in annotations:
        if not isinstance(annotation,dict):
            raise ValueError('Every annotation must be a dictionary')
        value=annotation.get('score')
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=100:
            raise ValueError('Every score must be finite in [0,100]')
        values.append(float(value)/100.0)
    return float(sum(values)/len(values))


def matrix_hash(scores,names,items):
    digest=hashlib.sha256(np.asarray(scores,dtype='<f8').tobytes())
    for values in (names.tolist(),items.tolist()):
        digest.update(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode())
    return digest.hexdigest()


def build_matrices(records):
    included={}; report=[]
    for language,items_to_scores in sorted(records.items()):
        coverage=Counter()
        for scores in items_to_scores.values():
            for system,annotations in scores.items():
                if isinstance(annotations,list) and annotations:
                    coverage[system]+=1
        if not coverage:
            report.append(dict(language=language,included=False,reason='no_nonreference_annotations'))
            continue
        maximum=max(coverage.values())
        systems=sorted(system for system,count in coverage.items() if count==maximum)
        common=sorted(item for item,scores in items_to_scores.items()
                      if all(isinstance(scores.get(system),list) and scores[system]
                             for system in systems))
        if len(systems)<3 or len(common)<30:
            reason=('fewer_than_three_max_coverage_systems' if len(systems)<3
                    else 'fewer_than_30_common_items')
            report.append(dict(language=language,included=False,reason=reason,
                               maximum_coverage=maximum,systems=len(systems),
                               common_items=len(common)))
            continue
        matrix=np.array([[mean_score(items_to_scores[item][system])
                          for item in common] for system in systems],dtype=float)
        names=np.array(systems,dtype=str); items=np.array(common,dtype=str)
        included[language]=(matrix,names,items)
        report.append(dict(language=language,included=True,
                           maximum_coverage=maximum,systems=len(systems),
                           common_items=len(common),pairs=len(systems)*(len(systems)-1)//2,
                           matrix_sha256=matrix_hash(matrix,names,items)))
    return included,report


def prepare(source,output):
    records,lines=parse_jsonl(source)
    matrices,report=build_matrices(records)
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    for language,(scores,names,items) in matrices.items():
        np.savez_compressed(output/f'wmt25_{language.replace("/","_")}_mean_score.npz',
                            scores=scores,systems=names,items=items)
    provenance=dict(source_url=SOURCE_URL,upstream_commit=UPSTREAM_COMMIT,
                    source_sha256=LFS_SHA256,source_bytes=LFS_BYTES,
                    jsonl_lines=lines,
                    outcome='Arithmetic mean of retained recorded 0--100 scores, divided by 100',
                    scope='Recorded WMT25 human score on the fixed common pool',reports=report)
    (output/'DATA_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return matrices,provenance


def load_prepared(directory):
    directory=Path(directory)
    provenance=json.loads((directory/'DATA_PROVENANCE.json').read_text())
    if (provenance.get('upstream_commit'),provenance.get('source_sha256'),provenance.get('source_bytes'))!=(UPSTREAM_COMMIT,LFS_SHA256,LFS_BYTES):
        raise ValueError('Prepared data differs from the frozen WMT25 source')
    result={}
    for row in provenance['reports']:
        if not row['included']: continue
        language=row['language']
        with np.load(directory/f'wmt25_{language.replace("/","_")}_mean_score.npz',allow_pickle=False) as data:
            scores,names,items=data['scores'],data['systems'],data['items']
        if matrix_hash(scores,names,items)!=row['matrix_sha256']:
            raise ValueError('Prepared matrix hash mismatch: '+language)
        result[language]=(scores,names,items)
    if not result: raise ValueError('No language met the frozen inclusion rule')
    return result,provenance


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True); parser.add_argument('--output',required=True)
    arguments=parser.parse_args(); prepare(arguments.source,arguments.output)
