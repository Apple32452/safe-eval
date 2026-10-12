"""Follow-up diagnostic: unchanged Stage 5 engines on the Stage 6 WMT23 pools."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
from reserve_fallback import evaluate_reserved,METHODS,WEIGHTS
from wmt_experiment import QueryOracle
from prepare_wmt23 import load_data
from stage7_experiment import (ROOT,build_cases,load_stage6_reference,pack_curves,
    nominal_confidence,write_csv,aggregate)

def verify_configuration():
    lock=json.loads((ROOT/'PROTOCOL_LOCK.json').read_text())
    for name,digest in lock['code_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Locked file changed: {name}')
    parent=json.loads((ROOT/'PARENT_RECORDS.json').read_text())
    for name,digest in parent['stage5_code_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Stage 5 module is no longer unchanged: {name}')
    datasets,provenance=load_data(ROOT/'data')
    if [r['matrix_sha256'] for r in provenance['datasets']]!=lock['matrix_sha256']:
        raise ValueError('Dataset differs from the locked comparison')
    return lock,datasets,provenance

def run_case(job):
    case,history,outcomes,repeats,output,stage6_expected=job
    n=len(outcomes); truth=float(outcomes.mean())
    runs,diag=evaluate_reserved(history,QueryOracle(outcomes,repeats),repeats,seed=case['raw_seed'])
    selected_hash=hashlib.sha256(np.asarray(diag['selected'],dtype='<i4').tobytes()).hexdigest()
    raw=runs['published_ppr95']['stop']
    if stage6_expected is not None:
        if selected_hash!=stage6_expected['raw_stream_sha256']:
            raise RuntimeError('Stage 7 raw stream differs from Stage 6')
        np.testing.assert_array_equal(raw,stage6_expected['raw95'])
    trace=pack_curves(runs,diag['selected'])
    rows=np.arange(repeats)
    trace['repair_before']=np.stack([diag['repair_before_stop_ever'][f'reserve_mix{int(100*w)}'] for w in WEIGHTS]).astype(np.uint8)
    trace['stop_strength']=np.stack([diag['prediction_strength'][runs[m]['stop']-1,rows] for m in METHODS])
    trace['stop_gate']=np.stack([diag['legacy_gate'][runs[m]['stop']-1,rows] for m in METHODS]).astype(np.uint8)
    np.savez_compressed(Path(output)/'curves'/f"{case['case_id']}.npz",**trace)
    target_rows,trial_rows=[],[]
    for method in METHODS:
        run=runs[method]
        simultaneous=((run['lower']<=truth+1e-12)&(truth<=run['upper']+1e-12)).all(axis=0)
        empty=(run['lower']>run['upper']).any(axis=0)
        repair=diag['repair_before_stop_ever'].get(method,np.zeros(repeats,dtype=bool))
        strength=diag['prediction_strength'][run['stop']-1,rows]
        gate=diag['legacy_gate'][run['stop']-1,rows]
        errors=np.abs((run['stop_lower']+run['stop_upper'])/2-truth)
        if np.any(run['stop_upper']<run['stop_lower']) or np.any(run['stop_upper']-run['stop_lower']>.1+1e-12):
            raise RuntimeError('Invalid precision decision')
        meta={k:case[k] for k in ('case_id','scenario','protocol','language_pair','target_system')}
        target_rows.append(dict(**meta,method=method,paths=repeats,n=n,
            nominal_anytime_confidence=nominal_confidence(method),mean_queries=float(run['stop'].mean()),
            simultaneous_coverage=float(simultaneous.mean()),empty_ever_rate=float(empty.mean()),
            repair_before_stop_rate=float(repair.mean()),stopped_error_over_epsilon_rate=float((errors>.05+1e-12).mean()),
            mean_paired_query_change_vs_raw95=float((run['stop']-raw).mean()),
            shared_predictor_strength_at_stop=float(strength.mean()),shared_gate_at_stop=float(gate.mean())))
        for j in range(repeats):
            trial_rows.append(dict(**meta,method=method,repeat=j,n=n,true_mean=truth,
                stop_queries=int(run['stop'][j]),stop_lower=float(run['stop_lower'][j]),stop_upper=float(run['stop_upper'][j]),
                simultaneous_coverage=int(simultaneous[j]),empty_ever=int(empty[j]),repair_before_stop=int(repair[j]),
                stopped_absolute_error=float(errors[j]),raw95_stop=int(raw[j]),
                shared_predictor_strength_at_stop=float(strength[j]),shared_gate_at_stop=float(gate[j])))
    audit=dict(case_id=case['case_id'],raw_stream_sha256=selected_hash,
        stage6_paired_stream_checked=stage6_expected is not None,engine_full_path_reserve_containment_checked=True)
    return case,target_rows,trial_rows,audit

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repeats',type=int,default=100)
    p.add_argument('--workers',type=int,default=2)
    p.add_argument('--output',default='results_local')
    args=p.parse_args()
    if args.repeats<1 or args.workers<1:p.error('repeats and workers must be positive')
    lock,datasets,provenance=verify_configuration()
    reference,comparators=load_stage6_reference()
    reference_cases={c['case_id']:c for c in reference['cases']}
    cases=build_cases(datasets)
    output=Path(args.output).resolve();(output/'curves').mkdir(parents=True,exist_ok=True)
    jobs=[]
    for case,history,outcomes in cases:
        prior=reference_cases[case['case_id']]
        for field in ('n','raw_seed','background_systems','history_sha256'):
            if case[field]!=prior[field]:raise ValueError(f'Stage 6 case alignment differs: {field}')
        expected=None
        if args.repeats==reference['repeats']:
            expected={name:np.array([comparators[(case['case_id'],j)][name] for j in range(args.repeats)])
                      for name in ('raw95','active10','random10')}
            expected['raw_stream_sha256']=prior['raw_stream_sha256']
        jobs.append((case,history,outcomes,args.repeats,str(output),expected))
    start=time.perf_counter()
    metadata=dict(status='running',repeats=args.repeats,workers=args.workers,cases=[c for c,_,_ in cases],
        methods=METHODS,weights=WEIGHTS,protocol_lock=lock,source_provenance=provenance,
        python=platform.python_version(),numpy=np.__version__,stage6_pairing=args.repeats==reference['repeats'])
    (output/'run_metadata.json').write_text(json.dumps(metadata,indent=2))
    target_rows,trial_rows,case_audits=[],[],[]
    def collect(result):
        case,targets,trials,audit=result
        target_rows.extend(targets);trial_rows.extend(trials);case_audits.append(audit)
        costs={r['method']:r['mean_queries'] for r in targets}
        active='n/a'
        if metadata['stage6_pairing']:
            active=f"{np.mean([comparators[(case['case_id'],j)]['active10'] for j in range(args.repeats)]):6.1f}"
        print(f"{case['scenario']:17s} {case['language_pair']} {case['target_system']:26s} raw95={costs['published_ppr95']:6.1f} trust={costs['legacy_trust201']:6.1f} pred={costs['prediction_count_grid']:6.1f} mix75={costs['reserve_mix75']:6.1f} active10={active}",flush=True)
    if args.workers==1:
        for job in jobs:collect(run_case(job))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for future in as_completed([pool.submit(run_case,job) for job in jobs]):collect(future.result())
    key=lambda r:(r['scenario'],r['language_pair'],r['target_system'],r['method'],r.get('repeat',-1))
    target_rows.sort(key=key);trial_rows.sort(key=key)
    summary=aggregate(target_rows)
    write_csv(output/'by_target.csv',target_rows);write_csv(output/'per_trial.csv',trial_rows)
    write_csv(output/'summary.csv',summary);(output/'summary.json').write_text(json.dumps(summary,indent=2))
    metadata.update(status='complete',runtime_seconds=time.perf_counter()-start,
        completed_cases=len(cases),method_trajectories=len(trial_rows),case_audits=case_audits)
    (output/'run_metadata.json').write_text(json.dumps(metadata,indent=2))
    print(f"Finished {len(cases)} cases and {len(trial_rows)} method trajectories in {metadata['runtime_seconds']:.1f}s. Results: {args.output}",flush=True)

if __name__=='__main__':main()
