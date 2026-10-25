"""Reuse matched archives; profile only the surviving exact paired control."""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[name]='1'
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def load(path):
    path=ROOT/path
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location(path.stem,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod

def read(path):return json.loads((ROOT/path).read_text())

def fixtures():
    original=read('experiments/joint_order_gate/results_reference/cases.json')
    records=[dict(tag=c['scenario']+'_archived',scenario=c['scenario'],scores=c['scores'],
                  order=c['stage22_order'],repeat=c['repeat']) for c in original if c['repeat']==0]
    import numpy as np
    for n in (64,128):
        rng=np.random.default_rng(731+n)
        scores=(rng.random((3,n))<np.array([.15,.5,.85])[:,None]).astype(int)
        records.append(dict(tag=f'independent_strong_scale_{n}',scenario='independent_strong',
                            scores=scores.tolist(),order=rng.permutation(n).tolist(),repeat=None))
    assert len(records)==7
    return records

def worker(config):
    import numpy as np
    import psutil
    controls=load('experiments/joint_order_controls/controls.py')
    from run_study import stage22,GRAPHS,SCENARIOS
    fixture=config['fixture']; method=config['method']; graph=config['graph']
    controls.paired_update.cache_clear();controls.null_histograms.cache_clear()
    inference=[]
    original_update=controls.paired_update
    def timed(*args):
        start=time.perf_counter()
        try:return original_update(*args)
        finally:inference.append(time.perf_counter()-start)
    # No replacement algorithm: only time the existing function at its boundary.
    controls.paired_update=timed
    scores=np.array(fixture['scores']);order=fixture['order']
    ready=psutil.Process().memory_info().rss
    start,cpu=time.perf_counter(),time.process_time()
    if method=='stage22':result=stage22(scores,GRAPHS[graph],np.array(order))
    else:result=controls.run_block(scores,SCENARIOS[fixture['scenario']][1],order,graph,
                                   'paired_exact_closure',keep_trace=False)
    wall,cpu=time.perf_counter()-start,time.process_time()-cpu
    peak=psutil.Process().memory_info().peak_wset
    if fixture['repeat'] is not None:
        archive=read('experiments/joint_order_gate/results_reference/cases.json' if method=='stage22'
                     else 'experiments/joint_order_controls/results_reference/cases.json')
        ref=next(c for c in archive if c['scenario']==fixture['scenario'] and c['repeat']==0)
        expected=ref['stops'][graph][method]
        assert all(result[k]==expected[k] for k in ('paid','charged','wrong','decisions'))
    return dict(config=config,wall_s=wall,cpu_s=cpu,cpu_core_percent=100*cpu/wall,
                peak_mib=peak/2**20,ready_mib=ready/2**20,
                inference_s=sum(inference),inference_calls=len(inference),
                paid=result['paid'],charged=result['charged'],wrong=result['wrong'],
                decisions=result['decisions'],archive_parity=fixture['repeat'] is not None,
                unit_fallbacks=result.get('unit_fallbacks'),
                failed_status=result.get('solver_failed_status'))

def archive_comparison(out):
    import numpy as np
    old=read('experiments/joint_order_gate/results_reference/cases.json')
    new=read('experiments/joint_order_controls/results_reference/cases.json')
    assert len(old)==len(new)==100
    assert [(c['scenario'],c['repeat']) for c in old]==[(c['scenario'],c['repeat']) for c in new]
    summary=read('experiments/joint_order_controls/results_reference/summary.json')
    rows=[];paired=[]
    rng=np.random.default_rng(20261025)
    for scenario in dict.fromkeys(c['scenario'] for c in old):
        for graph in ('star','triangle'):
            cases=[(a,b) for a,b in zip(old,new) if a['scenario']==scenario]
            costs={}
            for method in ('stage22','joint_order','rebalanced_pair_order','paired_exact_closure','paired_exact_bonferroni'):
                stops=[(a if method in ('stage22','joint_order') else b)['stops'][graph][method] for a,b in cases]
                costs[method]=np.array([s['charged'] for s in stops])
                mean=float(costs[method].mean())
                expected=summary[scenario][graph].get('stage22_mean' if method=='stage22' else 'joint_mean') if method in ('stage22','joint_order') else summary[scenario][graph][method]['mean_charged']
                assert abs(mean-expected)<1e-10
                rows.append(dict(scenario=scenario,graph=graph,method=method,mean_charged=mean,
                    mean_paid=float(np.mean([s['paid'] for s in stops])),wrong=sum(s['wrong'] for s in stops),cases=len(stops)))
            for candidate,control in [('joint_order','rebalanced_pair_order'),('joint_order','paired_exact_closure'),
                                      ('paired_exact_closure','stage22'),('paired_exact_closure','rebalanced_pair_order')]:
                a,b=costs[candidate],costs[control]
                ids=rng.integers(len(a),size=(10000,len(a)))
                ci=np.quantile(1-a[ids].mean(1)/b[ids].mean(1),[.025,.975])
                paired.append(dict(scenario=scenario,graph=graph,candidate=candidate,control=control,
                    saving=1-float(a.mean()/b.mean()),ci_low=float(ci[0]),ci_high=float(ci[1]),
                    wins=int((a<b).sum()),ties=int((a==b).sum()),losses=int((a>b).sum())))
    for name,data in [('matched_archive.csv',rows),('paired_archive.csv',paired)]:
        with (out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker');args=parser.parse_args()
    if args.worker:print(json.dumps(worker(json.loads(args.worker))));return
    out=HERE/'results';out.mkdir(exist_ok=True)
    configs=[dict(fixture=f,graph=g,method=m) for f in fixtures()
             for g in ('star','triangle') for m in ('stage22','paired_exact_closure')]
    paths=['experiments/method_screening/PROTOCOL.md','experiments/method_screening/screen.py',
      'experiments/joint_order_controls/controls.py','experiments/joint_order_controls/VALIDITY.md',
      'experiments/joint_order_gate/joint_order.py','experiments/joint_order_gate/run_study.py',
      'experiments/stage17/continuous_engine.py',
      'experiments/joint_order_gate/results_reference/cases.json',
      'experiments/joint_order_controls/results_reference/cases.json',
      'experiments/joint_order_controls/results_reference/summary.json',
      'experiments/exact_sequential_probe/results_reference.json',
      'experiments/exact_sequential_probe/audit_reference.json',
      'experiments/adaptive_q_gate/audit_reference.json',
      'experiments/computational_profile/results/summary.json']
    manifest=dict(base='a9c2f50',source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                  configs=configs,repeats=3,python=sys.version,started=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    archive_comparison(out)
    with (out/'timings.jsonl').open('w') as handle:
        for i,config in enumerate(configs):
            for rep in range(3):
                try:
                    child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',json.dumps(config)],
                        capture_output=True,text=True,timeout=90,cwd=ROOT)
                    row=json.loads(child.stdout) if child.returncode==0 else dict(config=config,error=child.stderr)
                except subprocess.TimeoutExpired:row=dict(config=config,timeout_s=90)
                row.update(case=i,repeat=rep);handle.write(json.dumps(row)+'\n');handle.flush()
                print(i,rep,config['fixture']['tag'],config['graph'],config['method'],row.get('wall_s'),row.get('error','')[:100],flush=True)

if __name__=='__main__':main()
