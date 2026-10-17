from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from fractions import Fraction
import hashlib,json,platform,time
from pathlib import Path
import numpy as np
from stage9_common import verify_protocol,build_cases,records,aggregate,write_csv
from stage9_engine import evaluate,METHODS
from certify_stage9 import load_certificate
from wmt_experiment import QueryOracle


def run_case(job):
    case,h,y,repeats,output,certdir=job
    certificate,raw,cal=load_certificate(certdir,case["n"],verify_runtime=False)
    alpha=Fraction(certificate["prediction_error_numerator"],certificate["prediction_error_denominator"])
    trace=evaluate(h,QueryOracle(y,repeats),repeats,case["raw_seed"],raw,cal,alpha)
    np.savez_compressed(Path(output)/"curves"/(case["case_id"]+".npz"),**trace)
    targets,trials=records(case,y,trace)
    costs={r["method"]:r["mean_queries"] for r in targets}
    digest=hashlib.sha256(np.asarray(trace["selected"],dtype="<i4").tobytes()).hexdigest()
    return case,targets,trials,costs,digest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--certificates",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--repeats",type=int,default=100)
    p.add_argument("--workers",type=int,default=2)
    args=p.parse_args()
    if min(args.repeats,args.workers)<1:p.error("Positive repeats and workers required")
    lock,datasets=verify_protocol()
    out=Path(args.output).resolve();certdir=Path(args.certificates).resolve()
    if (out/"run_metadata.json").exists():p.error("Use a new output directory")
    certificates={}
    for n in sorted({v[0].shape[1] for v in datasets.values()}):
        certificate,_,_=load_certificate(certdir,n,verify_runtime=True)
        certificates[str(n)]=certificate
    cases=build_cases(datasets)
    (out/"curves").mkdir(parents=True,exist_ok=True)
    meta=dict(status="running",repeats=args.repeats,workers=args.workers,methods=METHODS,
              cases=[c for c,_,_ in cases],certificates=certificates,protocol_lock=lock,
              python=platform.python_version(),numpy=np.__version__)
    (out/"run_metadata.json").write_text(json.dumps(meta,indent=2))
    targets=[];trials=[];hashes={}
    jobs=[(c,h,y,args.repeats,str(out),str(certdir)) for c,h,y in cases]
    start=time.perf_counter()
    def collect(result):
        c,ts,rs,cost,digest=result
        targets.extend(ts);trials.extend(rs);hashes[c["case_id"]]=digest
        print(f"{c['scenario']:17s} {c['language_pair']} {c['target_system']:28s} "
              f"raw95={cost['raw95']:6.1f} calibrated={cost['calibrated_raw95']:6.1f} "
              f"zero={cost['budget_zero95']:6.1f} prediction={cost['budget_prediction95']:6.1f}",flush=True)
    if args.workers==1:
        for job in jobs:collect(run_case(job))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for f in as_completed([pool.submit(run_case,job) for job in jobs]):collect(f.result())
    key=lambda r:(r["scenario"],r["language_pair"],r["target_system"],r["method"],r.get("repeat",-1))
    targets.sort(key=key);trials.sort(key=key)
    write_csv(out/"by_target.csv",targets);write_csv(out/"per_trial.csv",trials)
    write_csv(out/"summary.csv",aggregate(targets))
    meta.update(status="complete",completed_cases=len(cases),method_trajectories=len(trials),
                raw_stream_sha256=hashes,runtime_seconds=time.perf_counter()-start)
    (out/"run_metadata.json").write_text(json.dumps(meta,indent=2))
    print(f"Finished {len(cases)} cases and {len(trials)} trajectories in "
          f"{meta['runtime_seconds']:.1f}s. Results: {args.output}",flush=True)


if __name__=="__main__":main()
