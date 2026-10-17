from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import numpy as np
from boost_reference import replay
from stage11_common import (ROOT,METHODS,CONTRASTS,METRICS,verify_protocol,validate_sources,
    source_curves,cache_key,read_csv,integer_decisions,check_trials,check_summary,
    summary_from_decision,check_aggregate,write_csv,comparison_rows,sha256)


def run_analysis(directory,stage9,stage10):
    start=time.perf_counter();directory=Path(directory);lock,data=verify_protocol()
    meta=json.loads((directory/'run_metadata.json').read_text())
    if (meta['status']!='complete' or meta['protocol_lock']!=lock or tuple(meta['methods'])!=METHODS
        or meta['repeats']!=100 or meta['wealth_grid']!=2**39 or meta['rejection_wealth']!=20*2**39):
        raise ValueError('Incomplete or changed Stage 11 run')
    snapshot,cases,source_targets,_=validate_sources(stage9,stage10,canonical=meta['canonical_source'])
    if snapshot!=meta['source_manifest'] or meta['cases']!=[c for c,_,_ in cases]:raise ValueError('Source changed')
    if meta['canonical_source'] and snapshot!=json.loads((ROOT/'STAGE10_TRACE_MANIFEST.json').read_text()):
        raise ValueError('Canonical source fingerprints differ')
    rows=read_csv(directory/'per_trial.csv');lookup={(r['case_id'],r['method'],int(r['repeat'])):r for r in rows}
    if len(rows)!=93600 or len(lookup)!=93600:raise ValueError('Wrong saved decision count')
    summaries=[];costs={};coverage={};diagnostics=[];worst=[];cache={}
    checked=bounds=query_steps=distinct_steps=candidate_steps=interval_differences=0
    for case,_,y in cases:
        n=case['n'];curves,flags,ledger=source_curves(stage9,stage10,case)
        name=case['case_id']+'.npz'
        if sha256(directory/'curves'/name)!=meta['curve_sha256'][name]:raise ValueError('Saved trace hash changed')
        with np.load(directory/'curves'/name) as f:new={k:f[k] for k in f.files}
        key=cache_key(y,ledger,curves[0])
        if key not in cache:
            cache[key]=replay(y,ledger,curves[0]);distinct_steps+=2*n*100
            candidate_steps+=int(np.minimum(cache[key]['rejection_time'],n).astype(np.int64).sum())
        ref=cache[key]
        if set(new)!=set(ref):raise ValueError('Wrong saved arrays')
        for field in ref:
            if not np.array_equal(new[field],ref[field]):raise ValueError('Independent replay differs: '+field)
        if np.any(new['rejection_time'][1]>new['rejection_time'][0]):raise ValueError('Boosted candidate rejection was later')
        grid,boost=new['counts'];gn=grid[1]>=grid[0];bn=boost[1]>=boost[0]
        if np.any(bn&((~gn)|(boost[0]<grid[0])|(boost[1]>grid[1]))):raise ValueError('Matched hull containment failed')
        all_curves=[*curves,*new['counts']];all_flags=[*flags,*new['repaired']]
        case_cost=[];case_cover=[]
        for method,curve,repair in zip(METHODS,all_curves,all_flags):
            d=integer_decisions(curve,y,repair);checked+=check_trials(case,method,d,lookup)
            summaries.append(summary_from_decision(case,method,d))
            case_cost.append(d['stop_queries']);case_cover.append(d['simultaneous_coverage'])
        if np.any(case_cost[7]>case_cost[6]):raise ValueError('Matched precision stopping bound failed')
        bounds+=100;query_steps+=2*n*100
        costs[case['case_id']]=np.stack(case_cost);coverage[case['case_id']]=np.stack(case_cover)
        different=new['counts'][0]!=curves[0];interval_differences+=int(different.sum())
        for j,method in enumerate(METHODS[6:]):
            diagnostics.append(dict(case_id=case['case_id'],scenario=case['scenario'],language_pair=case['language_pair'],
                target_system=case['target_system'],method=method,
                largest_hole_count=int(new['holes'][j].max()),paths_with_holes=int((new['holes'][j]>0).any(axis=0).sum()),
                hole_timepoints=int((new['holes'][j]>0).sum()),
                underlying_candidate_set_empty_paths=int((new['rejection_time'][j]<=n).all(axis=0).sum()),
                grid_interval_entries_different_from_raw95=int(different.sum()) if j==0 else 0,
                grid_paths_different_from_raw95=int(different.any(axis=(0,1)).sum()) if j==0 else 0,
                grid_stop_paths_later_than_raw95=int((case_cost[6]>case_cost[0]).sum()) if j==0 else 0,
                grid_stop_paths_earlier_than_raw95=int((case_cost[6]<case_cost[0]).sum()) if j==0 else 0))
        for m,c in CONTRASTS:
            diff=case_cost[m]-case_cost[c];r=int(diff.argmax())
            worst.append(dict(scenario=case['scenario'],language_pair=case['language_pair'],target_system=case['target_system'],
                method=METHODS[m],control=METHODS[c],repeat=r,extra_queries=int(diff[r]),
                method_queries=int(case_cost[m][r]),control_queries=int(case_cost[c][r]),
                method_covered=int(case_cover[m][r]),control_covered=int(case_cover[c][r])))
        print('Audited',case['scenario'],case['language_pair'],case['target_system'],flush=True)
    values=check_summary(summaries,directory/'by_target.csv');check_aggregate(summaries,directory/'summary.csv')
    source={(r['case_id'],r['method']):r for r in source_targets};preserved=0
    for row in summaries:
        if row['method'] not in METHODS[:6]:continue
        old=source[(row['case_id'],row['method'])]
        for field in METRICS:
            if abs(old[field]-row[field])>1e-12:raise ValueError('Preserved metric changed')
            preserved+=1
    write_csv(directory/'comparison.csv',comparison_rows(cases,costs,data))
    write_csv(directory/'diagnostics.csv',diagnostics)
    write_csv(directory/'worst_paths.csv',sorted(worst,key=lambda r:-r['extra_queries']))
    result=dict(all_checks_passed=True,saved_decisions_checked=checked,source_saved_decisions_reconstructed=snapshot['decisions_checked'],
        source_metric_values_preserved=preserved,target_metric_values_checked=values,
        matched_stopping_bounds_checked=bounds,new_control_query_steps_checked=query_steps,
        distinct_query_replay_steps=distinct_steps,distinct_candidate_wealth_updates=candidate_steps,
        distinct_model_free_ledgers=len(cache),grid_interval_entries_different_from_raw95=interval_differences,
        canonical_source=meta['canonical_source'],reused_stage10_audit=snapshot['stage10_original_audit'],
        prediction_capital_replayed_again=False,calibration_audits_repeated=False,runtime_seconds=time.perf_counter()-start)
    (directory/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    p.add_argument('--stage9-input',required=True);p.add_argument('--stage10-input',required=True)
    args=p.parse_args();run_analysis(args.input,args.stage9_input,args.stage10_input)


if __name__=='__main__':main()
