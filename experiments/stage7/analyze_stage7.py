"""Audit full saved CS curves, raw PPR replay, and Stage 6 paired comparisons."""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from binary_control import ppr_interval
from reserve_fallback import METHODS,WEIGHTS
from prepare_wmt23 import load_data
from stage7_experiment import (ROOT,build_cases,load_stage6_reference,unpack_curves,
    nominal_confidence,aggregate,write_csv,SCENARIOS)

def read_csv(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))

def check_close(saved,actual,label):
    if not math.isclose(float(saved),float(actual),rel_tol=1e-12,abs_tol=1e-12):
        raise ValueError(f'Saved value differs from audited result: {label}')

def same_confidence_sets(a,b):
    """Compare represented sets; empty intervals have no unique endpoints."""
    a,b=np.asarray(a),np.asarray(b)
    if a.shape!=b.shape or a.shape[0]!=2:return False
    nonempty_a=a[0]<=a[1];nonempty_b=b[0]<=b[1]
    if not np.array_equal(nonempty_a,nonempty_b):return False
    return bool(np.array_equal(a[:,nonempty_a],b[:,nonempty_b]))

def replay_raw(selected,y,seed):
    """Rebuild uniform indices and original-grid raw CSs at four error levels."""
    n,repeats=selected.shape
    rng=np.random.default_rng(seed);rows=np.arange(repeats)
    unseen=np.ones((repeats,n),dtype=bool);successes=np.zeros(repeats,dtype=int)
    specifications=[('published_ppr95',1.)]+[(f'ppr_reserve{int(100*w)}',w) for w in WEIGHTS]
    current={name:(np.zeros(repeats),np.ones(repeats)) for name,_ in specifications}
    saved={name:[] for name,_ in specifications}
    for t in range(1,n+1):
        cdf=np.cumsum(unseen/(n-t+1),axis=1);cdf[:,-1]=1.
        indices=np.sum(cdf<=rng.random(repeats)[:,None],axis=1)
        if not np.array_equal(indices,selected[t-1]):raise ValueError('Raw stream is not its unchanged uniform seeded permutation')
        unseen[rows,indices]=False;successes+=y[indices].astype(int)
        counts,inverse=np.unique(successes,return_inverse=True)
        for name,w in specifications:
            lo,hi=ppr_interval(counts,t,n,.05*w)
            previous_lo,previous_hi=current[name]
            lo,hi=np.maximum(previous_lo,lo[inverse]),np.minimum(previous_hi,hi[inverse])
            if t==n:lo=successes/n;hi=lo.copy()
            current[name]=(lo,hi);saved[name].append(np.stack([lo,hi]))
    return {name:np.asarray(values).transpose(1,0,2) for name,values in saved.items()}

def audit_decisions(curve,truth):
    lower,upper=curve
    precise=(upper>=lower)&(upper-lower<=.1+1e-12)
    if not precise.any(axis=0).all():raise ValueError('No nonempty precision stop on a saved path')
    stop=np.argmax(precise,axis=0)+1;rows=np.arange(len(stop))
    lo,hi=lower[stop-1,rows],upper[stop-1,rows]
    if not np.allclose(lower[-1],truth,atol=1e-12) or not np.allclose(upper[-1],truth,atol=1e-12):
        raise ValueError('Full-evaluation saved mean is not exact')
    simultaneous=((lower<=truth+1e-12)&(truth<=upper+1e-12)).all(axis=0)
    errors=np.abs((lo+hi)/2-truth)
    if np.any(errors[simultaneous]>.05+1e-12):raise ValueError('Covered precision stop has too-large midpoint error')
    return dict(stop_queries=stop,stop_lower=lo,stop_upper=hi,simultaneous_coverage=simultaneous.astype(int),
                empty_ever=(lower>upper).any(axis=0).astype(int),stopped_absolute_error=errors)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='results_local')
    args=p.parse_args();output=Path(args.input)
    meta=json.loads((output/'run_metadata.json').read_text())
    if meta['status']!='complete':raise ValueError('Experiment is incomplete')
    datasets,_=load_data(ROOT/'data')
    expected_cases={c['case_id']:(c,h,y) for c,h,y in build_cases(datasets)}
    reference,stage6=load_stage6_reference()
    stage6_cases={c['case_id']:c for c in reference['cases']}
    saved_rows=read_csv(output/'per_trial.csv');saved_targets=read_csv(output/'by_target.csv');saved_summary=read_csv(output/'summary.csv')
    grouped=defaultdict(list)
    for row in saved_rows:grouped[(row['case_id'],row['method'])].append(row)
    if len(saved_rows)!=meta['completed_cases']*meta['repeats']*len(METHODS):raise ValueError('Saved decision count is incomplete')
    audited_targets=[];all_trials={};raw_cache={};seen_cases=set()
    checked=bounds=paired=0
    empty_raw_representation_events=0
    maximum_primary_extra=0
    for case in meta['cases']:
        case_id=case['case_id']
        if case_id in seen_cases:raise ValueError('Repeated case')
        seen_cases.add(case_id)
        expected,history,y=expected_cases[case_id]
        for field in ('scenario','language_pair','target_system','n','raw_seed','background_systems','history_sha256'):
            if case[field]!=expected[field]:raise ValueError(f'Target exclusion or case adapter mismatch: {field}')
        n=len(y);truth=float(y.mean())
        with np.load(output/'curves'/f'{case_id}.npz',allow_pickle=False) as z:trace={name:z[name] for name in z.files}
        selected=trace['selected']
        if selected.shape!=(n,meta['repeats']):raise ValueError('Wrong query-curve dimensions')
        curves=unpack_curves(trace)
        target_key=(case['language_pair'],case['target_system'])
        if target_key not in raw_cache:raw_cache[target_key]=(selected.copy(),replay_raw(selected,y,case['raw_seed']))
        elif not np.array_equal(selected,raw_cache[target_key][0]):raise ValueError('Raw paths change with historical scenario')
        replayed=raw_cache[target_key][1]
        for name,curve in replayed.items():
            if not same_confidence_sets(curves[name],curve):raise ValueError(f'Raw PPR full confidence set differs from original-grid replay: {name}')
            empty_raw_representation_events+=int(np.count_nonzero(np.any(curves[name]!=curve,axis=0)))
        decisions={name:audit_decisions(curves[name],truth) for name in METHODS}
        raw_stop=decisions['published_ppr95']['stop_queries']
        if meta['stage6_pairing']:
            digest=hashlib.sha256(np.asarray(selected,dtype='<i4').tobytes()).hexdigest()
            if digest!=stage6_cases[case_id]['raw_stream_sha256']:raise ValueError('Stage 6 raw path hash differs')
            expected_stop=np.array([stage6[(case_id,j)]['raw95'] for j in range(meta['repeats'])])
            np.testing.assert_array_equal(raw_stop,expected_stop);paired+=len(raw_stop)
        for w in WEIGHTS:
            suffix=str(int(100*w));mixture='reserve_mix'+suffix;strict='ppr_reserve'+suffix
            if np.any(curves[mixture][0]<curves[strict][0]-1e-12) or np.any(curves[mixture][1]>curves[strict][1]+1e-12):
                raise ValueError('Full saved path violates reserved-raw containment')
            if np.any(decisions[mixture]['stop_queries']>decisions[strict]['stop_queries']):raise ValueError('Reserved stopping bound failed')
            bounds+=len(raw_stop)
        maximum_primary_extra=max(maximum_primary_extra,int((decisions['reserve_mix75']['stop_queries']-raw_stop).max()))
        for method_index,method in enumerate(METHODS):
            decision=decisions[method]
            repair=np.zeros(meta['repeats'],dtype=int)
            if method.startswith('reserve_mix'):
                repair_index=list(WEIGHTS).index(int(method.removeprefix('reserve_mix'))/100)
                repair=trace['repair_before'][repair_index].astype(int)
            saved=sorted(grouped[(case_id,method)],key=lambda r:int(r['repeat']))
            if [int(r['repeat']) for r in saved]!=list(range(meta['repeats'])):raise ValueError('Repeated or missing path rows')
            strength=trace['stop_strength'][method_index];gate=trace['stop_gate'][method_index]
            for j,row in enumerate(saved):
                for field,array in decision.items():check_close(row[field],array[j],field)
                for field,value in [('true_mean',truth),('n',n),('raw95_stop',raw_stop[j]),('repair_before_stop',repair[j]),
                    ('shared_predictor_strength_at_stop',strength[j]),('shared_gate_at_stop',gate[j])]:check_close(row[field],value,field)
                for field in ('case_id','scenario','protocol','language_pair','target_system'):
                    if row[field]!=case[field]:raise ValueError('Saved row metadata differs from its case')
                checked+=1
            all_trials[(case_id,method)]=decision['stop_queries']
            fields={k:case[k] for k in ('case_id','scenario','protocol','language_pair','target_system')}
            audited_targets.append(dict(**fields,method=method,paths=meta['repeats'],n=n,
                nominal_anytime_confidence=nominal_confidence(method),mean_queries=float(decision['stop_queries'].mean()),
                simultaneous_coverage=float(decision['simultaneous_coverage'].mean()),empty_ever_rate=float(decision['empty_ever'].mean()),
                repair_before_stop_rate=float(repair.mean()),stopped_error_over_epsilon_rate=float((decision['stopped_absolute_error']>.05+1e-12).mean()),
                mean_paired_query_change_vs_raw95=float((decision['stop_queries']-raw_stop).mean()),
                shared_predictor_strength_at_stop=float(strength.mean()),shared_gate_at_stop=float(gate.mean())))
    if len(grouped)!=len(audited_targets) or set(seen_cases)!=set(expected_cases):raise ValueError('Unexpected or missing cases/methods')
    target_lookup={(r['case_id'],r['method']):r for r in audited_targets}
    if len(saved_targets)!=len(target_lookup):raise ValueError('Aggregate target count differs')
    for row in saved_targets:
        for field,value in target_lookup[(row['case_id'],row['method'])].items():
            if isinstance(value,(int,float)):check_close(row[field],value,field)
    expected_summary=aggregate(audited_targets)
    summary_lookup={(r['scenario'],r['language_pair'],r['method']):r for r in expected_summary}
    if len(saved_summary)!=len(summary_lookup):raise ValueError('Aggregate scenario count differs')
    for row in saved_summary:
        for field,value in summary_lookup[(row['scenario'],row['language_pair'],row['method'])].items():
            if isinstance(value,(int,float)):check_close(row[field],value,field)
    main_methods=('legacy_trust201','prediction_count_grid','reserve_mix75','legacy_gate201')
    comparison=[]
    for scenario in SCENARIOS:
        for pair in sorted(datasets):
            raw=summary_lookup[(scenario,pair,'published_ppr95')]
            result=dict(scenario=scenario,language_pair=pair,n=datasets[pair][0].shape[1],
                target_systems=raw['target_systems'],raw95_mean_queries=raw['mean_queries'])
            for method in main_methods:
                row=summary_lookup[(scenario,pair,method)]
                result[method+'_mean_queries']=row['mean_queries']
                result[method+'_percent_change']=100*(row['mean_queries']/raw['mean_queries']-1)
                result[method+'_coverage']=row['simultaneous_coverage']
            result['strict_raw96_25_mean_queries']=summary_lookup[(scenario,pair,'ppr_reserve75')]['mean_queries']
            if meta['stage6_pairing']:
                cases=[c for c in meta['cases'] if c['scenario']==scenario and c['language_pair']==pair]
                for method in ('active10','random10'):
                    value=float(np.mean([np.mean([stage6[(c['case_id'],j)][method] for j in range(meta['repeats'])]) for c in cases]))
                    result['stage6_'+method+'_mean_queries']=value
                    result['stage6_'+method+'_percent_change']=100*(value/raw['mean_queries']-1)
            comparison.append(result)
    write_csv(output/'primary_comparison.csv',comparison)
    overall=[]
    for scenario in SCENARIOS:
        selected=[r for r in comparison if r['scenario']==scenario]
        raw_mean=float(np.mean([r['raw95_mean_queries'] for r in selected]))
        methods=list(main_methods)+(['stage6_active10','stage6_random10'] if meta['stage6_pairing'] else [])
        for method in methods:
            method_mean=float(np.mean([r[method+'_mean_queries'] for r in selected]))
            variances=[]
            for pair in sorted(datasets):
                cases=[c for c in meta['cases'] if c['scenario']==scenario and c['language_pair']==pair]
                variance=0.
                for c in cases:
                    baseline=all_trials[(c['case_id'],'published_ppr95')]
                    costs=np.array([stage6[(c['case_id'],j)][method.removeprefix('stage6_')] for j in range(meta['repeats'])]) if method.startswith('stage6_') else all_trials[(c['case_id'],method)]
                    variance+=float(np.var(costs-baseline,ddof=1))/len(costs) if len(costs)>1 else float('nan')
                variances.append(variance/len(cases)**2)
            overall.append(dict(scenario=scenario,method=method,equal_language_raw95_mean=raw_mean,
                equal_language_method_mean=method_mean,percent_query_change=100*(method_mean/raw_mean-1),
                mean_paired_difference=method_mean-raw_mean,conditional_query_randomization_mcse=math.sqrt(sum(variances))/len(selected),
                mcse_scope='Fixed recorded WMT23 pools; not uncertainty for future models, sentences or raters'))
    write_csv(output/'overall_comparison.csv',overall)
    from plot_stage7 import make_figures
    make_figures(comparison,summary_lookup,output)
    audit=dict(saved_decisions_checked=checked,reserved_stopping_bounds_checked=bounds,
        distinct_raw_target_streams_replayed=len(raw_cache),full_saved_case_curves_audited=len(seen_cases),
        stage6_paired_raw_stops_checked=paired,largest_observed_primary_extra_vs_ordinary_raw95=maximum_primary_extra,
        empty_raw_representation_events=empty_raw_representation_events,
        empty_raw_representation_scope='Both intervals empty, with identical nonempty flags; all nonempty endpoints must match exactly; coverage failures remain counted',
        original_raw_count_grid_used=True,all_checks_passed=True)
    (output/'VERIFICATION.json').write_text(json.dumps(audit,indent=2))
    print(f'Checked {checked} saved decisions and {bounds} reserved stopping bounds; audited {len(seen_cases)} case bundles of full confidence-sequence curves and {paired} Stage 6 paired raw stops; wrote comparison tables and figures.')

if __name__=='__main__':main()
