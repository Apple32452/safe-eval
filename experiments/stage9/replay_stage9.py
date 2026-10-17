"""Independent backward risk counting and replay from saved query ledgers.

Does not call the experiment engine. Shares the tested outward-arithmetic
primitives and historical feature routine, not engine state or decisions.
"""
from fractions import Fraction
import math
import numpy as np
from certify_stage9 import pointwise_intervals, exact_risk
from rounded_betting import (ratio_bounds,prediction_bounds,stakes,lower_factors,
                             ScaledCapital,average_crossed)
from safe_eval_v1 import reference_features
from binary_control import ppr_interval


def binomial_rows(n):
    rows=[[1]]
    for _ in range(n):
        old=rows[-1]
        rows.append([1]+[old[i-1]+old[i] for i in range(1,len(old))]+[1])
    return rows


def backward_failures(table,k,choose):
    n=len(table)-1;fmax=n-k
    lower=table[:,:,0].tolist();upper=table[:,:,1].tolist()
    future=[0]*(fmax+2)
    for s in range(k,-1,-1):
        row=[0]*(fmax+2)
        for f in range(fmax,-1,-1):
            t=s+f
            if not lower[t][s]<=k<=upper[t][s]:
                row[f]=choose[n-t][k-s]
            else:
                row[f]=(future[f] if s<k else 0)+(row[f+1] if f<fmax else 0)
        future=row
    return future[0]


def audit_certificate(record,raw,calibrated):
    n=record["n"];choose=binomial_rows(n)
    checked=0
    for name,table in (("raw",raw),("calibrated",calibrated)):
        expected=record[name]
        symmetric=all(table[t,s,0]==n-table[t,t-s,1] and table[t,s,1]==n-table[t,t-s,0]
                      for t in range(n+1) for s in range(t+1))
        risks=[]
        for k in range(n//2+1 if symmetric else n+1):
            failed=backward_failures(table,k,choose)
            total=choose[n][k]
            if str(total-failed)!=expected["surviving_strings"][k]:
                raise ValueError("Backward risk count differs from certificate")
            if symmetric and str(total-failed)!=expected["surviving_strings"][n-k]:
                raise ValueError("Mirrored certificate count differs")
            risks.append(Fraction(failed,total));checked+=1
        if max(risks)!=exact_risk(expected):
            raise ValueError("Worst certified risk differs")
    h=record["calibrated"]["threshold"]
    if h>2:
        previous=record["evaluated_thresholds"][str(h-1)]
        k=previous["worst_k"][0]
        unsafe=pointwise_intervals(n,h-1)
        risk=Fraction(backward_failures(unsafe,k,choose),choose[n][k])
        if risk<=Fraction(1,20):
            raise ValueError("Minimal integer calibration threshold not certified")
        checked+=1
    alpha=Fraction(record["prediction_error_numerator"],record["prediction_error_denominator"])
    spare=Fraction(1,20)-exact_risk(record["raw"])
    expected=Fraction(spare.numerator*1_000_000//spare.denominator,1_000_000)
    if alpha!=expected:
        raise ValueError("Prediction error allocation differs from fixed rounding rule")
    return checked


def replay(case,history,outcomes,trace,calibrated,alpha):
    ledger=np.asarray(trace["selected"])
    n,repeats=ledger.shape
    if not np.array_equal(np.sort(ledger,axis=0),np.broadcast_to(np.arange(n)[:,None],(n,repeats))):
        raise ValueError("Query ledger is not a unique full permutation")
    mean,features,_=reference_features(history)
    d=features.shape[1];rows=np.arange(repeats)
    a=np.broadcast_to(np.diag([.25]+[1.]*(d-1)),(repeats,d,d)).copy()
    b=np.zeros((repeats,d));s=np.zeros(repeats,dtype=int)
    unseen=np.ones((repeats,n),dtype=bool)
    xx,xy,xsum,ysum=(np.zeros(repeats) for _ in range(4))
    means=np.zeros((2,repeats));variances=means.copy()
    qlo,qhi=ratio_bounds(np.arange(n+1),n)
    plus=[ScaledCapital((repeats,n+1)) for _ in range(2)]
    minus=[ScaledCapital((repeats,n+1)) for _ in range(2)]
    candidates=np.ones((2,repeats,n+1),dtype=bool)
    lo_raw=np.zeros(repeats,dtype=int);hi_raw=np.full(repeats,n,dtype=int)
    lo_cal=lo_raw.copy();hi_cal=hi_raw.copy()
    rng=np.random.default_rng(case["raw_seed"])
    for t in range(1,n+1):
        old=t-1;r=n-t+1
        slope=np.full(repeats,.5)
        if old:
            cov=xy-xsum*ysum/old
            slope=np.clip((.125+cov)/(.25+np.maximum(0,xx-xsum*xsum/old)),0,.5)
        coefficients=np.linalg.solve(a,b[...,None])[...,0]
        forecast=np.clip(mean+coefficients@features.T,0,1)
        mu=.5+slope[:,None]*(forecast-.5)
        eta=np.minimum(100,.05/((.25+variances)/t+.05**2))
        support_lo,support_hi,central=prediction_bounds(s,unseen,mu,None,None)
        cdf=np.cumsum(unseen/r,axis=1);cdf[:,-1]=1.
        expected=np.sum(cdf<=rng.random(repeats)[:,None],axis=1)
        indices=ledger[t-1]
        if not np.array_equal(expected,indices):
            raise ValueError("Saved ledger differs from fixed seeded query stream")
        y=np.asarray(outcomes[indices],dtype=np.float64)
        pl,pu=prediction_bounds(s,unseen,mu,indices,y)
        zl,zu=ratio_bounds(s+r*y,n)
        raw_support_lo=ratio_bounds(s,n)[0]
        raw_support_hi=ratio_bounds(s+r,n)[1]
        scalars=np.stack([np.stack([raw_support_lo,raw_support_hi,zl,zu,eta[0]]),
                          np.stack([support_lo,support_hi,pl,pu,eta[1]])])
        if not np.array_equal(scalars,trace["scalar_enclosures"][t-1]):
            raise ValueError("Saved prediction/support/stake scalars differ from historical replay")
        for j in range(2):
            al,au,lower,upper,bet=scalars[j]
            lp,lm=stakes(al,au,qlo,qhi,bet)
            fp,fm=lower_factors(lower,upper,qlo,qhi,lp,lm)
            plus[j].update(fp);minus[j].update(fm)
            candidates[j] &= ~average_crossed(plus[j],minus[j],alpha)
        xi=features[indices]
        a+=xi[:,:,None]*xi[:,None,:]
        b+=xi*(y-mean[indices])[:,None]
        score=forecast[rows,indices]
        xsum+=score;xx+=score**2;xy+=score*y;ysum+=y
        corrected=np.stack([s/n+r/n*y,central+r/n*(y-mu[rows,indices])])
        change=corrected-means
        means+=change/t;variances+=change*(corrected-means)
        s+=y.astype(int);unseen[rows,indices]=False
        lower,upper=ppr_interval(s,t,n)
        lo_raw=np.maximum(lo_raw,np.rint(lower*n).astype(int))
        hi_raw=np.minimum(hi_raw,np.rint(upper*n).astype(int))
        empty=lo_raw>hi_raw
        rl=np.where(empty,n,lo_raw);ru=np.where(empty,0,hi_raw)
        lo_cal=np.maximum(lo_cal,calibrated[t,s,0]);hi_cal=np.minimum(hi_cal,calibrated[t,s,1])
        flags=[lo_cal>hi_cal]
        intervals=[(rl,ru),(np.where(flags[0],rl,lo_cal),np.where(flags[0],ru,hi_cal))]
        counts=np.arange(n+1)[None,:]
        for j in range(2):
            mask=candidates[j]&(counts>=lo_raw[:,None])&(counts<=hi_raw[:,None])
            lo=np.min(np.where(mask,counts,n),axis=1);hi=np.max(np.where(mask,counts,0),axis=1)
            flags.append(lo>hi)
            intervals.append((np.where(flags[-1],rl,lo),np.where(flags[-1],ru,hi)))
        actual=np.stack([np.stack(v) for v in intervals])
        flags=np.stack(flags)
        if t==n:
            actual[:]=s[None,None,:];flags[:]=False
        if not np.array_equal(actual,trace["counts"][:,:,t-1]):
            raise ValueError("Replayed capital or raw interval differs")
        if not np.array_equal(flags,trace["repaired"][:,t-1]):
            raise ValueError("Replayed fallback flags differ")
    return n*repeats
