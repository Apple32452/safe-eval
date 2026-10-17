"""Verified reuse of audited Stage 9/10 traces and Stage 11 result helpers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'stage10'))
from stage10_common import (METHODS as SOURCE_METHODS,validate_source,verify_protocol as verify_parent,
    read_csv,sha256,integer_decisions,check_trials,check_summary,summary_from_decision,
    serialize,aggregate,write_csv,SCENARIOS,METRICS)

METHODS=(*SOURCE_METHODS,'grid_ppr95','boosted_ppr95')
CONTRASTS=((3,7),(3,6),(3,5),(3,2),(3,0),(7,6),(7,5),(7,0),(6,0),(2,7))


def verify_protocol():
    lock=json.loads((ROOT/'PROTOCOL_LOCK.json').read_text())
    for name,digest in lock['sha256'].items():
        if sha256(ROOT/name)!=digest:raise ValueError('Locked Stage 11 file changed: '+name)
    _,data=verify_parent()
    return lock,data


def source_curves(stage9,stage10,case):
    name=case['case_id']+'.npz'
    with np.load(Path(stage9)/'curves'/name) as f:
        old=f['counts'];ledger=f['selected'];flags=f['repaired']
    with np.load(Path(stage10)/'curves'/name) as f:
        extra=[f['fine_counts'],f['repair_counts']]
        extra_flags=[f['fine_repaired'],f['repair_repaired']]
    return [*old,*extra],[np.zeros(ledger.shape,dtype=bool),*flags,*extra_flags],ledger


def validate_sources(stage9,stage10,canonical=False):
    old,_,cases,_,_=validate_source(stage9,require_reference=canonical)
    stage10=Path(stage10);lock,_=verify_parent()
    meta=json.loads((stage10/'run_metadata.json').read_text())
    audit=json.loads((stage10/'VERIFICATION.json').read_text())
    expected=dict(all_checks_passed=True,saved_decisions_checked=70200,
        stage9_metric_values_preserved=2340,target_metric_values_checked=3510,
        backward_fine_risk_counts_checked=1568,repaired_risk_certificates_independently_checked=4,
        raw95_stopping_bounds_checked=23400,new_control_query_replay_steps=12313800,
        prediction_capital_replayed_again=False)
    if any(audit.get(k)!=v for k,v in expected.items()):raise ValueError('A complete Stage 10 audit is required')
    if (meta['status']!='complete' or meta['repeats']!=100 or meta['protocol_lock']!=lock
        or tuple(meta['methods'])!=SOURCE_METHODS or meta['source_manifest']!=old
        or meta['cases']!=[c for c,_,_ in cases]):raise ValueError('Wrong Stage 10 source or protocol')
    rows=read_csv(stage10/'per_trial.csv')
    lookup={(r['case_id'],r['method'],int(r['repeat'])):r for r in rows}
    if len(rows)!=70200 or len(lookup)!=70200:raise ValueError('Wrong source decision count')
    hashes={};summaries=[];checked=0
    for case,_,y in cases:
        curves,flags,ledger=source_curves(stage9,stage10,case)
        n=case['n'];repeats=100
        hashes['curves/'+case['case_id']+'.npz']=sha256(stage10/'curves'/(case['case_id']+'.npz'))
        for method,curve,repair in zip(SOURCE_METHODS,curves,flags):
            if curve.shape!=(2,n,repeats) or repair.shape!=(n,repeats):raise ValueError('Wrong source dimensions')
            d=integer_decisions(curve,y,repair)
            checked+=check_trials(case,method,d,lookup)
            summaries.append(summary_from_decision(case,method,d))
    values=check_summary(summaries,stage10/'by_target.csv')
    check_aggregate(summaries,stage10/'summary.csv')
    archived={(r['case_id'],r['method']):r for r in read_csv(ROOT.parent/'stage10/results_reference/by_target.csv')}
    different=[]
    for row in summaries:
        for field in METRICS:
            ref=float(archived[(row['case_id'],row['method'])][field])
            if abs(row[field]-ref)>1e-12:different.append(dict(case_id=row['case_id'],method=row['method'],field=field,local=row[field],reference=ref))
    if canonical and different:raise ValueError('Canonical source metrics differ')
    for name in ('run_metadata.json','VERIFICATION.json','per_trial.csv','by_target.csv','summary.csv','comparison.csv','worst_paths.csv'):
        hashes[name]=sha256(stage10/name)
    snapshot=dict(stage9=old,stage10_file_sha256=hashes,stage10_protocol_sha256=sha256(ROOT.parent/'stage10/PROTOCOL_LOCK.json'),
        decisions_checked=checked,metric_values_checked=values,archived_metric_differences=different,
        stage10_original_audit=audit,prediction_and_calibration_audits='verified reuse, not repeated')
    return snapshot,cases,summaries,rows


def check_aggregate(summaries,path):
    saved={(r['scenario'],r['language_pair'],r['method']):r for r in read_csv(path)}
    expected=aggregate(summaries)
    if len(saved)!=len(expected):raise ValueError('Wrong aggregate row count')
    for row in expected:
        other=saved[(row['scenario'],row['language_pair'],row['method'])]
        for field in METRICS:
            if abs(row[field]-float(other[field]))>1e-12:raise ValueError('Aggregate differs: '+field)


def cache_key(y,ledger,raw):
    return hashlib.sha256(np.asarray(y,dtype='i1').tobytes()+np.asarray(ledger,dtype='<i4').tobytes()+
                          np.asarray(raw,dtype='<i2').tobytes()).hexdigest()


def comparison_rows(cases,costs,data):
    comparisons=[]
    for scenario in SCENARIOS:
        for language in (*sorted(data),'overall'):
            selected=[c for c,_,_ in cases if c['scenario']==scenario and (language=='overall' or c['language_pair']==language)]
            languages=sorted({c['language_pair'] for c in selected})
            means=np.stack([np.mean([costs[c['case_id']] for c in selected if c['language_pair']==lang],axis=0)
                            for lang in languages]).mean(axis=0)
            for method,control in CONTRASTS:
                delta=means[method]-means[control]
                by_target=np.array([(costs[c['case_id']][method]-costs[c['case_id']][control]).mean() for c in selected])
                comparisons.append(dict(scenario=scenario,language_pair=language,method=METHODS[method],control=METHODS[control],
                    method_mean=float(means[method].mean()),control_mean=float(means[control].mean()),
                    paired_mean_difference=float(delta.mean()),percent_change=float(100*delta.mean()/means[control].mean()),
                    conditional_mcse=float(delta.std(ddof=1)/10),
                    largest_extra_queries=max(int((costs[c['case_id']][method]-costs[c['case_id']][control]).max()) for c in selected),
                    target_mean_wins=int((by_target< -1e-10).sum()),target_mean_ties=int((abs(by_target)<=1e-10).sum()),
                    target_mean_losses=int((by_target>1e-10).sum())))
    return comparisons
