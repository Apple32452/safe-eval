"""Locked synthetic study and preserved stronger controls."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path

import numpy as np
import scipy

from engine import (ALPHA,CELL_METHODS,ColumnModel,edges_for,finish,run_cells,run_paired)

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'joint_order_controls'))
from controls import rebalanced_update,run_block
from joint_order import PAIRS,ORDERS,decide,possible_orders,state_update
sys.path.insert(0,str(HERE.parent/'stage17'))
from continuous_engine import make_paths

SCENARIOS=('independent','monotone','opposed','one_hot','reversed','near_ties')
ALL_METHODS=CELL_METHODS+('paired_exact','stage22','paired_exact_closure','rebalanced_pair_order')


def seed_for(scenario,k,n,graph,repeat,purpose):
    text=f'20261026|peer_cell_scale|{scenario}|{k}|{n}|{graph}|{repeat}|{purpose}'
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],'little')


def distribution(scenario,k):
    patterns=np.array(list(__import__('itertools').product((0,1),repeat=k)),int)
    name='one_hot' if scenario=='reversed' else scenario
    if name in ('independent','near_ties'):
        marginal=np.full(k,.5) if name=='near_ties' else np.linspace(.2,.8,k)
        prob=np.prod(np.where(patterns,marginal,1-marginal),axis=1)
    else:
        structured=np.zeros(len(patterns))
        if name=='monotone':
            marginal=np.linspace(.2,.8,k)
            bounds=np.r_[0,marginal,1.]
            for low,high in zip(bounds[:-1],bounds[1:]):
                bits=((low+high)/2<marginal).astype(int)
                structured[np.all(patterns==bits,axis=1)]+=high-low
        elif name=='opposed':
            first=np.zeros(k,int); first[0]=1
            structured[np.all(patterns==first,axis=1)]=.2
            structured[np.all(patterns==1-first,axis=1)]=.8
        elif name=='one_hot':
            weights=np.array([1,3,6] if k==3 else [1,2,3,4,5],float); weights/=weights.sum()
            for v,w in enumerate(weights): structured[np.all(patterns==np.eye(k,dtype=int)[v],axis=1)]=w
        else: raise ValueError('Unknown design')
        prob=.9*structured+.1/len(patterns)
    return patterns,prob/prob.sum()


def inputs(spec,smoke=False):
    scenario,k,n,graph,repeat=spec
    if smoke:
        seed=seed_for(scenario,k,n,graph,repeat,'smoke')
        seeds={p:seed^offset for p,offset in zip(('history','target','acquisition','particle','order'),range(5))}
    else:
        seeds={p:seed_for(scenario,k,n,graph,repeat,p) for p in ('history','target','acquisition','particle','order')}
    patterns,prob=distribution(scenario,k)
    history=patterns[np.random.default_rng(seeds['history']).choice(len(prob),size=2048,p=prob)].T
    scores=patterns[np.random.default_rng(seeds['target']).choice(len(prob),size=n,p=prob)].T.copy()
    if scenario=='reversed': history=1-history
    if scenario=='near_ties' and repeat%2==0: scores[1]=scores[0]
    order=np.random.default_rng(seeds['order']).permutation(n)
    return scores,history,seeds,order


def stage22(scores,edges,order):
    paths=np.tile(order,(len(edges),1,1))
    events,_=make_paths(scores,np.asarray(edges,dtype=np.int16),paths,2*len(edges)/ALPHA)
    prefix=[int(np.flatnonzero(event!=2)[0])+1 for event in events[:,0]]
    decisions=np.array([events[i,0,count-1] for i,count in enumerate(prefix)])
    trace=[]; paid=0
    for step in range(max(prefix)):
        active=sorted({v for e,edge in enumerate(edges) if step<prefix[e] for v in edge})
        item=int(order[step]); paid+=len(active)
        trace.append({'item':item,'active':active,'values':[int(scores[v,item]) for v in active]})
    record=finish(scores,edges,decisions,paid,trace); record['edge_prefixes']=prefix
    return record


def legacy_rebalanced(scores,prior,edges,graph,seed):
    graph='star' if graph=='star' else 'triangle'; n=scores.shape[1]
    rng=np.random.default_rng(seed); s=np.zeros(3,int); m=np.full(3,n)
    unseen=[list(range(n)) for _ in range(3)]
    logs=np.zeros(13); excluded=np.zeros(13,bool); decisions=np.full(3,2,int)
    ids=[PAIRS.index(e) for e in edges]; trace=[]
    for t in range(scores.size):
        old=state_update(tuple(s),tuple(m),prior,n)
        fitted=rebalanced_update(tuple(s),tuple(m),prior,n,graph)
        v=int(rng.choice(3,p=old['q'])); item=unseen[v].pop(int(rng.integers(len(unseen[v]))))
        value=int(scores[v,item]); s[v]+=value; m[v]-=1
        logs+=np.log(fitted['factors'][:,2*v+value])
        excluded|=(logs>=np.log(1/ALPHA))|~possible_orders(s,m)
        decisions=decide(s,m,excluded,decisions)
        trace.append({'cell':v*n+item,'value':value,'decisions':decisions[ids].tolist()})
        if np.all(decisions[ids]!=2): return finish(scores,edges,decisions[ids],t+1,trace)
    raise AssertionError('Legacy control did not complete')


def grid():
    specs=[]
    for scenario in SCENARIOS:
        specs.extend((scenario,3,64,'star',r) for r in range(50 if scenario=='one_hot' else 10))
        specs.extend((scenario,3,64,'complete',r) for r in range(10))
        specs.extend((scenario,5,128,'star',r) for r in range(5))
    assert len(specs)==190
    return specs


def one_case(spec,smoke=False):
    started=time.perf_counter(); scenario,k,n,graph,repeat=spec
    scores,history,seeds,order=inputs(spec,smoke); model=ColumnModel(history)
    edges=edges_for(k,graph); methods={}; runtime={}
    for method in ALL_METHODS:
        if k!=3 and method in ALL_METHODS[-2:]: continue
        tick=time.perf_counter()
        if method in CELL_METHODS:
            result=run_cells(scores,model,edges,method,seeds['acquisition'],seeds['particle'])
        elif method=='paired_exact': result=run_paired(scores,model,edges,order)
        elif method=='stage22': result=stage22(scores,edges,order)
        elif method=='paired_exact_closure':
            result=run_block(scores,tuple(model.marginal),order,
                             'star' if graph=='star' else 'triangle',method)
        else: result=legacy_rebalanced(scores,tuple(model.marginal),edges,graph,seeds['acquisition'])
        runtime[method]=time.perf_counter()-tick; methods[method]=result
    return dict(spec=list(spec),smoke=smoke,scores=scores.tolist(),seeds=seeds,
                history_counts=((model.prob*(2048+.5*2**k))-.5).round().astype(int).tolist(),
                order=order.tolist(),methods=methods,runtime_seconds=runtime,
                elapsed_seconds=time.perf_counter()-started)


def summarize(cases):
    result={}; bootstrap_rng=np.random.default_rng(2026102601)
    for key in sorted({tuple(c['spec'][:4]) for c in cases}):
        subset=[c for c in cases if tuple(c['spec'][:4])==key]
        subset.sort(key=lambda c:c['spec'][4]); label='|'.join(map(str,key))
        methods=tuple(subset[0]['methods']); count=len(subset)
        primary=key==('one_hot',3,64,'star')
        indices=bootstrap_rng.integers(count,size=(20000,count))
        tail=.025/(len(methods)-1) if primary else .025
        costs={m:np.array([c['methods'][m]['charged'] for c in subset]) for m in methods}
        candidate=costs['peer_cell']; row={'cases':count,'primary':primary,'methods':{},'comparisons':{}}
        for method in methods:
            data=[c['methods'][method] for c in subset]
            row['methods'][method]={'mean_paid':float(np.mean([d['paid'] for d in data])),
                'mean_charged':float(costs[method].mean()),'wrong':sum(d['wrong'] for d in data),
                'mean_runtime_seconds':float(np.mean([c['runtime_seconds'][method] for c in subset]))}
            if method=='peer_cell': continue
            base=costs[method]
            boot=1-candidate[indices].mean(axis=1)/base[indices].mean(axis=1)
            row['comparisons'][method]={'relative_saving':float(1-candidate.mean()/base.mean()),
                'mean_labels_saved':float((base-candidate).mean()),
                'bootstrap_interval':np.quantile(boot,[tail,1-tail]).tolist(),
                'interval_tail':tail}
        result[label]=row
    primary=result.get('one_hot|3|64|star')
    result['primary_efficiency_gate']=bool(primary and primary['cases']==50 and
        all(c['bootstrap_interval'][0]>0 for c in primary['comparisons'].values()))
    result['case_count']=len(cases)
    result['trajectory_count']=sum(len(c['methods']) for c in cases)
    result['wrong_trajectories']=sum(r['wrong'] for c in cases for r in c['methods'].values())
    return result


def run(output,workers=2,smoke=False):
    if output.exists(): raise ValueError('Use a new output directory')
    output.mkdir(parents=True)
    specs=[('one_hot',3,8,'star',0)] if smoke else grid()
    cases=[]; started=time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(one_case,spec,smoke):spec for spec in specs}
        for future in as_completed(futures):
            case=future.result(); cases.append(case)
            with gzip.open(output/f"checkpoint_{specs.index(tuple(case['spec'])):03d}.json.gz",'wt') as f:
                json.dump(case,f,separators=(',',':'))
            print(f"Completed {len(cases)}/{len(specs)}: {case['spec']} ({case['elapsed_seconds']:.1f}s)",flush=True)
    cases.sort(key=lambda c:tuple(c['spec']))
    with gzip.open(output/'cases.json.gz','wt') as f: json.dump(cases,f,separators=(',',':'))
    summary=summarize(cases)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    metadata={'date':'2026-10-26','smoke':smoke,'cases':len(cases),'alpha':ALPHA,
        'seconds':time.perf_counter()-started,'numpy':np.__version__,'scipy':scipy.__version__,
        'protocol_sha256':hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')},
        'human_judgments':0,'WMT_data_used':False}
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'trajectories':summary['trajectory_count'],
                      'primary_efficiency_gate':summary['primary_efficiency_gate'],
                      'seconds':metadata['seconds']},indent=2),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args(); run(args.output,args.workers,args.smoke)
