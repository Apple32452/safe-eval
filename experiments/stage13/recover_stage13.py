"""Recover damaged local archives only if frozen reruns match original hashes.

This is an integrity utility, not a new experiment or parameter adjustment.
The original run metadata is never rewritten. Publish the recovery record.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from run_stage13 import run_case
from stage13_common import build_cases, verify_lock


def main(directory):
    metadata=json.loads((directory/'run_metadata.json').read_text())
    if metadata['frozen_protocol']!=verify_lock():
        raise ValueError('The original frozen source/data must be unchanged')
    cases,_=build_cases()
    lookup={case[0]['case_id']:case for case in cases}
    damaged=[]
    for record in metadata['cases']:
        path=directory/'traces'/(record['case_id']+'.npz')
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual!=record['trace_sha256']:
            damaged.append((record,actual))
    recovered=[]
    start=time.time()
    for record,previous in damaged:
        meta,histories,labels=lookup[record['case_id']]
        with tempfile.TemporaryDirectory(prefix='stage13_recovery_',dir=str(directory)) as temporary:
            (Path(temporary)/'traces').mkdir()
            regenerated=run_case((meta,histories,labels,metadata['repeats'],temporary))
            if regenerated!=record:
                raise ValueError('Regeneration differed from original metadata: '+record['case_id'])
            source=Path(temporary)/'traces'/(record['case_id']+'.npz')
            destination=directory/'traces'/source.name
            os.replace(source,destination)
            if hashlib.sha256(destination.read_bytes()).hexdigest()!=record['trace_sha256']:
                raise ValueError('Recovered archive did not persist')
        recovered.append(dict(case_id=record['case_id'],damaged_sha256=previous,
                              original_and_recovered_sha256=record['trace_sha256']))
        print('Recovered exact original bytes:',record['case_id'],flush=True)
    result=dict(status='passed',recovered=recovered,source_data_rules_and_seeds_unchanged=True,
                original_run_metadata_unchanged=True,elapsed_seconds=time.time()-start)
    (directory/'RECOVERY.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recovered',len(recovered),'damaged archives; every hash matches the original run.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    args=parser.parse_args()
    main(Path(args.input))
