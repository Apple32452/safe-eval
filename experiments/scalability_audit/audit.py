import ast, contextlib, hashlib, inspect, itertools, json, os
from pathlib import Path
import subprocess,sys,time
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[key]='1'
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/computational_profile'))
from benchmark import load,instrument,Phases

def matrix():
    rows=[]
    for s,n in [(32,64),(100,64),(200,64),(400,64),(100,256),(200,256),(400,256),(100,1024),(200,1024)]:
        for graph in ('star','complete'):
            rows.append(dict(s=s,n=n,graph=graph,scenario='separated'))
    rows += [dict(s=100,n=256,graph='ring',scenario='separated'),
             dict(s=200,n=256,graph='complete',scenario='tie')]
    return rows

def save(path,row):path.write_text(json.dumps(row))

def worker(config,rep,path):
    import numpy as np,psutil
    mod=load('experiments/stage22/run_stage22.py');engine=sys.modules['continuous_engine']
    s,n=config['s'],config['n'];rng=np.random.default_rng(731)
    edges=list(itertools.combinations(range(s),2)) if config['graph']=='complete' else [(0,i) for i in range(1,s)] if config['graph']=='star' else sorted({tuple(sorted((i,(i+1)%s))) for i in range(s)})
    pairs=np.array(edges,dtype=np.int16);p=len(pairs)
    scores=np.full((s,n),.5) if config['scenario']=='tie' else np.clip(np.linspace(.05,.95,s)[:,None]+rng.uniform(-.02,.02,(s,n)),0,1)
    permutation=np.broadcast_to(rng.permutation(n),(p,n)).copy().astype(np.int32)
    priority=rng.permutation(s*n).reshape(s,n)
    start,cpu=time.perf_counter(),time.process_time()
    events,evidence=engine.make_paths(scores,pairs,permutation[:,None,:],40*p)
    plain=time.perf_counter()-start;cpu=time.process_time()-cpu
    row=dict(config=config,repeat=rep,pairs=p,evidence_wall_s=plain,evidence_cpu_s=cpu,
             peak_plain_mib=psutil.Process().memory_info().peak_wset/2**20)
    save(path,row)
    phases=Phases()
    clone=instrument(engine,'directional_paths',[
      ('cs_update','remaining_before=n-t','log_mixture=peak+np.log(np.mean(np.exp(log_wealth-peak[...,None]),axis=-1))'),
      ('stop_check','forward=log_mixture[0]>=log_threshold','events[:,:,t]=np.sign(observed).astype(np.int8)')],phases)
    old=engine.directional_paths;engine.directional_paths=clone
    start=time.perf_counter()
    e2,v2=engine.make_paths(scores,pairs,permutation[:,None,:],40*p)
    row['instrumented_evidence_s']=time.perf_counter()-start;engine.directional_paths=old
    assert np.array_equal(events,e2) and np.array_equal(evidence,v2)
    row['parity']=True;row['phases']={k:dict(total_s=sum(v),calls=len(v),p50_s=float(np.median(v)),p95_s=float(np.quantile(v,.95))) for k,v in phases.values.items()}
    row['peak_attribution_mib']=psutil.Process().memory_info().peak_wset/2**20
    del e2,v2,evidence
    row['phase']='evidence_complete';save(path,row)
    if rep==0:
        # Time original global stop predicates, including the comparison itself.
        def check(thunk):
            start=time.perf_counter();value=thunk();stop_times.append(time.perf_counter()-start);return value
        tree=ast.parse(inspect.getsource(mod.simulate_graph));stop_times=[];close_times=[]
        class StopWrap(ast.NodeTransformer):
            def visit_Call(self,node):
                self.generic_visit(node)
                if ast.unparse(node)=='np.any(decision == 2)':
                    return ast.copy_location(ast.Call(ast.Name('_check',ast.Load()),[ast.Lambda(ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),node)],[]),node)
                return node
        original_close=mod.close_free
        def close(*args):
            start=time.perf_counter()
            try:return original_close(*args)
            finally:close_times.append(time.perf_counter()-start)
        namespace=dict(mod.__dict__,_check=check,close_free=close)
        exec(compile(ast.fix_missing_locations(StopWrap().visit(tree)),'<stop-check attribution>','exec'),namespace)
        row['phase']='replay_running';save(path,row)
        start=time.perf_counter();result=namespace['simulate_graph'](scores,pairs,permutation,events[:,0,:],priority,'star_pruned')
        row.update(replay_instrumented_s=time.perf_counter()-start,replay_labels=result['completion_cost'],
            global_stop_s=sum(stop_times),global_stop_calls=len(stop_times),availability_s=sum(close_times),
            availability_calls=len(close_times),replay_decisions_sha256=hashlib.sha256(result['decision'].tobytes()).hexdigest())
        # On the smallest fixture, check full replay parity with the original.
        if s==32:
            result2=mod.simulate_graph(scores,pairs,permutation,events[:,0,:],priority,'star_pruned')
            assert result['acquired']==result2['acquired'] and np.array_equal(result['decision'],result2['decision'])
            row['replay_parity']=True
    row['phase']='complete';row['peak_process_mib']=psutil.Process().memory_info().peak_wset/2**20;save(path,row)

def main():
    if len(sys.argv)>1:
        worker(json.loads(sys.argv[1]),int(sys.argv[2]),Path(sys.argv[3]));return
    import psutil,platform
    out=HERE/'results';out.mkdir(exist_ok=True)
    sources=['experiments/scalability_audit/audit.py','experiments/scalability_audit/PROTOCOL.md',
      'experiments/computational_profile/benchmark.py','experiments/stage17/continuous_engine.py',
      'experiments/stage17/run_stage17.py','experiments/stage22/run_stage22.py']
    manifest=dict(matrix=matrix(),repeats=3,base='5d991e7',platform=platform.platform(),python=sys.version,
      cpus=psutil.cpu_count(),memory_bytes=psutil.virtual_memory().total,
      numpy=__import__('numpy').__version__,
      hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
      exclusion=dict(s=400,n=1024,graph='complete',estimated_bytes=48*79800*1024,limit_bytes=1.5*2**30))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    with (out/'raw.jsonl').open('w') as handle:
      for case,config in enumerate(matrix()):
        for rep in range(3):
            path=out/f'case_{case}_{rep}.json';err=out/'worker_stderr.log'
            with err.open('a') as stderr:
                child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),json.dumps(config),str(rep),str(path.resolve())],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=stderr)
                start=time.perf_counter();replay_start=None;reason=None
                while child.poll() is None:
                    time.sleep(.2)
                    if path.exists():
                        try:partial=json.loads(path.read_text())
                        except (json.JSONDecodeError,PermissionError):continue
                        if partial.get('phase')=='replay_running' and replay_start is None:replay_start=time.perf_counter()
                    if replay_start and time.perf_counter()-replay_start>45:reason='replay_timeout_45s'
                    elif time.perf_counter()-start>180:reason='worker_timeout_180s'
                    if reason:child.kill();child.wait();break
            row=json.loads(path.read_text()) if path.exists() else dict(config=config,repeat=rep)
            if reason:row['censored']=reason
            elif child.returncode:row['error_exit']=child.returncode
            row['case']=case;handle.write(json.dumps(row)+'\n');handle.flush()
            print(case,rep,config,'evidence',row.get('evidence_wall_s'),'replay',row.get('replay_instrumented_s'),row.get('censored',row.get('error_exit','')),flush=True)

if __name__=='__main__':main()
