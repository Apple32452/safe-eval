"""Raw95 intersections using certified spare error and conservative capital."""
from __future__ import annotations
from fractions import Fraction
import sys
from pathlib import Path
import numpy as np
from rounded_betting import (ratio_bounds, prediction_bounds, stakes,
                             lower_factors, ScaledCapital, average_crossed)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage7"))
from safe_eval_v1 import reference_features

METHODS = ("raw95", "calibrated_raw95", "budget_zero95", "budget_prediction95")


def hull(mask):
    k = np.arange(mask.shape[1])
    n = len(k)-1
    lo = np.min(np.where(mask, k, n), axis=1)
    hi = np.max(np.where(mask, k, 0), axis=1)
    return lo, hi


def evaluate(history, oracle, repeats, seed, raw_table, calibrated_table,
             alpha, forced_ledger=None, prequery_hook=None):
    history = np.asarray(history, dtype=np.float64)
    if history.ndim != 2 or min(history.shape) < 2 or not np.isfinite(history).all() or np.any((history<0)|(history>1)):
        raise ValueError("Finite bounded historical matrix required")
    n, rows = history.shape[1], np.arange(repeats)
    if raw_table.shape != (n+1,n+1,2) or calibrated_table.shape != raw_table.shape:
        raise ValueError("Wrong certificate state dimensions")
    mean, x, _ = reference_features(history)
    d = x.shape[1]
    unseen = np.ones((repeats,n), dtype=bool)
    successes = np.zeros(repeats, dtype=int)
    ridge = np.broadcast_to(np.diag([.25]+[1.]*(d-1)), (repeats,d,d)).copy()
    b = np.zeros((repeats,d))
    sx,sxx,sxy,sy = (np.zeros(repeats) for _ in range(4))
    zmean = np.zeros((2,repeats)); m2 = zmean.copy()
    qlo,qhi = ratio_bounds(np.arange(n+1),n)
    capitals = [(ScaledCapital((repeats,n+1)),ScaledCapital((repeats,n+1))) for _ in range(2)]
    accepted = np.ones((2,repeats,n+1),dtype=bool)
    raw_lo, raw_hi = np.zeros(repeats,dtype=int),np.full(repeats,n,dtype=int)
    cal_lo, cal_hi = raw_lo.copy(),raw_hi.copy()
    curves=np.empty((len(METHODS),2,n,repeats),dtype=np.int16)
    repaired=np.zeros((3,n,repeats),dtype=bool)
    ledger=np.empty((n,repeats),dtype=np.int16)
    scalar_enclosures=np.empty((n,2,5,repeats),dtype=np.float64)
    rng=np.random.default_rng(seed)
    for t in range(1,n+1):
        count,remaining=t-1,n-t+1
        strength=np.full(repeats,.5)
        if count:
            spread=np.maximum(0,sxx-sx*sx/count)
            covariance=sxy-sx*sy/count
            strength=np.clip((.125+covariance)/(.25+spread),0,.5)
        beta=np.linalg.solve(ridge,b[...,None])[...,0]
        full=np.clip(mean+beta@x.T,0,1)
        mu=.5+strength[:,None]*(full-.5)
        plo,phi,base=prediction_bounds(successes,unseen,mu,None,None)
        zlo0,zhi0=ratio_bounds(successes,n)
        top0=ratio_bounds(successes+remaining,n)[1]
        eta=np.minimum(100,.05/((.25+m2)/t+.05**2))
        lambdas=[stakes(zlo0,top0,qlo,qhi,eta[0]),
                 stakes(plo,phi,qlo,qhi,eta[1])]
        if forced_ledger is None:
            cdf=np.cumsum(unseen/remaining,axis=1)
            cdf[:,-1]=1.
            indices=np.sum(cdf<=rng.random(repeats)[:,None],axis=1)
        else:
            indices=np.asarray(forced_ledger[t-1],dtype=int)
        if not unseen[rows,indices].all():
            raise ValueError("Repeated query")
        if prequery_hook:
            prequery_hook(t,indices,dict(mu=mu.copy(),eta=eta.copy(),
                          support=np.stack([plo,phi]),lambdas=lambdas))
        y=np.asarray(oracle(indices))
        if y.shape!=(repeats,) or np.any((y!=0)&(y!=1)):
            raise ValueError("Exact binary outcomes required")
        pred_zlo,pred_zhi=prediction_bounds(successes,unseen,mu,indices,y)
        zero_zlo,zero_zhi=ratio_bounds(successes+remaining*y.astype(int),n)
        scalar_enclosures[t-1,0]=np.stack([zlo0,top0,zero_zlo,zero_zhi,eta[0]])
        scalar_enclosures[t-1,1]=np.stack([plo,phi,pred_zlo,pred_zhi,eta[1]])
        for j,(lo,hi) in enumerate(((zero_zlo,zero_zhi),(pred_zlo,pred_zhi))):
            fp,fm=lower_factors(lo,hi,qlo,qhi,*lambdas[j])
            capitals[j][0].update(fp);capitals[j][1].update(fm)
            accepted[j] &= ~average_crossed(*capitals[j],alpha)
        # All predictor and stake updates follow the current label.
        xi=x[indices]
        ridge+=xi[:,:,None]*xi[:,None,:]
        b+=xi*(y-mean[indices])[:,None]
        score=full[rows,indices]
        sx+=score;sxx+=score**2;sxy+=score*y;sy+=y
        approx=np.stack([successes/n+remaining/n*y,
                         base+remaining/n*(y-mu[rows,indices])])
        diff=approx-zmean
        zmean+=diff/t;m2+=diff*(approx-zmean)
        successes+=y.astype(int)
        unseen[rows,indices]=False
        ledger[t-1]=indices
        raw_lo=np.maximum(raw_lo,raw_table[t,successes,0])
        raw_hi=np.minimum(raw_hi,raw_table[t,successes,1])
        cal_lo=np.maximum(cal_lo,calibrated_table[t,successes,0])
        cal_hi=np.minimum(cal_hi,calibrated_table[t,successes,1])
        raw_empty=raw_lo>raw_hi
        rlo=np.where(raw_empty,n,raw_lo)
        rhi=np.where(raw_empty,0,raw_hi)
        intervals=[(rlo,rhi)]
        empty=cal_lo>cal_hi
        repaired[0,t-1]=empty
        intervals.append((np.where(empty,rlo,cal_lo),np.where(empty,rhi,cal_hi)))
        k=np.arange(n+1)[None,:]
        raw_mask=(k>=raw_lo[:,None])&(k<=raw_hi[:,None])
        for j in range(2):
            lo,hi=hull(accepted[j]&raw_mask)
            empty=lo>hi
            repaired[j+1,t-1]=empty
            intervals.append((np.where(empty,rlo,lo),np.where(empty,rhi,hi)))
        for j,(lo,hi) in enumerate(intervals):
            if t==n:
                lo=successes;hi=successes
            curves[j,0,t-1]=lo;curves[j,1,t-1]=hi
        if t==n:
            repaired[:,t-1]=False
    raw=curves[0]
    for output in curves[1:]:
        nonempty=output[1]>=output[0]
        if np.any(nonempty&((output[0]<raw[0])|(output[1]>raw[1]))):
            raise AssertionError("Raw95 containment failed")
    return dict(counts=curves,selected=ledger,repaired=repaired,scalar_enclosures=scalar_enclosures)
