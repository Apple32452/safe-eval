"""Frozen-source validation and shared result serialization for Stage 10."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'stage9'))
from stage9_common import verify_protocol as verify_stage9,build_cases,write_csv,aggregate
from stage9_engine import METHODS as PARENT_METHODS
from stage8_common import decisions,target_record,METRICS

METHODS=(*PARENT_METHODS,'fine_raw95','repair_raw95')
SCENARIOS=('aligned','permuted_history','reversed_history')
CONTRASTS=((3,5),(3,4),(3,1),(3,2),(3,0),(4,1),(5,4),(5,1),(5,0))


def read_csv(path):
    with Path(path).open(newline='') as handle:return list(csv.DictReader(handle))


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def verify_protocol():
    lock=json.loads((ROOT/'PROTOCOL_LOCK.json').read_text())
    for name,h in lock['sha256'].items():
        if sha256(ROOT/name)!=h:raise ValueError('Stage 10 locked file changed: '+name)
    _,data=verify_stage9()
    return lock,data


def verify_certificate_design(record):
    from fractions import Fraction
    from calibrate_stage10 import ROUNDS,MAX_STATES,MAX_TRANSITIONS,exact_risk
    if (record['rounds'],record['max_states'],record['max_transitions'])!=(ROUNDS,MAX_STATES,MAX_TRANSITIONS):
        raise ValueError('Calibration settings differ from frozen design')
    for name,h in record['source_sha256'].items():
        if sha256(ROOT/name)!=h:raise ValueError('Certificate-generating source differs: '+name)
    probes=record['evaluated']
    low=Fraction(record['integer_threshold']-1);high=Fraction(record['integer_threshold'])
    if len(probes)!=ROUNDS+2 or probes[0]['threshold']!=float(low) or probes[1]['threshold']!=float(high):
        raise ValueError('Fine search starting bracket differs')
    if exact_risk(probes[0])<=Fraction(1,20) or exact_risk(probes[1])>Fraction(1,20):
        raise ValueError('Invalid initial fine bracket')
    for p in probes[2:]:
        mid=(low+high)/2
        if p['threshold']!=float(mid):raise ValueError('Fine midpoint differs from frozen bisection')
        if exact_risk(p)<=Fraction(1,20):high=mid
        else:low=mid
    if (str(low),str(high))!=(record['unsafe_fraction'],record['safe_fraction']):
        raise ValueError('Fine search final endpoints differ')
    rp=record['repair_probes']
    expected=[high,high-Fraction(1,2),high-Fraction(1,8),high-Fraction(1,64)]
    if len(rp)!=4 or [p['threshold'] for p in rp]!=[float(h) for h in expected]:
        raise ValueError('Repaired probe grid differs')
    valid=[float(high)]
    for i,p in enumerate(rp):
        if p['status']=='complete':
            if len(p['surviving_strings'])!=record['n']+1:raise ValueError('Incomplete repaired count')
            if exact_risk(p)<=Fraction(1,20):valid.append(p['threshold'])
        elif p['status']=='skipped':
            if i==0 or rp[0]['status']!='capped':raise ValueError('Unjustified skipped probe')
        elif p['status']=='capped':
            if 'surviving_strings' in p or 'risk_numerator' in p:raise ValueError('Capped count claims risk')
        else:raise ValueError('Unknown repaired probe status')
    if record['repair_threshold']!=min(valid):raise ValueError('Repaired threshold selection differs')


def integer_decisions(counts,y,repaired):
    lower,upper=counts
    n,repeats=lower.shape;k=int(np.asarray(y,dtype=int).sum())
    nonempty=upper>=lower
    precise=nonempty&(10*(upper.astype(np.int32)-lower)<=n)
    if not precise.any(axis=0).all():raise ValueError('Missing nonempty precision stop')
    stops=precise.argmax(axis=0)+1;idx=np.arange(repeats)
    lo=lower[stops-1,idx];hi=upper[stops-1,idx]
    coverage=((lower<=k)&(k<=upper)).all(axis=0)
    if not np.all(counts[:,-1]==k):raise ValueError('Full mean not exact')
    flags=(np.asarray(repaired,dtype=bool)&(np.arange(n)[:,None]<stops)).any(axis=0)
    error=np.abs((lo.astype(np.int32)+hi-2*k)/(2*n))
    if np.any(error[coverage]>.05+1e-12):raise ValueError('Covered stop exceeds precision')
    return dict(stop_queries=stops,stop_lower=lo/n,stop_upper=hi/n,
                simultaneous_coverage=coverage.astype(int),empty_ever=(~nonempty).any(axis=0).astype(int),
                stopped_absolute_error=error,repair_before_stop=flags.astype(int),
                true_mean=np.full(repeats,k/n))


def serialize(case,method,counts,y,repaired):
    # Original floating Stage 9 decision route; auditor uses integer_decisions.
    d=decisions(counts/case['n'],float(y.mean()))
    flags=(repaired&(np.arange(case['n'])[:,None]<d['stop_queries'])).any(axis=0).astype(int)
    target=target_record(case,method,d,flags)
    trials=[]
    for r in range(len(d['stop_queries'])):
        item={k:target[k] for k in ('case_id','scenario','language_pair','target_system','method','n')}
        item.update(repeat=r,true_mean=float(y.mean()),repair_before_stop=int(flags[r]))
        item.update({k:float(v[r]) if v.dtype.kind=='f' else int(v[r]) for k,v in d.items()})
        trials.append(item)
    return target,trials


def summary_from_decision(case,method,d):
    return dict(case_id=case['case_id'],scenario=case['scenario'],language_pair=case['language_pair'],
                target_system=case['target_system'],method=method,paths=len(d['stop_queries']),n=case['n'],
                nominal_anytime_confidence=.95,mean_queries=float(d['stop_queries'].mean()),
                simultaneous_coverage=float(d['simultaneous_coverage'].mean()),
                empty_ever_rate=float(d['empty_ever'].mean()),
                repair_before_stop_rate=float(d['repair_before_stop'].mean()),
                stopped_error_over_epsilon_rate=float((d['stopped_absolute_error']>.05+1e-12).mean()))


def check_trials(case,method,d,lookup):
    for r in range(len(d['stop_queries'])):
        row=lookup[(case['case_id'],method,r)]
        for field in ('scenario','language_pair','target_system','n'):
            if str(row[field])!=str(case[field]):raise ValueError('Saved case metadata differs')
        for field,array in d.items():
            if not math.isclose(float(row[field]),float(array[r]),rel_tol=0,abs_tol=1e-12):
                raise ValueError('Saved decision differs: '+case['case_id']+' '+method+' '+field)
    return len(d['stop_queries'])


def check_summary(rows,path):
    saved={(r['case_id'],r['method']):r for r in read_csv(path)}
    if len(saved)!=len(rows):raise ValueError('Wrong number of target summaries')
    for row in rows:
        old=saved[(row['case_id'],row['method'])]
        for field in METRICS:
            if not math.isclose(float(old[field]),row[field],rel_tol=0,abs_tol=1e-12):
                raise ValueError('Target summary differs: '+field)
    return len(rows)*len(METRICS)


def validate_source(directory,require_reference=False):
    """Reuse an audited full Stage 9 run and reconstruct all its decisions."""
    directory=Path(directory)
    lock,data=verify_stage9()
    meta=json.loads((directory/'run_metadata.json').read_text())
    audit=json.loads((directory/'VERIFICATION.json').read_text())
    if meta['status']!='complete' or meta['protocol_lock']!=lock or meta['repeats']!=100:
        raise ValueError('A complete, frozen, 100-repeat Stage 9 source is required')
    expected=dict(all_checks_passed=True,saved_decisions_checked=46800,
                  raw95_stopping_bounds_checked=35100,query_and_capital_replay_steps=6156900,
                  exact_backward_risk_counts_checked=1571,stage8_raw_metric_values_checked=585,
                  largest_extra_vs_raw95=0)
    if any(audit[k]!=v for k,v in expected.items()):raise ValueError('Stage 9 audit is incomplete')
    if tuple(meta['methods'])!=PARENT_METHODS:raise ValueError('Wrong parent methods')
    cases=build_cases(data)
    if meta['cases']!=[c for c,_,_ in cases]:raise ValueError('Wrong parent cases or seeds')
    source_rows=read_csv(directory/'per_trial.csv')
    lookup={(r['case_id'],r['method'],int(r['repeat'])):r for r in source_rows}
    if len(source_rows)!=46800 or len(lookup)!=46800:raise ValueError('Wrong parent decisions')
    archived=json.loads((ROOT.parent/'stage9/results_reference/run_metadata.json').read_text())
    reconstructed=[];hashes={};decisions_checked=0
    for case,history,y in cases:
        filename=directory/'curves'/(case['case_id']+'.npz')
        hashes['curves/'+filename.name]=sha256(filename)
        with np.load(filename) as f:
            counts=f['counts'];selected=f['selected'];repaired=f['repaired']
        n=case['n'];repeats=100
        if counts.shape!=(4,2,n,repeats) or selected.shape!=(n,repeats) or repaired.shape!=(3,n,repeats):
            raise ValueError('Wrong parent trace dimensions')
        if not np.array_equal(np.sort(selected,axis=0),np.broadcast_to(np.arange(n)[:,None],selected.shape)):
            raise ValueError('Parent query ledger is not unique')
        digest=hashlib.sha256(np.asarray(selected,dtype='<i4').tobytes()).hexdigest()
        if digest!=meta['raw_stream_sha256'][case['case_id']] or digest!=archived['raw_stream_sha256'][case['case_id']]:
            raise ValueError('Parent stream differs from frozen reference')
        for j,method in enumerate(PARENT_METHODS):
            flags=np.zeros((n,repeats),dtype=bool) if j==0 else repaired[j-1]
            d=integer_decisions(counts[j],y,flags)
            decisions_checked+=check_trials(case,method,d,lookup)
            reconstructed.append(summary_from_decision(case,method,d))
    values_checked=check_summary(reconstructed,directory/'by_target.csv')
    source_aggregate={(r['scenario'],r['language_pair'],r['method']):r for r in read_csv(directory/'summary.csv')}
    aggregate_rows=aggregate(reconstructed)
    if len(source_aggregate)!=len(aggregate_rows):raise ValueError('Wrong parent aggregate rows')
    for row in aggregate_rows:
        saved=source_aggregate[(row['scenario'],row['language_pair'],row['method'])]
        for field in METRICS:
            if abs(float(saved[field])-row[field])>1e-12:raise ValueError('Parent aggregate differs')
    archived_rows={(r['case_id'],r['method']):r for r in read_csv(ROOT.parent/'stage9/results_reference/by_target.csv')}
    different=[]
    for row in reconstructed:
        ref=archived_rows[(row['case_id'],row['method'])]
        for field in METRICS:
            if abs(row[field]-float(ref[field]))>1e-12:
                different.append(dict(case_id=row['case_id'],method=row['method'],field=field,
                                      local=row[field],reference=float(ref[field])))
    if require_reference and different:raise ValueError('Canonical source differs from Stage 9 reference')
    for name in ('run_metadata.json','VERIFICATION.json','per_trial.csv','by_target.csv','summary.csv'):
        hashes[name]=sha256(directory/name)
    manifest=dict(stage9_protocol_sha256=sha256(ROOT.parent/'stage9/PROTOCOL_LOCK.json'),
                  file_sha256=hashes,repeats=100,cases=117,decisions_checked=decisions_checked,
                  metric_values_checked=values_checked,archived_metric_differences=different,
                  original_capital_audit=audit,scope='verified reuse of a previously audited Stage 9 run; no new capital replay')
    return manifest,meta,cases,reconstructed,source_rows


def snapshot_main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    args=p.parse_args()
    manifest,*_=validate_source(args.input,require_reference=True)
    out=Path(args.output)
    if out.exists():p.error('Use a new manifest path')
    out.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Verified source:',manifest['decisions_checked'],'decisions,',manifest['metric_values_checked'],'metric values')


if __name__=='__main__':snapshot_main()
