"""Continuous finite-population pair evidence on complete random paths."""
from __future__ import annotations

import numpy as np

RHOS=np.array((0.02,0.05,0.10,0.20,0.40,0.80),dtype=float)


def directional_paths(differences,threshold):
    differences=np.asarray(differences,dtype=float)
    if differences.ndim!=3 or not np.isfinite(differences).all() or np.any(np.abs(differences)>1):
        raise ValueError('Expected finite pair differences in [-1,1]')
    pair_count,repeats,n=differences.shape
    if n<2 or not np.isfinite(threshold) or threshold<=1:
        raise ValueError('Invalid pool or threshold')
    log_threshold=float(np.log(threshold))
    log_wealth=np.zeros((2,pair_count,repeats,len(RHOS)),dtype=float)
    sums=np.zeros((2,pair_count,repeats),dtype=float)
    events=np.full((pair_count,repeats,n),2,dtype=np.int8)
    evidence=np.zeros((pair_count,repeats,n),dtype=float)
    for t in range(n):
        remaining_before=n-t
        for direction in range(2):
            x=differences[:,:,t] if direction==0 else -differences[:,:,t]
            center=-sums[direction]/remaining_before
            feasible=center>-1
            factor=np.ones((*center.shape,len(RHOS)),dtype=float)
            if np.any(feasible):
                c=center[feasible,None]
                factor[feasible]=1+RHOS[None,:]*(x[feasible,None]-c)/(1+c)
            if np.any(factor<=0) or not np.isfinite(factor).all():
                raise FloatingPointError('Betting factor left its valid range')
            log_wealth[direction]+=np.log(factor)
            sums[direction]+=x
        peak=np.max(log_wealth,axis=-1)
        log_mixture=peak+np.log(np.mean(np.exp(log_wealth-peak[...,None]),axis=-1))
        capped=np.exp(np.minimum(log_mixture,log_threshold))
        evidence[:,:,t]=np.maximum(capped[0],capped[1])
        forward=log_mixture[0]>=log_threshold
        reverse=log_mixture[1]>=log_threshold
        statistical=np.where(forward&~reverse,1,np.where(reverse&~forward,-1,2))
        remaining_after=n-t-1
        observed=sums[0]
        deterministic=np.where(observed-remaining_after>0,1,
                               np.where(observed+remaining_after<0,-1,2))
        events[:,:,t]=np.where(deterministic!=2,deterministic,statistical)
        if t==n-1:
            events[:,:,t]=np.sign(observed).astype(np.int8)
    return events,evidence


def make_paths(scores,pairs,permutations,threshold):
    scores=np.asarray(scores,dtype=float)
    pairs=np.asarray(pairs)
    permutations=np.asarray(permutations)
    pair_count,repeats,n=permutations.shape
    if scores.ndim!=2 or scores.shape[1]!=n or len(pairs)!=pair_count:
        raise ValueError('Matrix and paths must align')
    if not np.isfinite(scores).all() or np.any((scores<0)|(scores>1)):
        raise ValueError('Scores must be finite in [0,1]')
    if not np.array_equal(np.sort(permutations,axis=-1),
                          np.broadcast_to(np.arange(n),permutations.shape)):
        raise ValueError('Every pair path must be a permutation')
    a,b=pairs.T
    differences=(scores[a[:,None,None],permutations]-
                 scores[b[:,None,None],permutations])
    return directional_paths(differences,threshold)
