"""Reconstruct paid ledgers, decisions, and actual-null conditional expectations."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path

import numpy as np

from engine import (ALPHA,CELL_METHODS,ColumnModel,edges_for,pair_factor,
                    paired_factor,proposal)
from study import HERE,ALL_METHODS,grid,inputs,legacy_rebalanced,run_block,stage22,summarize


def decisions_from_ledger(observed,edges,previous,logs):
    answer=previous.copy()
    total=np.array([sum(x for x in row if x>=0) for row in observed])
    missing=np.array([sum(x<0 for x in row) for row in observed])
    threshold=np.log(2*len(edges)/ALPHA)
    for e,(a,b) in enumerate(edges):
        if answer[e]!=2: continue
        low=total[a]-total[b]-missing[b]; high=total[a]+missing[a]-total[b]
        if low>0: answer[e]=1
        elif high<0: answer[e]=-1
        elif missing[a]==missing[b]==0: answer[e]=int(np.sign(total[a]-total[b]))
        elif (logs[e,0]>=threshold)!=(logs[e,1]>=threshold):
            answer[e]=1 if logs[e,0]>=threshold else -1
    return answer


def audit_cells(case,method,model,scores,edges):
    saved=case['methods'][method]; observed=np.full_like(scores,-1)
    logs=np.zeros((len(edges),2)); decisions=np.full(len(edges),2,int)
    rng=np.random.default_rng(case['seeds']['acquisition'])
    prng=np.random.default_rng(case['seeds']['particle'])
    checks=0; largest=0.
    for row in saved['trace']:
        predicted=model.predict(observed,peer=method!='no_peer')
        q=proposal(observed,predicted,edges,decisions,method,model,prng)
        if np.any(q[observed>=0]) or abs(q.sum()-1)>1e-13:
            raise AssertionError('Bad conditional acquisition probabilities')
        selected=int(rng.choice(scores.size,p=q.ravel()))
        if selected!=row['cell']: raise AssertionError('Changed query or RNG ledger')
        v,item=divmod(selected,scores.shape[1]); value=int(scores[v,item])
        if observed[v,item]>=0 or value!=row['value']:
            raise AssertionError('Duplicate or incorrect paid score')
        if abs(q[v,item]-row['q'])>1e-13: raise AssertionError('Wrong saved selection chance')
        increment=np.zeros_like(logs); bound=0.
        for e,(a,b) in enumerate(edges):
            if decisions[e]!=2: continue
            for direction,(x,y) in enumerate(((a,b),(b,a))):
                factor,peak=pair_factor(observed,predicted,q,x,y)
                if peak>1+1e-12: raise AssertionError('Failed full null calibration')
                # This expectation is computed from the hidden fixed matrix,
                # independently of the maximization/projection implementation.
                if scores[x].sum()<=scores[y].sum():
                    realized=np.take_along_axis(factor,scores[:,:,None],axis=2)[:,:,0]
                    expectation=float(np.sum(q*realized))
                    if expectation>1+1e-12: raise AssertionError('True-null factor expectation exceeds one')
                    largest=max(largest,expectation); checks+=1
                increment[e,direction]=np.log(factor[v,item,value]); bound=max(bound,peak)
        np.testing.assert_allclose(increment,row['increments'],rtol=0,atol=1e-12)
        if abs(bound-row['peak'])>1e-12: raise AssertionError('Changed calibration bound')
        observed[v,item]=value; logs+=increment
        decisions=decisions_from_ledger(observed,edges,decisions,logs)
        if decisions.tolist()!=row['decisions']: raise AssertionError('Wrong stopped decision')
    return observed,decisions,checks,largest


def audit_paired(case,model,scores,edges):
    observed=np.full_like(scores,-1); logs=np.zeros((len(edges),2)); decisions=np.full(len(edges),2,int)
    counts=np.zeros((len(edges),2,3),int); checks=0; largest=0.; n=scores.shape[1]
    for step,row in enumerate(case['methods']['paired_exact']['trace']):
        item=case['order'][step]
        unresolved=np.flatnonzero(decisions==2)
        active=sorted({v for e in unresolved for v in edges[e]})
        if row['item']!=item or row['active']!=active: raise AssertionError('Changed common-item active set')
        if row['values']!=[int(scores[v,item]) for v in active]: raise AssertionError('Incorrect block scores')
        increments=np.zeros_like(logs)
        for e in unresolved:
            a,b=edges[e]
            for direction,(x,y) in enumerate(((a,b),(b,a))):
                pd=model.patterns[:,x]-model.patterns[:,y]
                prior=tuple(float(model.prob[pd==v].sum()) for v in (-1,0,1))
                f=paired_factor(tuple(counts[e,direction]),prior,n)
                if scores[x].sum()<=scores[y].sum():
                    remaining=np.array(case['order'][step:])
                    outcomes=scores[x,remaining]-scores[y,remaining]+1
                    expectation=float(f[outcomes].mean())
                    if expectation>1+1e-12: raise AssertionError('Invalid paired true-null expectation')
                    checks+=1; largest=max(largest,expectation)
                event=int(scores[x,item]-scores[y,item]+1)
                increments[e,direction]=np.log(f[event]); counts[e,direction,event]+=1
        np.testing.assert_allclose(increments,row['increments'],rtol=0,atol=1e-10)
        for v in active:
            if observed[v,item]>=0: raise AssertionError('Repeated block score')
            observed[v,item]=scores[v,item]
        logs+=increments; decisions=decisions_from_ledger(observed,edges,decisions,logs)
        if decisions.tolist()!=row['decisions']: raise AssertionError('Wrong paired decision')
    return observed,decisions,checks,largest


def audit_case(case):
    spec=tuple(case['spec']); scenario,k,n,graph,repeat=spec
    scores,history,seeds,order=inputs(spec,case['smoke']); model=ColumnModel(history)
    if scores.tolist()!=case['scores'] or seeds!=case['seeds'] or order.tolist()!=case['order']:
        raise AssertionError('Case differs from frozen generator')
    counts=((model.prob*(2048+.5*2**k))-.5).round().astype(int).tolist()
    if counts!=case['history_counts']: raise AssertionError('Historical input changed')
    methods=ALL_METHODS if k==3 else ALL_METHODS[:-2]
    if set(case['methods'])!=set(methods): raise AssertionError('Missing control')
    edges=edges_for(k,graph); checks=paid=wrong=0; largest=0.
    for method in methods:
        saved=case['methods'][method]
        if method in CELL_METHODS:
            observed,decisions,tests,peak=audit_cells(case,method,model,scores,edges)
        elif method=='paired_exact':
            observed,decisions,tests,peak=audit_paired(case,model,scores,edges)
        else:
            if method=='stage22': fresh=stage22(scores,edges,order)
            elif method=='paired_exact_closure':
                fresh=run_block(scores,tuple(model.marginal),order,
                    'star' if graph=='star' else 'triangle',method)
            else: fresh=legacy_rebalanced(scores,tuple(model.marginal),edges,graph,seeds['acquisition'])
            if fresh!=saved: raise AssertionError('Preserved control replay changed')
            observed=np.full_like(scores,-1)
            for row in saved['trace']:
                purchases=[(divmod(row['cell'],n),row['value'])] if 'cell' in row else [
                    ((v,row['item']),y) for v,y in zip(row['active'],row['values'])]
                for (v,i),y in purchases:
                    if observed[v,i]>=0 or y!=scores[v,i]: raise AssertionError('Invalid legacy paid ledger')
                    observed[v,i]=y
            decisions=np.array(saved['decisions']); tests=0; peak=0.
        true=np.array([np.sign(scores[a].sum()-scores[b].sum()) for a,b in edges])
        errors=int(np.any(decisions!=true)); cost=int(np.sum(observed>=0))
        if np.any(decisions==2) or decisions.tolist()!=saved['decisions']:
            raise AssertionError('Unfinished or inconsistent final decisions')
        if cost!=saved['paid'] or errors!=saved['wrong'] or saved['charged']!=(scores.size if errors else cost):
            raise AssertionError('Incorrect cost, error, or penalty')
        checks+=tests; largest=max(largest,peak); paid+=cost; wrong+=errors
    return {'trajectories':len(methods),'paid_cells_checked':paid,'actual_null_factor_checks':checks,
            'largest_actual_null_expectation':largest,'wrong':wrong}


def audit(folder,workers=2):
    metadata=json.loads((folder/'metadata.json').read_text())
    if hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest()!=metadata['protocol_sha256']:
        raise AssertionError('Protocol changed')
    for name,digest in metadata['source_sha256'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest: raise AssertionError('Implementation changed: '+name)
    with gzip.open(folder/'cases.json.gz','rt') as f: cases=json.load(f)
    expected=[('one_hot',3,8,'star',0)] if metadata['smoke'] else grid()
    if sorted(tuple(c['spec']) for c in cases)!=sorted(expected): raise AssertionError('Incomplete locked grid')
    reports=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(audit_case,c) for c in cases]
        for future in as_completed(futures):
            reports.append(future.result())
            if len(reports)%10==0 or len(reports)==len(cases):
                print(f'Audited {len(reports)}/{len(cases)} cases',flush=True)
    if summarize(cases)!=json.loads((folder/'summary.json').read_text()): raise AssertionError('Changed analysis')
    report={'status':'passed','cases':len(cases),'trajectories':sum(r['trajectories'] for r in reports),
        'paid_cells_checked':sum(r['paid_cells_checked'] for r in reports),
        'actual_null_factor_checks':sum(r['actual_null_factor_checks'] for r in reports),
        'largest_actual_null_expectation':max(r['largest_actual_null_expectation'] for r in reports),
        'wrong_trajectories':sum(r['wrong'] for r in reports),
        'protocol_sha256':metadata['protocol_sha256'],
        'scope':'full ledger/decision replay; actual fixed-null expectations; support formula tested separately by exhaustive small completions'}
    (folder/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args(); audit(args.input,args.workers)
