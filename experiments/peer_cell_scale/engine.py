"""Peer-informed finite-matrix acquisition with predictable null calibration."""
from __future__ import annotations

from functools import lru_cache
from itertools import product

import numpy as np
from scipy.optimize import minimize

ALPHA = .05
CELL_METHODS = ('peer_cell', 'row_peer', 'no_peer', 'ec2_weighted')


def edges_for(k, graph):
    return tuple((0,b) for b in range(1,k)) if graph == 'star' else tuple(
        (a,b) for a in range(k) for b in range(a+1,k))


class ColumnModel:
    """A small historical categorical model; never receives target outcomes."""
    def __init__(self, history):
        history = np.asarray(history, dtype=int)
        self.k = history.shape[0]
        self.patterns = np.array(list(product((0,1),repeat=self.k)), dtype=int)
        code = (history.T * 2**np.arange(self.k-1,-1,-1)).sum(axis=1)
        self.prob = (np.bincount(code,minlength=2**self.k)+.5)/(history.shape[1]+.5*2**self.k)
        self.marginal = self.prob @ self.patterns
        self.states = np.array(list(product((-1,0,1),repeat=self.k)), dtype=int)
        self.posterior = []
        for state in self.states:
            compatible = np.all((state == -1) | (self.patterns == state),axis=1)
            mass = self.prob*compatible
            self.posterior.append(mass/mass.sum())
        self.posterior = np.array(self.posterior)
        self.predictions = np.clip(self.posterior @ self.patterns,.02,.98)
        self.ternary = 3**np.arange(self.k-1,-1,-1)

    def codes(self, observed):
        return ((observed.T+1)*self.ternary).sum(axis=1)

    def predict(self, observed, peer=True):
        if peer: return self.predictions[self.codes(observed)].T
        return np.broadcast_to(np.clip(self.marginal,.02,.98)[:,None], observed.shape).copy()

    def particles(self, observed, rng, count=256):
        codes = self.codes(observed)
        samples = np.empty((count,self.k,observed.shape[1]),dtype=np.int8)
        for code in np.unique(codes):
            items = np.flatnonzero(codes==code)
            values = rng.choice(len(self.prob),size=(count,len(items)),p=self.posterior[code])
            samples[:,:,items] = self.patterns[values].transpose(0,2,1)
        return samples


def ec2_gains(particles, edges):
    """Empirical expected cut of cross-class edges, with equal particle mass."""
    count = len(particles)
    totals = particles.sum(axis=2)
    signs = np.array([np.sign(totals[:,a]-totals[:,b]) for a,b in edges]).T
    _, classes = np.unique(signs,axis=0,return_inverse=True)
    values = particles.reshape(count,-1).astype(float)
    sizes = np.bincount(classes)
    full_weight = (count*count-float(sizes@sizes))/2
    remaining = np.zeros(values.shape[1])
    for outcome in (0,1):
        selected = values if outcome else 1-values
        totals_y = selected.sum(axis=0)
        class_counts = np.zeros((len(sizes),values.shape[1]))
        np.add.at(class_counts,classes,selected)
        weight = (totals_y**2-(class_counts**2).sum(axis=0))/2
        remaining += totals_y/count*weight
    return np.maximum(0.,full_weight-remaining).reshape(particles.shape[1:])


def proposal(observed, predicted, edges, decisions, method, model=None, particle_rng=None):
    k,n = observed.shape
    unresolved = [edge for edge,d in zip(edges,decisions) if d==2]
    active = np.zeros(k,bool)
    for a,b in unresolved: active[a]=active[b]=True
    eligible = (observed<0)&active[:,None]
    if not eligible.any(): raise AssertionError('No eligible unresolved cell')
    totals = np.where(observed<0,predicted,observed).sum(axis=1)
    urgency = np.zeros(k)
    for a,b in unresolved:
        w=1/max(abs(totals[a]-totals[b])/n,.1)
        urgency[a]+=w; urgency[b]+=w
    if method=='ec2_weighted':
        weight = ec2_gains(model.particles(observed,particle_rng),unresolved)*eligible
    else:
        weight = urgency[:,None]*np.sqrt(predicted*(1-predicted))*eligible
    if weight.sum()<=0: weight=eligible.astype(float)
    q=.2*eligible/eligible.sum()+.8*weight/weight.sum()
    if method=='row_peer':
        mass=q.sum(axis=1)
        q=np.divide(mass[:,None]*eligible,eligible.sum(axis=1)[:,None],
                    out=np.zeros_like(q),where=eligible.sum(axis=1)[:,None]>0)
    q/=q.sum()
    if np.any(q[eligible]<=0) or np.any(q[~eligible]!=0):
        raise AssertionError('Missing overlap or purchase of an observed cell')
    return q


def row_best(q, factors):
    """Maximum weighted factor for each possible number of remaining ones."""
    zero=q*factors[:,0]; one=q*factors[:,1]
    order=np.argsort(-(one-zero),kind='stable')
    zero,one=zero[order],one[order]
    # Summing nonnegative terms avoids subtracting huge likelihood ratios.
    suffix=np.r_[np.cumsum(zero[::-1])[::-1],0.]
    return np.r_[0.,np.cumsum(one)]+suffix


def null_peak(observed, q, factors, a, b):
    """Exact combinatorial maximum over the directional binary null."""
    unknown=observed<0
    difference=int(np.maximum(observed[a],0).sum()-np.maximum(observed[b],0).sum())
    qa,qb=q[a,unknown[a]],q[b,unknown[b]]
    va=row_best(qa,factors[a,unknown[a]])
    vb=row_best(qb,factors[b,unknown[b]])
    if difference>len(qb): return None
    suffix=np.maximum.accumulate(vb[::-1])[::-1]
    counts=np.arange(len(va))
    minimum_b=np.maximum(0,difference+counts)
    good=minimum_b<len(vb)
    value=float(np.max(va[good]+suffix[minimum_b[good]]))
    for v in range(observed.shape[0]):
        if v not in (a,b):
            value+=float(np.sum(q[v,unknown[v]]*np.max(factors[v,unknown[v]],axis=1)))
    return value


def projected_probabilities(ra, rb, qa, qb, difference):
    """Scalar KKT solve for min sum q*KL(r||z) subject to the pair null."""
    def shrink(r,t):
        return 2*r/(1+t+np.sqrt((1+t)**2-4*t*r))
    def at(lam):
        return shrink(ra,lam/qa),1-shrink(1-rb,lam/qb)
    if difference==len(rb): return np.zeros_like(ra),np.ones_like(rb)
    low,high=0.,1.
    for _ in range(60):
        za,zb=at(high)
        if difference+za.sum()-zb.sum()<=0: break
        high*=2
    for _ in range(45):
        mid=(low+high)/2; za,zb=at(mid)
        if difference+za.sum()-zb.sum()>0: low=mid
        else: high=mid
    return at(high)


def pair_factor(observed, predicted, q, a, b):
    unknown=observed<0
    difference=int(np.maximum(observed[a],0).sum()-np.maximum(observed[b],0).sum())
    ra,rb=predicted[a,unknown[a]],predicted[b,unknown[b]]
    factors=np.ones(observed.shape+(2,))
    if difference>len(rb): return factors,1.
    if difference+ra.sum()-rb.sum()<=0: return factors,1.
    qa,qb=q[a,unknown[a]],q[b,unknown[b]]
    if np.any(qa<=0) or np.any(qb<=0): raise AssertionError('Unresolved endpoint has zero probability')
    za,zb=projected_probabilities(ra,rb,qa,qb,difference)
    for v,r,z in ((a,ra,za),(b,rb,zb)):
        z=np.clip(z,1e-10,1-1e-10)
        factors[v,unknown[v],0]=(1-r)/(1-z)
        factors[v,unknown[v],1]=r/z
    peak=null_peak(observed,q,factors,a,b)
    factors/=max(1.,peak)*(1+1e-9)
    verified=null_peak(observed,q,factors,a,b)
    if not np.isfinite(factors).all() or factors.min()<=0 or verified>1+1e-12:
        raise AssertionError('Uncertified directional factor')
    return factors,float(verified)


def exact_decisions(observed, edges, decisions):
    sums=np.maximum(observed,0).sum(axis=1)
    remaining=(observed<0).sum(axis=1)
    answer=decisions.copy()
    for e,(a,b) in enumerate(edges):
        if answer[e]!=2: continue
        if sums[a]>sums[b]+remaining[b]: answer[e]=1
        elif sums[a]+remaining[a]<sums[b]: answer[e]=-1
        elif remaining[a]==remaining[b]==0: answer[e]=np.sign(sums[a]-sums[b])
    return answer


def after_evidence(observed,edges,decisions,logs,alpha=ALPHA):
    decisions=exact_decisions(observed,edges,decisions)
    threshold=np.log(2*len(edges)/alpha)
    for e in range(len(edges)):
        if decisions[e]!=2: continue
        plus,minus=logs[e]>=threshold
        if plus!=minus: decisions[e]=1 if plus else -1
    return decisions


def finish(scores,edges,decisions,paid,trace):
    truth=np.array([np.sign(scores[a].sum()-scores[b].sum()) for a,b in edges])
    wrong=int(np.any(decisions!=truth))
    if np.any(decisions==2): raise AssertionError('Unfinished comparison')
    return dict(paid=int(paid),charged=int(scores.size if wrong else paid),wrong=wrong,
                decisions=decisions.tolist(),trace=trace)


def run_cells(scores,model,edges,method,seed,particle_seed):
    if method not in CELL_METHODS: raise ValueError('Unknown cell method')
    observed=np.full_like(scores,-1)
    decisions=np.full(len(edges),2,int)
    logs=np.zeros((len(edges),2))
    rng=np.random.default_rng(seed); particle_rng=np.random.default_rng(particle_seed)
    trace=[]
    for t in range(scores.size):
        predicted=model.predict(observed,peer=method!='no_peer')
        q=proposal(observed,predicted,edges,decisions,method,model,particle_rng)
        # All factors are set before selecting or reading the next score.
        updates={}
        for e,(a,b) in enumerate(edges):
            if decisions[e]!=2: continue
            updates[e]=[pair_factor(observed,predicted,q,a,b),
                        pair_factor(observed,predicted,q,b,a)]
        cell=int(rng.choice(scores.size,p=q.ravel()))
        v,item=divmod(cell,scores.shape[1]); value=int(scores[v,item])
        if observed[v,item]!=-1: raise AssertionError('Repurchased a score')
        increments=np.zeros_like(logs)
        peak=0.
        for e, fits in updates.items():
            for direction,(factor,bound) in enumerate(fits):
                increments[e,direction]=np.log(factor[v,item,value]); peak=max(peak,bound)
        logs+=increments; observed[v,item]=value
        decisions=after_evidence(observed,edges,decisions,logs)
        trace.append(dict(cell=cell,value=value,q=float(q[v,item]),
                          increments=increments.tolist(),peak=float(peak),decisions=decisions.tolist()))
        if np.all(decisions!=2): return finish(scores,edges,decisions,t+1,trace)
    raise AssertionError('Full-pool fallback did not finish')


@lru_cache(maxsize=50000)
def paired_vertices(difference,remaining):
    """Vertices covering every integer ternary histogram under the null."""
    if difference>remaining: return np.empty((0,3))
    bound=-difference
    low=max(0,-bound)
    crossing=(remaining-bound)/2
    counts={low,remaining,int(np.floor(crossing)),int(np.ceil(crossing))}
    points=[]
    for minus in sorted(counts):
        if not low<=minus<=remaining: continue
        cap=min(remaining-minus,bound+minus)
        for plus in {0,cap}:
            if 0<=plus<=remaining-minus:
                points.append((minus,remaining-minus-plus,plus))
    return np.unique(np.asarray(points,float),axis=0)/remaining


@lru_cache(maxsize=50000)
def paired_factor(counts_tuple,prior_tuple,n):
    counts=np.array(counts_tuple); m=n-int(counts.sum())
    if m<=0: raise ValueError('No remaining pair')
    rows=paired_vertices(int(counts[2]-counts[0]),m)
    if not len(rows): return np.ones(3)
    predicted=(counts+4*np.array(prior_tuple))/(counts.sum()+4)
    result=minimize(lambda f:-float(predicted@np.log(f)),np.ones(3),
        jac=lambda f:-predicted/f,method='SLSQP',bounds=[(.001,10000)]*3,
        constraints=[{'type':'ineq','fun':lambda f:1-rows@f,'jac':lambda f:-rows}],
        options={'ftol':1e-10,'maxiter':500})
    f=result.x
    if not np.isfinite(f).all() or np.any(f<=0): return np.ones(3)
    f=f/(max(1.,float(np.max(rows@f)))*(1+1e-9))
    if float(predicted@np.log(f))<0: return np.ones(3)
    if np.max(rows@f)>1+1e-12: raise AssertionError('Invalid paired factor')
    return f


def run_paired(scores,model,edges,order):
    observed=np.full_like(scores,-1); n=scores.shape[1]
    counts=np.zeros((len(edges),2,3),int); logs=np.zeros((len(edges),2))
    decisions=np.full(len(edges),2,int); paid=0; trace=[]
    priors={}
    for e,(a,b) in enumerate(edges):
        d=model.patterns[:,a]-model.patterns[:,b]
        priors[e]=tuple(float(model.prob[d==value].sum()) for value in (-1,0,1))
    for item in order:
        unresolved=np.flatnonzero(decisions==2)
        active=sorted({v for e in unresolved for v in edges[e]})
        fits={e:[paired_factor(tuple(counts[e,0]),priors[e],n),
                 paired_factor(tuple(counts[e,1]),tuple(reversed(priors[e])),n)] for e in unresolved}
        values={v:int(scores[v,item]) for v in active}
        increments=np.zeros_like(logs)
        for e in unresolved:
            a,b=edges[e]; d=values[a]-values[b]
            for direction,event in enumerate((d+1,1-d)):
                increments[e,direction]=np.log(fits[e][direction][event])
                counts[e,direction,event]+=1
        logs+=increments
        for v,value in values.items():
            if observed[v,item]!=-1: raise AssertionError('Repeated paired purchase')
            observed[v,item]=value; paid+=1
        decisions=after_evidence(observed,edges,decisions,logs)
        trace.append(dict(item=int(item),active=active,values=[values[v] for v in active],
                          increments=increments.tolist(),decisions=decisions.tolist()))
        if np.all(decisions!=2): return finish(scores,edges,decisions,paid,trace)
    raise AssertionError('Paired policy did not complete')
