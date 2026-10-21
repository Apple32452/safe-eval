"""Batch the unchanged frozen auditor; inference and checks remain unchanged.

Added for runtime only. Each shard executes audit_stage13.py on original records
and original traces. Merge requires exact, disjoint coverage in original order.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from paired_engine import METHODS, LEVELS
from stage13_common import verify_lock


def audit_shard(directory):
    # Cache exact Python-integer combinations. This changes runtime only; the
    # unchanged reference optimizer still checks every saved raw evidence value.
    code = (
        "import sys,math,functools,types; "
        "sys.path.insert(0,sys.argv[1]); import paired_reference; "
        "paired_reference.math=types.SimpleNamespace(comb=functools.lru_cache(maxsize=400000)(math.comb)); "
        "import audit_stage13; sys.argv=['audit_stage13.py','--input',sys.argv[2]]; audit_stage13.main()"
    )
    with (directory/'audit.log').open('w') as log:
        result=subprocess.run([sys.executable,'-c',code,str(Path(__file__).parent),str(directory)],
                              stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Frozen audit failed: '+str(directory/'audit.log'))
    return directory


def atomic_npz(path,payload):
    temporary=path.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        np.savez_compressed(stream,**payload)
    os.replace(temporary,path)


def main(directory,workers,batch_name='audit_batches'):
    lock=verify_lock()
    metadata=json.loads((directory/'run_metadata.json').read_text())
    if metadata['frozen_protocol']!=lock:
        raise ValueError('Original source/data lock required')
    if not batch_name or Path(batch_name).name!=batch_name:
        raise ValueError('One batch folder name required')
    destination=directory/batch_name
    if destination.exists():
        raise ValueError('Batch directory exists; preserve it and use the serial audit or a new copy')
    destination.mkdir()
    workers=min(workers,len(metadata['cases']))
    shards=[[] for _ in range(workers)]
    loads=[0]*workers
    for record in sorted(metadata['cases'],key=lambda r:-r['n']):
        index=min(range(workers),key=lambda j:loads[j])
        shards[index].append(record)
        loads[index]+=record['n']
    folders=[]
    for index,records in enumerate(shards):
        folder=destination/str(index)
        folder.mkdir()
        (folder/'traces').symlink_to((directory/'traces').resolve(),target_is_directory=True)
        part=dict(metadata,cases=records,complete_reference=False)
        (folder/'run_metadata.json').write_text(json.dumps(part,indent=2)+'\n')
        folders.append(folder)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for folder in pool.map(audit_shard,folders):
            print('Frozen audit passed:',folder.name,flush=True)
    verified={}
    counts={key:0 for key in ('pairs','saved_decisions','raw_states','integer_expert_updates',
                              'fraction_factor_checks','paired_query_steps')}
    records=[]
    checks=None
    for folder in folders:
        report=json.loads((folder/'VERIFICATION.json').read_text())
        if report['status']!='passed':
            raise ValueError('Unverified shard')
        if checks is None:checks=report['checks']
        if checks!=report['checks']:raise ValueError('Different audit checks')
        for key in counts:counts[key]+=report[key]
        if hashlib.sha256((folder/'decisions.npz').read_bytes()).hexdigest()!=report['decisions_sha256']:
            raise ValueError('Shard artifact changed')
        with np.load(folder/'decisions.npz',allow_pickle=False) as z:
            np.testing.assert_array_equal(z['methods'],METHODS)
            np.testing.assert_array_equal(z['levels'],LEVELS)
            for index,case_id in enumerate(z['case_ids']):
                if str(case_id) in verified:raise ValueError('Duplicated case')
                verified[str(case_id)]={key:z[key][index].copy() for key in ('stop','direction','checkpoints','naive')}
        records.append(dict(batch=folder.name,verification=report,
                            verification_sha256=hashlib.sha256((folder/'VERIFICATION.json').read_bytes()).hexdigest()))
    ids=[record['case_id'] for record in metadata['cases']]
    if len(set(ids))!=len(ids) or set(ids)!=set(verified):
        raise ValueError('Missing/extra cases')
    expected_steps=sum(record['n'] for record in metadata['cases'])*metadata['repeats']
    if counts['pairs']!=len(ids) or counts['paired_query_steps']!=expected_steps or counts['integer_expert_updates']!=64*expected_steps:
        raise ValueError('Incomplete replay coverage')
    if counts['saved_decisions']!=len(ids)*metadata['repeats']*len(METHODS)*len(LEVELS):
        raise ValueError('Incomplete decision coverage')
    payload={key:np.stack([verified[case_id][key] for case_id in ids]) for key in ('stop','direction','checkpoints','naive')}
    payload.update(case_ids=np.array(ids),methods=np.array(METHODS),levels=np.array(LEVELS))
    atomic_npz(directory/'decisions.npz',payload)
    verification=dict(status='passed',**counts,complete_reference=metadata['complete_reference'],checks=checks,
                      decisions_sha256=hashlib.sha256((directory/'decisions.npz').read_bytes()).hexdigest(),
                      execution='Unchanged frozen auditor, batched with exact disjoint case coverage')
    (directory/'VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
    parallel=dict(status='passed',workers=workers,all_original_case_records_and_traces_unchanged=True,
                  exact_math_comb_cache_entries=400000,
                  frozen_auditor_sha256=lock['sha256']['experiments/stage13/audit_stage13.py'],
                  batches=records)
    (directory/'PARALLEL_AUDIT.json').write_text(json.dumps(parallel,indent=2)+'\n')
    print(json.dumps(verification,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--batch-name',default='audit_batches')
    args=parser.parse_args()
    if args.workers<1:parser.error('Positive worker count required')
    main(Path(args.input).resolve(),args.workers,args.batch_name)
