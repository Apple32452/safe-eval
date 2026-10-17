"""Conservative integer implementation of Fischer--Ramdas sequential boosting.

All candidate totals are inverted. No floating arithmetic decides rejection.
See THEORY.md for the PPR specialization and finite-precision argument.
"""
from __future__ import annotations
import numpy as np

Q = 2**39
B = 20*Q
MAX_N = 820


def next_pair(w, a, r, u, d, boost):
    """Possible next wealths, chosen from the pre-query state only.

    w is in grid units, a/r is the null probability, u/d the predictive
    probability. Arrays may broadcast. Caller enforces the int64 bound.
    """
    a=np.clip(a,0,r)
    z0=np.minimum(B,(w*(d-u)*r)//(d*np.maximum(r-a,1)))
    z1=np.minimum(B,(w*u*r)//(d*np.maximum(a,1)))
    if boost:
        high_one=u*r>=d*a
        high_num=np.where(high_one,a,r-a)
        crosses=w*np.where(high_one,u,d-u)*r>=B*d*high_num
        interior=(a>0)&(a<r)
        cap=crosses&interior
        low=(r*w-B*high_num)//np.maximum(r-high_num,1)
        z0=np.where(cap,np.where(high_one,low,B),z0)
        z1=np.where(cap,np.where(high_one,B,low),z1)
        z0=np.where(a==0,w,z0)
        z1=np.where(a==r,w,z1)
    # Outcomes outside null support can be rejected with probability zero.
    z1=np.where(a==0,B,z1)
    z0=np.where(a==r,B,z0)
    return z0,z1


def hull(alive):
    n=alive.shape[1]-1
    k=np.arange(n+1)
    empty=~alive.any(axis=1)
    lo=np.where(alive,k,n+1).min(axis=1)
    hi=np.where(alive,k,-1).max(axis=1)
    holes=np.where(empty,0,hi-lo+1-alive.sum(axis=1))
    return lo,hi,empty,holes


def validate_inputs(outcomes,ledger,raw):
    y=np.asarray(outcomes);ledger=np.asarray(ledger);raw=np.asarray(raw)
    if ledger.ndim!=2 or ledger.dtype.kind not in 'iu':raise ValueError('Integer query ledger required')
    n,repeats=ledger.shape
    if not 2<=n<=MAX_N or repeats<1 or B*(n+1)**2>np.iinfo(np.int64).max:
        raise ValueError('Unsupported dimensions or integer bound')
    if y.shape!=(n,) or np.any((y!=0)&(y!=1)):raise ValueError('Exact binary outcomes required')
    if not np.array_equal(np.sort(ledger,axis=0),np.broadcast_to(np.arange(n)[:,None],ledger.shape)):
        raise ValueError('Ledger must contain every item exactly once')
    if raw.shape!=(2,n,repeats) or raw.dtype.kind not in 'iu' or np.any((raw<0)|(raw>n)):
        raise ValueError('Integer raw interval trace required')
    return y.astype(np.int64),ledger.astype(int),raw


def evaluate(outcomes,ledger,raw):
    y,ledger,raw=validate_inputs(outcomes,ledger,raw)
    n,repeats=ledger.shape
    wealth=np.full((2,repeats,n+1),Q,dtype=np.int64)
    alive=np.ones_like(wealth,dtype=bool)
    first=np.full((2,n+1,repeats),n+1,dtype=np.int16)
    counts=np.empty((2,2,n,repeats),dtype=np.int16)
    repair=np.empty((2,n,repeats),dtype=bool)
    holes=np.empty((2,n,repeats),dtype=np.int16)
    successes=np.zeros(repeats,dtype=np.int64)
    for t in range(1,n+1):
        obs=y[ledger[t-1]];r=n-t+1;d=t+1;u=successes[:,None]+1
        for method in range(2):
            active=np.flatnonzero(alive[method].any(axis=0))
            if len(active):
                left,right=int(active[0]),int(active[-1])+1
                a=np.arange(left,right)[None,:]-successes[:,None]
                old=alive[method,:,left:right]
                w=wealth[method,:,left:right]
                z0,z1=next_pair(w,a,r,u,d,bool(method))
                chosen=np.where(obs[:,None]==1,z1,z0)
                possible=(a>=0)&(a<=r)&np.where(obs[:,None]==1,a>0,a<r)
                new=old&possible&(chosen<B)
                f=first[method,left:right].T
                f[old&~new]=t
                alive[method,:,left:right]=new
                wealth[method,:,left:right]=np.where(new,chosen,0)
            lo,hi,empty,gaps=hull(alive[method])
            fallback=raw[:,t-1] if method==0 else counts[0,:,t-1]
            counts[method,0,t-1]=np.where(empty,fallback[0],lo)
            counts[method,1,t-1]=np.where(empty,fallback[1],hi)
            repair[method,t-1]=empty;holes[method,t-1]=gaps
        successes+=obs
    counts[:,:,-1]=successes[None,None,:]
    repair[:,-1]=False
    return dict(counts=counts,repaired=repair,rejection_time=first,holes=holes)
