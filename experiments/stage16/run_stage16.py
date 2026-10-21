"""Run frozen WMT25 external validation."""
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
from external_engine import Q,make_paths
from prepare_wmt25 import load_prepared

MASTER=20261023
METHODS=('focus_random','evidence_first','frontier_evidence')


def frontier_utilities(cursor,decision,seen,pairs,permutation,evidence,cap_units):
    """Return label utilities using the frozen language-specific ceiling."""
    active=np.flatnonzero(decision==2)
    if not len(active):
        return {},active
    item=permutation[active,cursor[active]]
    current=np.zeros(len(active),dtype=np.int64)
    observed=cursor[active]>0
    current[observed]=evidence[active[observed],cursor[active[observed]]-1]
    weights=Q+np.minimum(current,int(cap_units)*Q)
    utility={}
    for row,pair_index in enumerate(active):
        for system in pairs[pair_index]:
            label=(int(system),int(item[row]))
            if not seen[label]:
                utility[label]=utility.get(label,0)+int(weights[row])
    if not utility:
        raise AssertionError('Free frontiers must be closed before scheduling')
    return utility,active


def simulate_frontier(scores,pairs,permutation,events,evidence,priority,cap_units,
                      fractions=FRACTIONS):
    """Acquire unique labels and close every newly free pair prefix."""
    scores=np.asarray(scores)
    systems,items=scores.shape
    pair_count=len(pairs)
    if permutation.shape!=(pair_count,items) or events.shape!=(pair_count,items) or evidence.shape!=(pair_count,items):
        raise ValueError('Expected one precommitted path for every pair')
    if priority.shape!=scores.shape or len(np.unique(priority))!=priority.size:
        raise ValueError('Unique tie priorities must match all labels')
    targets=tuple(int(np.floor(f*systems*items)) for f in fractions)
    seen=np.zeros_like(scores,dtype=bool)
    cursor=np.zeros(pair_count,dtype=np.int32)
    decision=np.full(pair_count,2,dtype=np.int8)
    acquired=[]
    snapshots=[]
    a,b=pairs.T

    def close_free():
        while True:
            active=np.flatnonzero(decision==2)
            if not len(active):
                return
            item=permutation[active,cursor[active]]
            ready=active[seen[a[active],item]&seen[b[active],item]]
            if not len(ready):
                return
            cursor[ready]+=1
            result=events[ready,cursor[ready]-1]
            resolved=result!=2
            decision[ready[resolved]]=result[resolved]

    close_free()
    for budget in targets:
        while len(acquired)<budget:
            utility,active=frontier_utilities(
                cursor,decision,seen,pairs,permutation,evidence,cap_units)
            if not len(active):
                break
            best=max(utility.values())
            candidates=[label for label,value in utility.items() if value==best]
            chosen=min(candidates,key=lambda label:int(priority[label]))
            if seen[chosen]:
                raise AssertionError('A paid label was acquired twice')
            seen[chosen]=True
            acquired.append(chosen)
            close_free()
        truth=np.sign(scores[a].sum(axis=1)-scores[b].sum(axis=1))
        correct=int(np.sum((decision!=2)&(decision==truth)))
        wrong=int(np.sum((decision!=2)&(decision!=truth)))
        snapshots.append(dict(
            budget=budget,labels=len(acquired),correct=correct,wrong=wrong,
            unresolved=pair_count-correct-wrong,reached_prefix=int(cursor.sum()),
            resolved_pairs=correct+wrong))
    if len(acquired)!=len(set(acquired)) or len(acquired)!=int(seen.sum()):
        raise AssertionError('Unique-label accounting failed')
    return snapshots,acquired,cursor,decision


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
                seed(master,language,str(names[a]),str(names[b]),repeat)
            ).permutation(n)
    return pairs,paths


def run(data_directory,repeats=50,output=None,master=MASTER):
    if repeats<1:
        raise ValueError('Positive repeats required')
    verify_lock()
    datasets,provenance=load_prepared(data_directory)
    rows=[]
    for language,(scores,names,items) in sorted(datasets.items()):
        pairs,paths=permutations(names,len(items),language,repeats,master)
        cap_units=40*len(pairs)
        events,evidence=make_paths(scores,pairs,paths,cap_units)
        for repeat in range(repeats):
            order=np.random.default_rng(seed(master,language,repeat,'pair_priority')).permutation(len(pairs))
            pair_priority=np.empty(len(pairs),dtype=np.int64); pair_priority[order]=np.arange(len(pairs))
            unique_priority=label_priority(len(names),len(items),language,repeat,master)
            for method in METHODS:
                if method=='frontier_evidence':
                    result=simulate_frontier(scores,pairs,paths[:,repeat],events[:,repeat],
                                             evidence[:,repeat],unique_priority,cap_units)
                else:
                    result=simulate(scores,pairs,paths[:,repeat],events[:,repeat],
                                    evidence[:,repeat],method,priority=pair_priority)
                snapshots,_,_,_=result
                for fraction,snapshot in zip(FRACTIONS,snapshots):
                    rows.append(dict(language=language,repeat=repeat,method=method,
                                     fraction=fraction,pairs=len(pairs),systems=len(names),
                                     items=len(items),threshold_units=cap_units,**snapshot))
            if (repeat+1)%10==0:
                print(f'{language}: {repeat+1}/{repeats} blocks',flush=True)
        # Drop the potentially large one-language cached table before the next pool.
        from external_engine import binomial_table
        binomial_table.cache_clear()
    if output:
        output=Path(output); output.mkdir(parents=True,exist_ok=False)
        with (output/'replicates.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        metadata=dict(master=master,repeats=repeats,languages=sorted(datasets),methods=list(METHODS),
                      fractions=list(FRACTIONS),protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
                      source_sha256=provenance['source_sha256'],matrix_hashes={r['language']:r['matrix_sha256'] for r in provenance['reports'] if r['included']})
        (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',required=True)
    parser.add_argument('--repeats',type=int,default=50)
    parser.add_argument('--output',default='results/stage16_external')
    args=parser.parse_args()
    run(args.data,args.repeats,args.output)
