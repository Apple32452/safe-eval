from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from stage10_common import (verify_protocol,validate_source,integer_decisions,
                            check_trials,check_summary,summary_from_decision,read_csv,
                            write_csv,aggregate,sha256,ROOT,METHODS,CONTRASTS,SCENARIOS,METRICS,
                            verify_certificate_design)
from calibrate_stage10 import load_certificate,exact_risk,count_record,state_sha
from calibration_control import parent_gates,replay_control
from repair_reference import explicit_repaired_counts
from replay_stage9 import backward_failures,binomial_rows


def audit_fine(record,table,choose):
    n=record['n'];symmetric=True
    for t in range(n+1):
        for s in range(t+1):
            if table[t,s,0]!=n-table[t,t-s,1] or table[t,s,1]!=n-table[t,t-s,0]:
                symmetric=False;break
        if not symmetric:break
    risks=[];checked=0
    for k in range(n//2+1 if symmetric else n+1):
        failed=backward_failures(table,k,choose)
        live=choose[n][k]-failed
        if str(live)!=record['surviving_strings'][k]:raise ValueError('Fine backward count differs')
        if symmetric and str(live)!=record['surviving_strings'][n-k]:raise ValueError('Fine symmetry differs')
        risks.append(Fraction(failed,choose[n][k]));checked+=1
    if max(risks)!=exact_risk(record):raise ValueError('Fine worst risk differs')
    return checked


def run_analysis(directory,source,certdir):
    start=time.perf_counter();directory=Path(directory);source=Path(source);certdir=Path(certdir)
    lock,data=verify_protocol()
    meta=json.loads((directory/'run_metadata.json').read_text())
    if meta['status']!='complete' or meta['protocol_lock']!=lock or tuple(meta['methods'])!=METHODS:
        raise ValueError('Incomplete or changed Stage 10 run')
    snapshot,parent,cases,old_rows,_=validate_source(source,require_reference=meta['canonical_source'])
    if snapshot!=meta['source_manifest']:raise ValueError('Source traces changed')
    if [c for c,_,_ in cases]!=meta['cases'] or meta['repeats']!=100:raise ValueError('Wrong cases/repeats')
    gates={};risk_checks=0;repair_checks=0
    for n in sorted({c['n'] for c,_,_ in cases}):
        record,tables=load_certificate(certdir,n,verify_runtime=True)
        verify_certificate_design(record)
        for name,h in meta['certificate_sha256'][str(n)].items():
            if sha256(certdir/name)!=h:raise ValueError('Certificate file changed')
        choose=binomial_rows(n)
        cache={}
        def actual(h):
            h=float(h)
            if h not in cache:cache[h]=parent_gates(n,h)
            return cache[h]
        raw=actual(20)
        if state_sha(raw)!=record['raw_state_sha256']:raise ValueError('Actual parent raw gates differ')
        for name,key in (('fine','safe'),('unsafe','unsafe')):
            table=actual(record[key]['threshold'])
            if not np.array_equal(table,tables[name]):raise ValueError('Parent interval gate differs from certifier')
            risk_checks+=audit_fine(record[key],table,choose)
            print(f"Checked N={n} {key} risk {record[key]['risk_decimal']:.12f}",flush=True)
        for probe in record['repair_probes']:
            if probe['status']!='complete':continue
            table=actual(probe['threshold'])
            if state_sha(table)!=probe['state_sha256']:raise ValueError('Repaired probe gate changed')
            live=explicit_repaired_counts(table,raw)
            if [str(v) for v in live]!=probe['surviving_strings']:
                raise ValueError('Independent explicit repaired count differs')
            independent=count_record(n,probe['threshold'],table,live)
            if exact_risk(independent)!=exact_risk(probe):raise ValueError('Repaired worst risk differs')
            repair_checks+=1
            print(f"Checked N={n} repaired risk H={probe['threshold']:.9f}",flush=True)
        repair=actual(record['repair_threshold'])
        if not np.array_equal(repair,tables['repair']):raise ValueError('Repaired control table changed')
        gates[n]=(raw,actual(record['safe']['threshold']),repair)
    saved=read_csv(directory/'per_trial.csv')
    lookup={(r['case_id'],r['method'],int(r['repeat'])):r for r in saved}
    if len(lookup)!=70200 or len(saved)!=70200:raise ValueError('Wrong saved decision count')
    summaries=[];costs={};cover={};worst=[];checked=0;bounds=0;steps=0
    model_free_hashes={}
    for case,history,y in cases:
        n=case['n'];repeats=100
        with np.load(source/'curves'/(case['case_id']+'.npz')) as f:
            old=f['counts'];ledger=f['selected'];old_flags=f['repaired']
        with np.load(directory/'curves'/(case['case_id']+'.npz')) as f:
            fine=f['fine_counts'];ff=f['fine_repaired'];repair=f['repair_counts'];rf=f['repair_repaired']
        raw,ftable,rtable=gates[n]
        base,_=replay_control(y,ledger,raw,raw)
        if not np.array_equal(base,old[0]):raise ValueError('Preserved raw curve differs from parent replay')
        for curve,flags,table in ((fine,ff,ftable),(repair,rf,rtable)):
            reference,reference_flags=replay_control(y,ledger,raw,table)
            if not np.array_equal(curve,reference) or not np.array_equal(flags,reference_flags):
                raise ValueError('New curve/fallback differs from independent replay')
            nonempty=curve[1]>=curve[0]
            if np.any(nonempty&((curve[0]<base[0])|(curve[1]>base[1]))):
                raise ValueError('Ordinary raw95 containment failed')
            steps+=n*repeats
        curves=[*old,fine,repair]
        repairs=[np.zeros((n,repeats),dtype=bool),*old_flags,ff,rf]
        case_cost=[];case_cover=[]
        for method,curve,flags in zip(METHODS,curves,repairs):
            d=integer_decisions(curve,y,flags)
            checked+=check_trials(case,method,d,lookup)
            summaries.append(summary_from_decision(case,method,d))
            case_cost.append(d['stop_queries']);case_cover.append(d['simultaneous_coverage'])
        costs[case['case_id']]=np.stack(case_cost);cover[case['case_id']]=np.stack(case_cover)
        if np.any(costs[case['case_id']][4:]>costs[case['case_id']][0]):
            raise ValueError('New control stopped later than ordinary raw95')
        bounds+=2*repeats
        digest=hashlib.sha256(np.stack([fine,repair]).tobytes()+np.stack([ff,rf]).tobytes()).hexdigest()
        key=(case['language_pair'],case['target_system'])
        if key in model_free_hashes and model_free_hashes[key]!=digest:raise ValueError('History changed model-free curves')
        model_free_hashes[key]=digest
        for method,control in CONTRASTS:
            difference=case_cost[method]-case_cost[control];r=int(difference.argmax())
            worst.append(dict(scenario=case['scenario'],language_pair=case['language_pair'],
                target_system=case['target_system'],method=METHODS[method],control=METHODS[control],repeat=r,
                extra_queries=int(difference[r]),method_queries=int(case_cost[method][r]),
                control_queries=int(case_cost[control][r]),method_covered=int(case_cover[method][r]),
                control_covered=int(case_cover[control][r])))
        print(f"Audited {case['scenario']:17s} {case['language_pair']} {case['target_system']}",flush=True)
    values=check_summary(summaries,directory/'by_target.csv')
    old_lookup={(r['case_id'],r['method']):r for r in old_rows}
    preserved=0
    for row in summaries:
        if row['method'] not in METHODS[:4]:continue
        old=old_lookup[(row['case_id'],row['method'])]
        for field in METRICS:
            if abs(old[field]-row[field])>1e-12:raise ValueError('Preserved source metric changed')
            preserved+=1
    aggregates=aggregate(summaries)
    saved_aggregate={(r['scenario'],r['language_pair'],r['method']):r for r in read_csv(directory/'summary.csv')}
    if len(saved_aggregate)!=len(aggregates):raise ValueError('Wrong aggregate table size')
    for row in aggregates:
        saved_row=saved_aggregate[(row['scenario'],row['language_pair'],row['method'])]
        for field in METRICS:
            if abs(row[field]-float(saved_row[field]))>1e-12:raise ValueError('Aggregate differs')
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
                    target_mean_wins=int((by_target< -1e-10).sum()),target_mean_ties=int((np.abs(by_target)<=1e-10).sum()),
                    target_mean_losses=int((by_target>1e-10).sum())))
    write_csv(directory/'comparison.csv',comparisons)
    worst.sort(key=lambda r:-r['extra_queries']);write_csv(directory/'worst_paths.csv',worst)
    result=dict(all_checks_passed=True,saved_decisions_checked=checked,
                source_saved_decisions_reconstructed=snapshot['decisions_checked'],
                stage9_metric_values_preserved=preserved,target_metric_values_checked=values,
                backward_fine_risk_counts_checked=risk_checks,
                repaired_risk_certificates_independently_checked=repair_checks,
                raw95_stopping_bounds_checked=bounds,new_control_query_replay_steps=steps,
                canonical_stage9_source=meta['canonical_source'],
                reused_stage9_capital_audit=snapshot['original_capital_audit'],
                prediction_capital_replayed_again=False,runtime_seconds=time.perf_counter()-start)
    (directory/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    p.add_argument('--stage9-input',required=True);p.add_argument('--certificates',required=True)
    args=p.parse_args();run_analysis(args.input,args.stage9_input,args.certificates)


if __name__=='__main__':main()
