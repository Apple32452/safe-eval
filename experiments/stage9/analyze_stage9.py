from __future__ import annotations
import argparse,csv,hashlib,json,math,time
from fractions import Fraction
from pathlib import Path
import numpy as np
from stage9_common import verify_protocol,build_cases,write_csv,ROOT
from stage9_engine import METHODS
from certify_stage9 import load_certificate
from replay_stage9 import replay,audit_certificate


def read_csv(path):
    with Path(path).open(newline="") as f:return list(csv.DictReader(f))


def run_analysis(directory,certdir):
    start=time.perf_counter()
    directory=Path(directory);certdir=Path(certdir)
    lock,datasets=verify_protocol()
    meta=json.loads((directory/"run_metadata.json").read_text())
    if meta["status"]!="complete" or meta["protocol_lock"]!=lock:
        raise ValueError("Incomplete run or changed protocol")
    certificates={};risk_checks=0
    for n in sorted({v[0].shape[1] for v in datasets.values()}):
        record,raw,cal=load_certificate(certdir,n)
        if record!=meta["certificates"][str(n)]:raise ValueError("Certificate changed")
        risk_checks+=audit_certificate(record,raw,cal)
        certificates[n]=(record,cal)
    saved=read_csv(directory/"per_trial.csv")
    lookup={(r["case_id"],r["method"],int(r["repeat"])):r for r in saved}
    if len(lookup)!=len(saved):raise ValueError("Duplicate saved decision")
    stage8meta=json.loads((ROOT.parent/"stage8/results_reference/run_metadata.json").read_text())
    stage8rows=read_csv(ROOT.parent/"stage8/results_reference/by_target.csv")
    stage8raw={r["case_id"]:r for r in stage8rows if r["method"]=="published_ppr95"}
    cases=build_cases(datasets)
    cost={};cover={};decisions_checked=0;stream_replay_steps=0;containment=0
    raw_metric_checks=0
    summaries=[];worst=[]
    for case,h,y in cases:
        n=case["n"];repeats=meta["repeats"];k=int(y.sum())
        with np.load(directory/"curves"/(case["case_id"]+".npz")) as f:
            trace={key:f[key] for key in f.files}
        if trace["counts"].shape!=(4,2,n,repeats):raise ValueError("Wrong curve dimensions")
        record,cal=certificates[n]
        alpha=Fraction(record["prediction_error_numerator"],record["prediction_error_denominator"])
        stream_replay_steps+=replay(case,h,y,trace,cal,alpha)
        digest=hashlib.sha256(np.asarray(trace["selected"],dtype="<i4").tobytes()).hexdigest()
        if digest!=meta["raw_stream_sha256"][case["case_id"]]:raise ValueError("Stream hash differs")
        if repeats==100 and digest!=stage8meta["raw_stream_sha256"][case["case_id"]]:
            raise ValueError("Parent query stream differs")
        c=trace["counts"]
        precise=(c[:,1]>=c[:,0])&(10*(c[:,1]-c[:,0])<=n)
        if not precise.any(axis=1).all():raise ValueError("Missing valid precision stop")
        stops=precise.argmax(axis=1)+1
        if np.any(stops[1:]>stops[0]):raise ValueError("Raw95 cost guarantee failed")
        containment+=3*repeats
        allcover=((c[:,0]<=k)&(c[:,1]>=k)).all(axis=1)
        if not np.all(c[:,:,-1]==k):raise ValueError("Final mean not exact")
        idx=np.arange(repeats)
        for j,method in enumerate(METHODS):
            lo=c[j,0,stops[j]-1,idx];hi=c[j,1,stops[j]-1,idx]
            error=np.abs((lo+hi-2*k)/(2*n))
            flags=np.zeros(repeats,dtype=int) if j==0 else (trace["repaired"][j-1]&(np.arange(n)[:,None]<stops[j])).any(axis=0).astype(int)
            empty=(c[j,0]>c[j,1]).any(axis=0).astype(int)
            for r in range(repeats):
                saved_row=lookup[(case["case_id"],method,r)]
                expected=dict(stop_queries=int(stops[j,r]),stop_lower=float(lo[r]/n),stop_upper=float(hi[r]/n),
                              simultaneous_coverage=int(allcover[j,r]),empty_ever=int(empty[r]),
                              stopped_absolute_error=float(error[r]),repair_before_stop=int(flags[r]))
                for key,value in expected.items():
                    if not math.isclose(float(saved_row[key]),value,rel_tol=0,abs_tol=1e-12):
                        raise ValueError("Saved decision differs: "+key)
                decisions_checked+=1
            row=dict(case_id=case["case_id"],scenario=case["scenario"],language_pair=case["language_pair"],
                     target_system=case["target_system"],method=method,n=n,
                     mean_queries=float(stops[j].mean()),simultaneous_coverage=float(allcover[j].mean()),
                     empty_ever_rate=float(empty.mean()),repair_before_stop_rate=float(flags.mean()),
                     stopped_error_over_epsilon_rate=float((error>.05+1e-12).mean()))
            summaries.append(row)
            if j==0 and repeats==100:
                for field in ("mean_queries","simultaneous_coverage","empty_ever_rate","repair_before_stop_rate","stopped_error_over_epsilon_rate"):
                    if abs(row[field]-float(stage8raw[case["case_id"]][field]))>1e-12:
                        raise ValueError("Stage 8 raw metric differs")
                    raw_metric_checks+=1
        cost[case["case_id"]]=stops
        cover[case["case_id"]]=allcover
        for j in range(1,4):
            for baseline in (0,1,2):
                if j==baseline:continue
                diff=stops[j]-stops[baseline];r=int(diff.argmax())
                worst.append(dict(scenario=case["scenario"],language_pair=case["language_pair"],
                    target_system=case["target_system"],method=METHODS[j],control=METHODS[baseline],
                    repeat=r,extra_queries=int(diff[r]),method_queries=int(stops[j,r]),
                    control_queries=int(stops[baseline,r]),method_covered=int(allcover[j,r]),
                    control_covered=int(allcover[baseline,r])))
        print(f"Audited {case['scenario']:17s} {case['language_pair']} {case['target_system']}",flush=True)
    if decisions_checked!=len(saved):raise ValueError("Unexpected saved rows")
    for pair in sorted(datasets):
        targets=[c["target_system"] for c,_,_ in cases if c["language_pair"]==pair and c["scenario"]=="aligned"]
        for target in targets:
            ids=[c["case_id"] for c,_,_ in cases if c["language_pair"]==pair and c["target_system"]==target]
            if any(not np.array_equal(cost[ids[0]][:3],cost[x][:3]) for x in ids[1:]):
                raise ValueError("Model-free controls changed across histories")
    # Verify target and aggregate files against decisions reconstructed above.
    by={(r["case_id"],r["method"]):r for r in read_csv(directory/"by_target.csv")}
    fields=("mean_queries","simultaneous_coverage","empty_ever_rate","repair_before_stop_rate","stopped_error_over_epsilon_rate")
    for row in summaries:
        for field in fields:
            if abs(row[field]-float(by[row["case_id"],row["method"]][field]))>1e-12:
                raise ValueError("Target summary differs")
    group_saved={(r["scenario"],r["language_pair"],r["method"]):r for r in read_csv(directory/"summary.csv")}
    for key,item in group_saved.items():
        rows=[r for r in summaries if (r["scenario"],r["language_pair"],r["method"])==key]
        for field in fields:
            if abs(float(item[field])-np.mean([r[field] for r in rows]))>1e-12:raise ValueError("Aggregate differs")
    comparisons=[]
    for scenario in ("aligned","permuted_history","reversed_history"):
        for pair in [*sorted(datasets),"overall"]:
            selected=[c for c,_,_ in cases if c["scenario"]==scenario and (pair=="overall" or c["language_pair"]==pair)]
            languages=sorted({c["language_pair"] for c in selected})
            means=np.stack([np.mean([cost[c["case_id"]] for c in selected if c["language_pair"]==lang],axis=0) for lang in languages]).mean(axis=0)
            for method,control in ((3,0),(3,1),(3,2),(2,0),(1,0)):
                delta=means[method]-means[control]
                comparisons.append(dict(scenario=scenario,language_pair=pair,method=METHODS[method],control=METHODS[control],
                    method_mean=float(means[method].mean()),control_mean=float(means[control].mean()),
                    paired_mean_difference=float(delta.mean()),
                    percent_change=float(100*delta.mean()/means[control].mean()),
                    conditional_mcse=float(delta.std(ddof=1)/np.sqrt(len(delta))) if len(delta)>1 else float("nan"),
                    largest_extra_queries=max(int((cost[c["case_id"]][method]-cost[c["case_id"]][control]).max()) for c in selected)))
    write_csv(directory/"comparison.csv",comparisons)
    worst.sort(key=lambda r:-r["extra_queries"])
    write_csv(directory/"worst_paths.csv",worst)
    result=dict(all_checks_passed=True,saved_decisions_checked=decisions_checked,
                raw95_stopping_bounds_checked=containment,query_and_capital_replay_steps=stream_replay_steps,
                exact_backward_risk_counts_checked=risk_checks,stage8_raw_metric_values_checked=raw_metric_checks,
                largest_extra_vs_raw95=max(r["largest_extra_queries"] for r in comparisons if r["control"]=="raw95"),
                runtime_seconds=time.perf_counter()-start)
    (directory/"VERIFICATION.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--certificates",required=True)
    args=p.parse_args();run_analysis(args.input,args.certificates)


if __name__=="__main__":main()
