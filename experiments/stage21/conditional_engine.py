"""Conditional finite-population e-processes after a score-dependent pilot."""
from __future__ import annotations

import numpy as np

RHOS=np.array((0.02,0.05,0.10,0.20,0.40,0.80),dtype=float)


def conditional_directional_paths(differences,pilot_sums,threshold):
    differences=np.asarray(differences,dtype=float)
    pilot_sums=np.asarray(pilot_sums,dtype=float)
    if differences.ndim!=3 or pilot_sums.shape!=differences.shape[:2]:
        raise ValueError("Pilot sums and remaining paths must align")
    if not np.isfinite(differences).all() or np.any(np.abs(differences)>1):
        raise ValueError("Expected remaining differences in [-1,1]")
    if not np.isfinite(pilot_sums).all() or not np.isfinite(threshold) or threshold<=1:
        raise ValueError("Invalid pilot sum or threshold")
    edges,repeats,m=differences.shape
    log_threshold=float(np.log(threshold))
    log_wealth=np.zeros((2,edges,repeats,len(RHOS)),dtype=float)
    sums=np.zeros((2,edges,repeats),dtype=float)
    events=np.full((edges,repeats,m+1),2,dtype=np.int8)
    evidence=np.ones((edges,repeats,m+1),dtype=float)
    initial=np.where(pilot_sums-m>0,1,np.where(pilot_sums+m<0,-1,2))
    events[:,:,0]=initial
    for t in range(m):
        remaining_before=m-t
        for direction in range(2):
            x=differences[:,:,t] if direction==0 else -differences[:,:,t]
            pilot=pilot_sums if direction==0 else -pilot_sums
            boundary=-pilot
            center=(boundary-sums[direction])/remaining_before
            feasible=center>-1
            factor=np.ones((*center.shape,len(RHOS)),dtype=float)
            if np.any(feasible):
                c=center[feasible,None]
                factor[feasible]=1+RHOS[None,:]*(x[feasible,None]-c)/(1+c)
            if np.any(factor<=0) or not np.isfinite(factor).all():
                raise FloatingPointError("Conditional betting factor left its valid range")
            log_wealth[direction]+=np.log(factor)
            sums[direction]+=x
        peak=np.max(log_wealth,axis=-1)
        log_mixture=peak+np.log(np.mean(np.exp(log_wealth-peak[...,None]),axis=-1))
        capped=np.exp(np.minimum(log_mixture,log_threshold))
        evidence[:,:,t+1]=np.maximum(capped[0],capped[1])
        forward=log_mixture[0]>=log_threshold
        reverse=log_mixture[1]>=log_threshold
        statistical=np.where(forward&~reverse,1,np.where(reverse&~forward,-1,2))
        remaining_after=m-t-1
        total_partial=pilot_sums+sums[0]
        deterministic=np.where(total_partial-remaining_after>0,1,
                               np.where(total_partial+remaining_after<0,-1,2))
        new=np.where(deterministic!=2,deterministic,statistical)
        events[:,:,t+1]=np.where(events[:,:,t]!=2,events[:,:,t],new)
        if t==m-1:
            events[:,:,t+1]=np.sign(total_partial).astype(np.int8)
    return events,evidence
