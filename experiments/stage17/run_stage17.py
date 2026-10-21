"""Run Stage 17 continuous-score shared-label development experiment."""
from __future__ import annotations

import argparse,csv,hashlib,json,sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage15'))
sys.path.insert(0,str(HERE.parent/'stage14'))
from frontier_experiment import label_priority
from shared_pilot import FRACTIONS,seed,simulate
from continuous_engine import make_paths
from prepare_scores import load_prepared

MASTER=20261024
METHODS=('uniform_labels','round_robin','focus_random','evidence_first',
         'frontier_count','frontier_evidence')


def verify_lock():
    lock=json.loads((HERE/'IMPLEMENTATION_LOCK.json').read_text())
    repository=HERE.parent.parent
    for relative,expected in lock['sha256'].items():
        if hashlib.sha256((repository/relative).read_bytes()).hexdigest()!=expected:
            raise ValueError('Locked source changed: '+relative)
    return lock


def permutations(names,n,language,repeats,master=MASTER):
    pairs=np.asarray(list(combinations(range(len(names)),2)),dtype=np.int16)
    paths=np.empty((len(pairs),repeats,n),dtype=np.int32)
    for p,(a,b) in enumerate(pairs):
        for repeat in range(repeats):
            paths[p,repeat]=np.random.default_rng(
                seed(master,language,str(names[a]),str(names[b]),repeat)).permutation(n)
    return pairs,paths


def snapshot(scores,pairs,decision,cursor,labels,budget):
    a,b=pairs.T
    truth=np.sign(scores[a].sum(axis=1)-scores[b].sum(axis=1))
    correct=int(np.sum((decision!=2)&(decision==truth)))
    wrong=int(np.sum((decision!=2)&(decision!=truth)))
    return dict(budget=budget,labels=labels,correct=correct,wrong=wrong,
                unresolved=len(pairs)-correct-wrong,reached_prefix=int(cursor.sum()),
                resolved_pairs=correct+wrong)


def close_free(seen,cursor,decision,pairs,permutation,events):
    a,b=pairs.T
    while True:
        active=np.flatnonzero(decision==2)
        if not len(active): return
        item=permutation[active,cursor[active]]
        ready=active[seen[a[active],item]&seen[b[active],item]]
        if not len(ready): return
        cursor[ready]+=1
        result=events[ready,cursor[ready]-1]
        resolved=result!=2
        decision[ready[resolved]]=result[resolved]


def simulate_uniform(scores,pairs,permutation,events,priority,fractions=FRACTIONS):
    systems,items=scores.shape; pair_count=len(pairs)
    if priority.shape!=scores.shape or len(np.unique(priority))!=priority.size:
        raise ValueError('Unique label priorities required')
    ordered=[tuple(map(int,index)) for index in np.ndindex(scores.shape)]
    ordered.sort(key=lambda label:int(priority[label]))
    targets=tuple(int(np.floor(f*systems*items)) for f in fractions)
    seen=np.zeros_like(scores,dtype=bool); cursor=np.zeros(pair_count,dtype=np.int32)
    decision=np.full(pair_count,2,dtype=np.int8); acquired=[]; position=0; snapshots=[]
    close_free(seen,cursor,decision,pairs,permutation,events)
    for budget in targets:
        while len(acquired)<budget and np.any(decision==2):
            while position<len(ordered) and seen[ordered[position]]: position+=1
            if position==len(ordered): break
            chosen=ordered[position]; position+=1; seen[chosen]=True; acquired.append(chosen)
            close_free(seen,cursor,decision,pairs,permutation,events)
        snapshots.append(snapshot(scores,pairs,decision,cursor,len(acquired),budget))
    return snapshots,acquired,cursor,decision


def frontier_utilities(cursor,decision,seen,pairs,permutation,evidence,method,threshold):
    active=np.flatnonzero(decision==2)
    if not len(active): return {},active
    item=permutation[active,cursor[active]]
    weights=np.ones(len(active),dtype=float)
    if method=='frontier_evidence':
        observed=cursor[active]>0
        weights[observed]+=np.minimum(
            evidence[active[observed],cursor[active[observed]]-1],threshold)
    elif method!='frontier_count':
        raise ValueError('Unknown frontier method')
    utility={}
    for row,pair_index in enumerate(active):
        for system in pairs[pair_index]:
            label=(int(system),int(item[row]))
            if not seen[label]: utility[label]=utility.get(label,0.0)+float(weights[row])
    if not utility: raise AssertionError('Free frontiers must close before scheduling')
    return utility,active


def simulate_frontier(scores,pairs,permutation,events,evidence,method,priority,
                      threshold,fractions=FRACTIONS):
    systems,items=scores.shape; pair_count=len(pairs)
    if priority.shape!=scores.shape or len(np.unique(priority))!=priority.size:
        raise ValueError('Unique label priorities required')
    targets=tuple(int(np.floor(f*systems*items)) for f in fractions)
    seen=np.zeros_like(scores,dtype=bool); cursor=np.zeros(pair_count,dtype=np.int32)
    decision=np.full(pair_count,2,dtype=np.int8); acquired=[]; snapshots=[]
    close_free(seen,cursor,decision,pairs,permutation,events)
    for budget in targets:
        while len(acquired)<budget:
            utility,active=frontier_utilities(cursor,decision,seen,pairs,permutation,
                                               evidence,method,threshold)
            if not len(active): break
            best=max(utility.values())
            chosen=min((label for label,value in utility.items() if value==best),
                       key=lambda label:int(priority[label]))
            seen[chosen]=True; acquired.append(chosen)
            close_free(seen,cursor,decision,pairs,permutation,events)
        snapshots.append(snapshot(scores,pairs,decision,cursor,len(acquired),budget))
    if len(acquired)!=len(set(acquired)) or len(acquired)!=int(seen.sum()):
        raise AssertionError('Unique-label accounting failed')
    return snapshots,acquired,cursor,decision


def run(data_directory,repeats=50,output=None,master=MASTER):
    if repeats<1: raise ValueError('Positive repeats required')
    verify_lock(); datasets,provenance=load_prepared(data_directory); rows=[]
    for language,(scores,names,items) in sorted(datasets.items()):
        pairs,paths=permutations(names,len(items),language,repeats,master)
        threshold=40*len(pairs)
        events,evidence=make_paths(scores,pairs,paths,threshold)
        for repeat in range(repeats):
            order=np.random.default_rng(seed(master,language,repeat,'pair_priority')).permutation(len(pairs))
            pair_priority=np.empty(len(pairs),dtype=np.int64); pair_priority[order]=np.arange(len(pairs))
            unique_priority=label_priority(len(names),len(items),language,repeat,master)
            for method in METHODS:
                if method=='uniform_labels':
                    result=simulate_uniform(scores,pairs,paths[:,repeat],events[:,repeat],unique_priority)
                elif method in ('round_robin','focus_random','evidence_first'):
                    result=simulate(scores,pairs,paths[:,repeat],events[:,repeat],
                                    evidence[:,repeat],method,priority=pair_priority)
                else:
                    result=simulate_frontier(scores,pairs,paths[:,repeat],events[:,repeat],
                                             evidence[:,repeat],method,unique_priority,threshold)
                for fraction,record in zip(FRACTIONS,result[0]):
                    rows.append(dict(language=language,repeat=repeat,method=method,
                                     fraction=fraction,pairs=len(pairs),systems=len(names),
                                     items=len(items),threshold=threshold,**record))
            if (repeat+1)%10==0: print(f'{language}: {repeat+1}/{repeats} blocks',flush=True)
    if output:
        output=Path(output); output.mkdir(parents=True,exist_ok=False)
        with (output/'replicates.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        metadata=dict(master=master,repeats=repeats,languages=sorted(datasets),methods=list(METHODS),
                      fractions=list(FRACTIONS),protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
                      source_sha256=provenance['source_sha256'],
                      matrix_hashes={r['language']:r['matrix_sha256'] for r in provenance['reports'] if r['included']})
        (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--data',required=True)
    parser.add_argument('--repeats',type=int,default=50); parser.add_argument('--output',default='results/stage17_development')
    arguments=parser.parse_args(); run(arguments.data,arguments.repeats,arguments.output)
