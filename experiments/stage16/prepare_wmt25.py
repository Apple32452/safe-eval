"""Frozen WMT25 JSONL parser for strict binary consensus outcomes."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np

UPSTREAM_COMMIT='2fc0874d85278d8c7e0807951e54d8422e7957e4'
LFS_SHA256='a36ebce10c9ea26f71449933721de3a87e27f6a5b09d96b5daa026eaf1d197ab'
LFS_BYTES=128674273
SOURCE_URL=('https://github.com/wmt-conference/wmt25-general-mt/raw/'
            +UPSTREAM_COMMIT+'/data/wmt25-genmt-humeval.jsonl')
KNOWN_SEVERITIES={'minor','major','undecided'}


def normalized_name(name):
    return re.sub('[^a-z0-9]+','',name.casefold())


def is_reference(name):
    value=normalized_name(name)
    return value.startswith('ref') or value.startswith('human')


def strict_outcome(annotations):
    if not isinstance(annotations,list) or not annotations:
        raise ValueError('A nonempty annotation list is required')
    perfect=True
    for annotation in annotations:
        if not isinstance(annotation,dict):
            raise ValueError('Every annotation must be a dictionary')
        score=annotation.get('score')
        errors=annotation.get('errors')
        if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=100:
            raise ValueError('Every retained score must be finite in [0,100]')
        if not isinstance(errors,list):
            raise ValueError('Every retained annotation needs an errors list')
        for error in errors:
            if not isinstance(error,dict) or str(error.get('severity','')).strip().casefold() not in KNOWN_SEVERITIES:
                raise ValueError('Unknown or malformed retained error')
        perfect &= (score == 100 and len(errors) == 0)
    return int(perfect)


def matrix_hash(scores,names,items):
    h=hashlib.sha256(np.asarray(scores,dtype=np.int8).tobytes())
    for values in (names.tolist(),items.tolist()):
        h.update(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode())
    return h.hexdigest()


def parse_jsonl(path):
    path=Path(path)
    if path.stat().st_size != LFS_BYTES:
        raise ValueError('Unexpected upstream byte count')
    digest=hashlib.sha256()
    records=defaultdict(dict)
    lines=0
    with path.open('rb') as stream:
        for raw in stream:
            digest.update(raw)
            if not raw.strip():
                continue
            lines+=1
            try:
                row=json.loads(raw)
            except (UnicodeDecodeError,json.JSONDecodeError) as exc:
                raise ValueError(f'Malformed JSONL line {lines}') from exc
            if not isinstance(row,dict) or not isinstance(row.get('doc_id'),str) or '_#_' not in row['doc_id']:
                raise ValueError(f'Invalid doc_id at line {lines}')
            scores=row.get('scores')
            if not isinstance(scores,dict) or not scores or not all(isinstance(k,str) for k in scores):
                raise ValueError(f'Invalid scores mapping at line {lines}')
            language=row['doc_id'].split('_#_',1)[0]
            if row['doc_id'] in records[language]:
                raise ValueError('Duplicate language/doc_id')
            records[language][row['doc_id']]={k:v for k,v in scores.items()
                                             if not is_reference(k)}
    if digest.hexdigest()!=LFS_SHA256:
        raise ValueError('Upstream SHA256 mismatch')
    return records,lines


def build_matrices(records):
    included={}
    report=[]
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
        systems=sorted(s for s,count in coverage.items() if count==maximum)
        common=sorted(item for item,scores in items_to_scores.items()
                      if all(isinstance(scores.get(system),list) and scores[system]
                             for system in systems))
        if len(systems)<3 or len(common)<30:
            reason='fewer_than_three_max_coverage_systems' if len(systems)<3 else 'fewer_than_30_common_items'
            report.append(dict(language=language,included=False,reason=reason,
                               maximum_coverage=maximum,systems=len(systems),common_items=len(common)))
            continue
        matrix=np.array([[strict_outcome(items_to_scores[item][system])
                          for item in common] for system in systems],dtype=np.int8)
        names=np.array(systems,dtype=str)
        item_array=np.array(common,dtype=str)
        included[language]=(matrix,names,item_array)
        report.append(dict(language=language,included=True,maximum_coverage=maximum,
                           systems=len(systems),common_items=len(common),
                           pairs=len(systems)*(len(systems)-1)//2,
                           matrix_sha256=matrix_hash(matrix,names,item_array)))
    return included,report


def prepare(source,output):
    records,lines=parse_jsonl(source)
    matrices,report=build_matrices(records)
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    for language,(scores,names,items) in matrices.items():
        safe=language.replace('/','_')
        np.savez_compressed(output/f'wmt25_{safe}_strict_error_free.npz',
                            scores=scores,systems=names,items=items)
    provenance=dict(source_url=SOURCE_URL,upstream_commit=UPSTREAM_COMMIT,
                    source_sha256=LFS_SHA256,source_bytes=LFS_BYTES,
                    jsonl_lines=lines,outcome=('One iff every retained annotation has score 100 and an empty error list'),
                    scope='Strict binary consensus proxy, not official continuous WMT25 human score',
                    reports=report)
    (output/'DATA_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return matrices,provenance


def load_prepared(directory):
    directory=Path(directory)
    provenance=json.loads((directory/'DATA_PROVENANCE.json').read_text())
    expected=(UPSTREAM_COMMIT,LFS_SHA256,LFS_BYTES)
    observed=(provenance.get('upstream_commit'),provenance.get('source_sha256'),
              provenance.get('source_bytes'))
    if observed!=expected:
        raise ValueError('Prepared data does not match the frozen WMT25 source')
    result={}
    for row in provenance['reports']:
        if not row['included']:
            continue
        language=row['language']
        with np.load(directory/f'wmt25_{language.replace("/","_")}_strict_error_free.npz',allow_pickle=False) as data:
            scores,names,items=data['scores'],data['systems'],data['items']
        if matrix_hash(scores,names,items)!=row['matrix_sha256']:
            raise ValueError('Prepared matrix hash mismatch: '+language)
        result[language]=(scores,names,items)
    if not result:
        raise ValueError('No language met the frozen inclusion rule')
    return result,provenance


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    prepare(args.source,args.output)
