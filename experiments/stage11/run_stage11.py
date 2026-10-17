from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import time
import numpy as np
from boosting import evaluate,Q,B
from stage11_common import (ROOT,METHODS,verify_protocol,validate_sources,source_curves,
    cache_key,serialize,aggregate,write_csv,sha256)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage9-input',required=True);p.add_argument('--stage10-input',required=True)
    p.add_argument('--output',required=True);p.add_argument('--canonical-reference',action='store_true')
    args=p.parse_args();start=time.perf_counter();lock,_=verify_protocol()
    old=Path(args.stage9_input).resolve();source=Path(args.stage10_input).resolve();out=Path(args.output).resolve()
    if out.exists():p.error('Use a new output directory')
    snapshot,cases,targets,trials=validate_sources(old,source,canonical=args.canonical_reference)
    canonical=snapshot==json.loads((ROOT/'STAGE10_TRACE_MANIFEST.json').read_text())
    if args.canonical_reference and not canonical:raise ValueError('Canonical source fingerprints differ')
    (out/'curves').mkdir(parents=True)
    meta=dict(status='running',protocol_lock=lock,source_manifest=snapshot,canonical_source=canonical,
        repeats=100,cases=[c for c,_,_ in cases],methods=METHODS,wealth_grid=Q,rejection_wealth=B,
        python=platform.python_version(),numpy=np.__version__,
        source_audits='prediction capital and calibration audits reused; not repeated')
    (out/'run_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    cache={};hashes={}
    for case,_,y in cases:
        curves,_,ledger=source_curves(old,source,case);key=cache_key(y,ledger,curves[0])
        if key not in cache:cache[key]=evaluate(y,ledger,curves[0])
        result=cache[key]
        name=case['case_id']+'.npz';np.savez_compressed(out/'curves'/name,**result)
        hashes[name]=sha256(out/'curves'/name)
        means={}
        for j,method in enumerate(METHODS[6:]):
            target,rows=serialize(case,method,result['counts'][j],y,result['repaired'][j])
            targets.append(target);trials.extend(rows);means[method]=target['mean_queries']
        print(f"{case['scenario']:17s} {case['language_pair']} {case['target_system']:28s} "
              f"grid={means['grid_ppr95']:.3f} boosted={means['boosted_ppr95']:.3f}",flush=True)
    order=lambda r:(r['scenario'],r['language_pair'],r['target_system'],r['method'],r.get('repeat',-1))
    targets.sort(key=order);trials.sort(key=order)
    write_csv(out/'by_target.csv',targets);write_csv(out/'per_trial.csv',trials)
    write_csv(out/'summary.csv',aggregate(targets))
    meta.update(status='complete',completed_cases=len(cases),method_trajectories=len(trials),
        distinct_model_free_ledgers=len(cache),curve_sha256=hashes,runtime_seconds=time.perf_counter()-start)
    (out/'run_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f"Finished {len(cases)} cases and {len(trials)} compared trajectories in {meta['runtime_seconds']:.1f}s",flush=True)


if __name__=='__main__':main()
