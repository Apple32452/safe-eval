"""Supplement: CPU time for Stage 22's offline evidence, warmed process."""
import itertools
import json
from pathlib import Path
import time
from benchmark import load, matrix, digest
import numpy as np

mod=load('experiments/stage22/run_stage22.py')
rows=[]
for config in matrix():
    if config['kind']!='stage22' or config['method']!='star_pruned':continue
    s,n=config['s'],config['n']
    rng=np.random.default_rng(731)
    pairs=np.array(list(itertools.combinations(range(s),2)) if config['graph']=='complete'
                   else [(0,i) for i in range(1,s)],dtype=np.int16)
    scores=np.full((s,n),.5) if config['scenario']=='tie' else np.clip(
        np.linspace(.1,.9,s)[:,None]+rng.normal(0,.05,(s,n)),0,1)
    perm=np.broadcast_to(rng.permutation(n),(len(pairs),1,n)).copy()
    for repeat in range(3):
        start,cpu=time.perf_counter(),time.process_time()
        result=mod.make_paths(scores,pairs,perm,40*len(pairs))
        wall,cpu=time.perf_counter()-start,time.process_time()-cpu
        rows.append(dict(config=config,repeat=repeat,wall_s=wall,cpu_s=cpu,
                         cpu_core_percent=100*cpu/wall,output_digest=digest(result)))
out=Path(__file__).resolve().parent/'results'/'preprocessing_cpu.json'
out.write_text(json.dumps(rows,indent=2))
for config in matrix():
    group=[r for r in rows if r['config']==config]
    if group:
        assert len({r['output_digest'] for r in group})==1
        print(config,'wall',sum(r['wall_s'] for r in group)/3,
              'CPU',sum(r['cpu_s'] for r in group)/3)
