from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import time
import numpy as np
from stage10_common import (verify_protocol,validate_source,serialize,write_csv,
                            aggregate,sha256,ROOT,METHODS,verify_certificate_design)
from calibrate_stage10 import load_certificate,load_stage9
from calibration_control import evaluate_control


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage9-input',required=True)
    p.add_argument('--stage9-certificates',required=True)
    p.add_argument('--certificates',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--canonical-reference',action='store_true')
    args=p.parse_args()
    start=time.perf_counter()
    lock,_=verify_protocol()
    source=Path(args.stage9_input).resolve();certdir=Path(args.certificates).resolve()
    parentdir=Path(args.stage9_certificates).resolve();out=Path(args.output).resolve()
    if (out/'run_metadata.json').exists():p.error('Use a new output directory')
    snapshot,parent_meta,cases,targets,trials=validate_source(source,require_reference=args.canonical_reference)
    canonical=snapshot==json.loads((ROOT/'STAGE9_TRACE_MANIFEST.json').read_text())
    if args.canonical_reference and not canonical:raise ValueError('Canonical trace manifest differs')
    certificates={};tables={}
    for n in sorted({c['n'] for c,_,_ in cases}):
        cert,t=load_certificate(certdir,n,verify_runtime=True)
        verify_certificate_design(cert)
        parent,raw,_=load_stage9(parentdir,n,verify_runtime=True)
        if parent!=parent_meta['certificates'][str(n)]:raise ValueError('Wrong source certificates')
        if cert['parent_certificate_sha256']!=sha256(parentdir/f'certificate_{n}.json'):
            raise ValueError('Fine calibration used a different parent certificate')
        certificates[str(n)]={name:sha256(certdir/name) for name in (f'certificate_{n}.json',f'states_{n}.npz')}
        tables[n]=(raw,t)
    (out/'curves').mkdir(parents=True,exist_ok=True)
    metadata=dict(status='running',protocol_lock=lock,source_manifest=snapshot,
                  canonical_source=canonical,repeats=100,cases=[c for c,_,_ in cases],
                  methods=METHODS,certificate_sha256=certificates,
                  python=platform.python_version(),numpy=np.__version__,
                  prediction_capital='unchanged; reuse of the source Stage 9 independent audit')
    (out/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    for case,history,y in cases:
        with np.load(source/'curves'/(case['case_id']+'.npz')) as f:
            ledger=f['selected']
        raw,cal=tables[case['n']]
        fine,fr=evaluate_control(y,ledger,raw,cal['fine'])
        if np.array_equal(cal['fine'],cal['repair']):
            repair,rr=fine,fr
        else:repair,rr=evaluate_control(y,ledger,raw,cal['repair'])
        np.savez_compressed(out/'curves'/(case['case_id']+'.npz'),
                            fine_counts=fine,fine_repaired=fr,repair_counts=repair,repair_repaired=rr)
        means={}
        for method,curve,flags in (('fine_raw95',fine,fr),('repair_raw95',repair,rr)):
            target,rows=serialize(case,method,curve,y,flags)
            targets.append(target);trials.extend(rows);means[method]=target['mean_queries']
        print(f"{case['scenario']:17s} {case['language_pair']} {case['target_system']:28s} "
              f"fine={means['fine_raw95']:.3f} repaired={means['repair_raw95']:.3f}",flush=True)
    order=lambda r:(r['scenario'],r['language_pair'],r['target_system'],r['method'],r.get('repeat',-1))
    targets.sort(key=order);trials.sort(key=order)
    write_csv(out/'by_target.csv',targets);write_csv(out/'per_trial.csv',trials)
    write_csv(out/'summary.csv',aggregate(targets))
    metadata.update(status='complete',completed_cases=len(cases),method_trajectories=len(trials),
                    runtime_seconds=time.perf_counter()-start)
    (out/'run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(f"Finished {len(cases)} cases and {len(trials)} trajectories in {metadata['runtime_seconds']:.1f}s",flush=True)


if __name__=='__main__':main()
