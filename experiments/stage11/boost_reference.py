"""Independent observed-branch replay, without the production pair updater."""
from __future__ import annotations
from fractions import Fraction
import numpy as np


def rational_pair(w,a,r,u,d,boost):
    """Arbitrary-precision reference, including rounding in grid units."""
    cap=20*2**39
    if a==0:return (w if boost else w*(d-u)//d),cap
    if a==r:return cap,(w if boost else w*u//d)
    factors=[Fraction((d-u)*r,d*(r-a)),Fraction(u*r,d*a)]
    if not boost:return tuple(min(cap,int(w*f)) for f in factors)
    p=[Fraction(r-a,r),Fraction(a,r)]
    high=int(factors[1]>=factors[0]);low=1-high
    if w*factors[high]<cap:return tuple(int(w*f) for f in factors)
    answer=[None,None];answer[high]=cap
    answer[low]=int((Fraction(w)-p[high]*cap)/p[low])
    return tuple(answer)


def replay(outcomes,ledger,raw):
    # Inputs are checked by source validation / tests, not the production engine.
    n,repeats=ledger.shape
    scale=2**39;cap=20*scale
    states=[np.full((repeats,n+1),scale,dtype=np.int64) for _ in range(2)]
    live=[np.ones((repeats,n+1),dtype=bool) for _ in range(2)]
    rejected=np.full((2,n+1,repeats),n+1,dtype=np.int16)
    curves=np.empty((2,2,n,repeats),dtype=np.int16)
    fallback=np.zeros((2,n,repeats),dtype=bool)
    gaps=np.zeros((2,n,repeats),dtype=np.int16)
    s=np.zeros(repeats,dtype=np.int64)
    for time in range(n):
        remaining=n-time;den=time+2;obs=np.asarray(outcomes[ledger[time]],dtype=np.int64)
        prior=np.where(obs==1,s+1,time-s+1)[:,None]
        for m in range(2):
            cols=np.flatnonzero(live[m].any(axis=0))
            if len(cols):
                begin,end=int(cols[0]),int(cols[-1])+1
                a=np.arange(begin,end)[None,:]-s[:,None]
                prob=np.where(obs[:,None]==1,a,remaining-a)
                possible=(prob>0)&(prob<=remaining)
                prob=np.clip(prob,1,remaining)
                w=states[m][:,begin:end]
                updated=np.minimum(cap,(w*prior*remaining)//(den*prob))
                if m:
                    observed_high=prior*remaining>=den*prob
                    self_cross=w*prior*remaining>=cap*den*prob
                    other_cross=w*(den-prior)*remaining>=cap*den*(remaining-prob)
                    adjusted=(remaining*w-cap*(remaining-prob))//prob
                    updated=np.where(observed_high&self_cross,cap,updated)
                    updated=np.where((~observed_high)&other_cross,adjusted,updated)
                    updated=np.where(prob==remaining,w,updated)
                before=live[m][:,begin:end]
                after=before&possible&(updated<cap)
                view=rejected[m,begin:end].T;view[before&~after]=time+1
                live[m][:,begin:end]=after
                states[m][:,begin:end]=np.where(after,updated,0)
            empty=live[m].sum(axis=1)==0
            lower=live[m].argmax(axis=1)
            upper=n-live[m][:,::-1].argmax(axis=1)
            gaps[m,time]=np.where(empty,0,upper-lower+1-live[m].sum(axis=1))
            base=raw[:,time] if m==0 else curves[0,:,time]
            curves[m,0,time]=np.where(empty,base[0],lower)
            curves[m,1,time]=np.where(empty,base[1],upper)
            fallback[m,time]=empty
        s+=obs
    curves[:,:,-1]=s[None,None,:];fallback[:,-1]=False
    return dict(counts=curves,repaired=fallback,rejection_time=rejected,holes=gaps)
