"""Exact-rational binary pilot; known joint evidence, not a novelty claim."""
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from math import comb
import numpy as np

MODES = ('hedge', 'product', 'mixture', 'peak')


@lru_cache(None)
def totals_grid(n, m): return np.array(list(product(range(n+1), repeat=m)), dtype=np.int16)


@lru_cache(None)
def ppr(n, observed, successes, total):
    if total<successes or n-total<observed-successes: return F(0)
    return F(comb(n, observed), (observed+1)*comb(total, successes)*comb(n-total, observed-successes))


def signs(k, edges):
    answer = np.full(len(edges), 2, dtype=np.int8)
    if not len(k): return answer
    for e, (a, b) in enumerate(edges):
        d = k[:, a]-k[:, b]
        if (d>0).all(): answer[e] = 1
        elif (d<0).all(): answer[e] = -1
        elif (d==0).all(): answer[e] = 0
    return answer


def choose_system(counts, edges, decisions, anchor, allocation):
    active = edges[decisions==2]
    degree = np.bincount(active.ravel(), minlength=len(counts))
    eligible = np.flatnonzero((degree>0)&(counts>0))
    if not len(eligible): return None
    if allocation=='anchor' and anchor in eligible: return int(anchor)
    priority = degree*counts if allocation=='anchor' else counts
    return int(max(eligible, key=lambda v:(int(priority[v]), -int(v))))


def run(n, m, oracle, edges, uniforms, mode='hedge', allocation='anchor', hook=None):
    if mode not in MODES or allocation not in ('anchor', 'round_robin'): raise ValueError('Unknown method')
    edges = np.asarray(edges, dtype=int)
    k = totals_grid(n,m); alive = np.ones(len(k), dtype=bool)
    seen = np.zeros(m,dtype=int); sums = np.zeros(m,dtype=int)
    remaining = [list(range(n)) for _ in range(m)]
    peak = [[F(1) for _ in range(n+1)] for _ in range(m)]
    degree = np.bincount(edges.ravel(), minlength=m); anchor = int(np.argmax(degree))
    decisions = np.full(len(edges),2,dtype=np.int8); resolution = np.full(len(edges),-1,dtype=int)
    acquired, masks, timeline = [], [], []
    for t in range(n*m):
        v = choose_system(n-seen, edges, decisions, anchor, allocation)
        if v is None: break
        j = min(int(uniforms[v, seen[v]]*len(remaining[v])), len(remaining[v])-1)
        item = remaining[v][j]
        if hook: hook(t,v,item,dict(seen=seen.copy(), sums=sums.copy(), decisions=decisions.copy()))
        y = oracle(v,item)
        if y not in (0,1): raise ValueError('Binary score required')
        y = int(y)
        if mode=='peak':
            for total in range(n+1):
                center = F(total-int(sums[v]), n-int(seen[v]))
                if 0<=center<=1:
                    estimate = F(int(sums[v]),int(seen[v])) if seen[v] else center
                    factor = 1+(estimate-center)*(y-center)/F(13,50)
                    assert factor>=F(1,26)
                    peak[v][total] *= factor
                else: peak[v][total] = F(0)
        seen[v]+=1; sums[v]+=y; remaining[v].pop(j); acquired.append((v,item))
        alive &= ((k>=sums)&(k<=sums+n-seen)).all(axis=1)
        capitals = peak if mode=='peak' else [[ppr(n,int(seen[a]),int(sums[a]),total) for total in range(n+1)] for a in range(m)]
        for index in np.flatnonzero(alive):
            parts = [capitals[a][int(k[index,a])] for a in range(m)]
            mixture = sum(parts,F(0))/m
            if mode in ('mixture','peak'): evidence = mixture
            else:
                joint = F(1)
                for value in parts: joint *= value
                evidence = joint if mode=='product' else (joint+mixture)/2
            if evidence>=20: alive[index] = False
        proposed = signs(k[alive],edges)
        new = (decisions==2)&(proposed!=2)
        decisions[new] = proposed[new]; resolution[new] = t+1
        # Exact populations may be reported even after a statistical exclusion.
        exact = (decisions==2)&(seen[edges[:,0]]==n)&(seen[edges[:,1]]==n)
        decisions[exact] = np.sign(sums[edges[exact,0]]-sums[edges[exact,1]])
        resolution[exact] = t+1
        masks.append(np.packbits(alive)); timeline.append(decisions.copy())
        if (decisions!=2).all(): break
    if (decisions==2).any(): raise AssertionError('Unresolved despite no eligible labels')
    assert len(acquired)==len(set(acquired))
    return dict(cost=len(acquired), decisions=decisions, resolution=resolution,
                acquired=np.array(acquired,dtype=np.int16), masks=np.stack(masks), timeline=np.stack(timeline))
