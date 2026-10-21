"""Run the frozen Stage 21 pilot-selected chain experiment."""
from __future__ import annotations

import argparse,csv,hashlib,json,sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"stage18")); sys.path.insert(0,str(HERE.parent/"stage17")); sys.path.insert(0,str(HERE.parent/"stage14"))
from prepare_scores import load_prepared
from run_stage18 import MASTER,common_design
from shared_pilot import FRACTIONS
from conditional_engine import conditional_directional_paths

METHODS=("selected_chain","selected_chain_allpair_threshold")


def verify_lock():
    lock=json.loads((HERE/"IMPLEMENTATION_LOCK.json").read_text()); repository=HERE.parent.parent
    for relative,expected in lock["sha256"].items():
        if hashlib.sha256((repository/relative).read_bytes()).hexdigest()!=expected: raise ValueError("Locked source changed: "+relative)
    return lock


def select_chain(pilot_scores,names):
    pilot_scores=np.asarray(pilot_scores,dtype=float); names=np.asarray(names)
    if pilot_scores.ndim!=2 or len(names)!=pilot_scores.shape[0]: raise ValueError("Pilot scores and names must align")
    sums=pilot_scores.sum(axis=1)
    order=sorted(range(len(names)),key=lambda system:(-float(sums[system]),str(names[system])))
    edges=np.asarray(list(zip(order[:-1],order[1:])),dtype=np.int16)
    return np.asarray(order,dtype=np.int16),edges


def closure_snapshot(scores,edges,decision,cursor,labels,budget):
    systems=scores.shape[0]; reach=np.zeros((systems,systems),dtype=bool)
    direct=int(np.sum(decision!=2))
    for (a,b),value in zip(edges,decision):
        if value==1: reach[a,b]=True
        elif value==-1: reach[b,a]=True
    for k in range(systems): reach|=reach[:,k,None]&reach[k,None,:]
    totals=scores.sum(axis=1); correct=wrong=resolved=0
    for a in range(systems):
        for b in range(a+1,systems):
            ab=bool(reach[a,b]); ba=bool(reach[b,a])
            if not ab and not ba: continue
            resolved+=1; truth=int(np.sign(totals[a]-totals[b]))
            predicted=(1 if ab and not ba else -1 if ba and not ab else 0)
            if predicted!=0 and predicted==truth: correct+=1
            else: wrong+=1
    pairs=systems*(systems-1)//2
    return dict(budget=budget,labels=labels,correct=correct,wrong=wrong,
                unresolved=pairs-resolved,resolved_pairs=resolved,
                direct_edges=direct,closure_added=resolved-direct,
                reached_prefix=int(cursor.sum()),complete_ranking=int(correct==pairs and wrong==0))


def simulate_chain(scores,edges,item_order,priority,pilot_size,events,fractions=FRACTIONS):
    systems,items=scores.shape; remaining=item_order[pilot_size:]
    if events.shape!=(len(edges),len(remaining)+1): raise ValueError("Event path mismatch")
    ordered=[tuple(map(int,index)) for index in np.ndindex(scores.shape)]
    ordered.sort(key=lambda label:int(priority[label]))
    targets=tuple(int(np.floor(f*systems*items)) for f in fractions)
    pilot_cost=pilot_size*systems; seen=np.zeros_like(scores,dtype=bool)
    cursor=np.zeros(len(edges),dtype=np.int32); decision=np.full(len(edges),2,dtype=np.int8)
    acquired=[]; position=0; snapshots=[]; initialized=False
    for budget in targets:
        while len(acquired)<budget:
            if position==len(ordered): break
            chosen=ordered[position]; position+=1; seen[chosen]=True; acquired.append(chosen)
            if not initialized and len(acquired)>=pilot_cost:
                decision=np.where(events[:,0]!=2,events[:,0],decision); initialized=True
            if initialized:
                while True:
                    active=np.flatnonzero(decision==2)
                    if not len(active): break
                    next_index=cursor[active]
                    eligible=active[next_index<len(remaining)]
                    if not len(eligible): break
                    item=remaining[cursor[eligible]]
                    a,b=edges[eligible].T
                    ready=eligible[seen[a,item]&seen[b,item]]
                    if not len(ready): break
                    cursor[ready]+=1
                    result=events[ready,cursor[ready]]
                    decision[ready[result!=2]]=result[result!=2]
            if not np.any(decision==2) and initialized: break
        snapshots.append(closure_snapshot(scores,edges,decision,cursor,len(acquired),budget))
    if len(acquired)!=len(set(acquired)) or len(acquired)!=int(seen.sum()): raise AssertionError("Unique-label accounting failed")
    return snapshots,acquired,cursor,decision


def run(data_directory,repeats=50,output=None,master=MASTER):
    if repeats<1: raise ValueError("Positive repeats required")
    verify_lock(); datasets,provenance=load_prepared(data_directory); rows=[]
    for language,(scores,names,items) in sorted(datasets.items()):
        n=len(items); pilot_size=n//4; systems=len(names); pair_count=systems*(systems-1)//2
        for repeat in range(repeats):
            item_order,priority=common_design(systems,n,language,repeat,master)
            pilot_items=item_order[:pilot_size]; remaining=item_order[pilot_size:]
            order,edges=select_chain(scores[:,pilot_items],names)
            pilot_sums=scores[edges[:,0]][:,pilot_items].sum(axis=1)-scores[edges[:,1]][:,pilot_items].sum(axis=1)
            differences=scores[edges[:,0]][:,remaining]-scores[edges[:,1]][:,remaining]
            thresholds={"selected_chain":40*len(edges),"selected_chain_allpair_threshold":40*pair_count}
            for method in METHODS:
                events,_=conditional_directional_paths(differences[:,None,:],pilot_sums[:,None],thresholds[method])
                result=simulate_chain(scores,edges,item_order,priority,pilot_size,events[:,0])
                for fraction,record in zip(FRACTIONS,result[0]):
                    rows.append(dict(language=language,repeat=repeat,method=method,fraction=fraction,
                                     pairs=pair_count,systems=systems,items=n,pilot_items=pilot_size,
                                     selected_edges=len(edges),threshold=thresholds[method],**record))
        print(f"{language}: {repeats}/{repeats} selected-chain blocks",flush=True)
    if output:
        output=Path(output); output.mkdir(parents=True,exist_ok=False)
        with (output/"replicates.csv").open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
        stage18=HERE.parent/"stage18"/"results_reference"
        metadata=dict(master=master,repeats=repeats,languages=sorted(datasets),methods=list(METHODS),fractions=list(FRACTIONS),
                      protocol_sha256=hashlib.sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest(),source_sha256=provenance["source_sha256"],
                      matrix_hashes={r["language"]:r["matrix_sha256"] for r in provenance["reports"] if r["included"]},
                      stage18_replicates_sha256=hashlib.sha256((stage18/"replicates.csv").read_bytes()).hexdigest())
        (output/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    return rows


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--data",required=True);parser.add_argument("--repeats",type=int,default=50);parser.add_argument("--output",default="results/stage21_development")
    a=parser.parse_args();run(a.data,a.repeats,a.output)
