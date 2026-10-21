"""Generic categorical PPR paths with a language-specific evidence ceiling."""
from __future__ import annotations

from functools import lru_cache
import math
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'stage13'))
from paired_engine import Q,boundary_modes


@lru_cache(maxsize=1)
def binomial_table(n):
    if n<2:
        raise ValueError('At least two items required')
    return tuple(tuple(math.comb(i,j) for j in range(i+1)) for i in range(n+1))


def raw_evidence(n,positive,negative,equal,cap_units,table=None):
    table=binomial_table(n) if table is None else table
    counts=np.asarray([positive,negative,equal],dtype=np.int64)
    if counts.ndim!=2 or np.any(counts<0):
        raise ValueError('Nonnegative count vectors required')
    totals=counts.sum(axis=0)
    if np.any(totals>n) or not np.all(totals==totals[0]):
        raise ValueError('Counts must share a feasible query time')
    cap=int(cap_units)*Q
    t=int(totals[0])
    numerator=2*Q*table[n][t]
    base=(t+1)*(t+2)
    result=np.zeros((2,counts.shape[1]),dtype=np.int64)
    for direction in range(2):
        a,b,c=counts[direction],counts[1-direction],counts[2]
        indices=np.flatnonzero(a>b)
        if not len(indices):
            continue
        aa,bb,cc=a[indices],b[indices],c[indices]
        modes=[boundary_modes(n,aa,bb,cc,d) for d in (0,1)]
        for j,index in enumerate(indices):
            maximum=0
            for parity,mode in enumerate(modes):
                k=int(mode[j])
                if k>=0:
                    product=(table[k][int(aa[j])]*table[k+parity][int(bb[j])]*
                             table[n-2*k-parity][int(cc[j])])
                    maximum=max(maximum,product)
            result[direction,index]=(cap if maximum==0 else
                                     min(cap,numerator//(base*maximum)))
    return result


def make_paths(scores,pairs,permutations,cap_units):
    scores=np.asarray(scores)
    pair_count,repeats,n=permutations.shape
    if scores.ndim!=2 or scores.shape[1]!=n or len(pairs)!=pair_count:
        raise ValueError('Matrix and paths must align')
    if np.any((scores!=0)&(scores!=1)):
        raise ValueError('Binary outcomes required')
    if not np.array_equal(np.sort(permutations,axis=-1),
                          np.broadcast_to(np.arange(n),permutations.shape)):
        raise ValueError('Every pair path must be a permutation')
    a,b=pairs.T
    differences=(scores[a[:,None,None],permutations]-
                 scores[b[:,None,None],permutations])
    positive=np.zeros((pair_count,repeats),dtype=np.int64)
    negative=positive.copy(); equal=positive.copy()
    events=np.full((pair_count,repeats,n),2,dtype=np.int8)
    evidence=np.zeros((pair_count,repeats,n),dtype=np.int64)
    table=binomial_table(n)
    threshold=int(cap_units)*Q
    for t in range(n):
        d=differences[:,:,t]
        positive+=d==1; negative+=d==-1; equal+=d==0
        raw=raw_evidence(n,positive.ravel(),negative.ravel(),equal.ravel(),
                         cap_units,table).reshape(2,pair_count,repeats)
        evidence[:,:,t]=np.maximum(raw[0],raw[1])
        forward=raw[0]>=threshold; reverse=raw[1]>=threshold
        statistical=np.where(forward&~reverse,1,np.where(reverse&~forward,-1,2))
        remaining=n-t-1
        observed=positive-negative
        deterministic=np.where(observed>remaining,1,np.where(observed< -remaining,-1,2))
        events[:,:,t]=np.where(deterministic!=2,deterministic,statistical)
        if t==n-1:
            events[:,:,t]=np.sign(observed)
    return events,evidence
