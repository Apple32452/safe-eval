"""Small binary-grid joint CS. No WMT data, oracle leakage, or Gaussian boundary."""
from functools import lru_cache
from itertools import product
import numpy as np


@lru_cache(None)
def grid(n, m):
    k = np.array(list(product(range(n+1), repeat=m)), dtype=np.int64)
    k.setflags(write=False)
    return k


def row_weights(history, observed, remaining, adaptive):
    if not adaptive:
        return np.ones(len(remaining), dtype=np.int64)
    center = (np.sum(observed, axis=0)+.5)/(len(observed)+1) if len(observed) else np.full(history.shape[1], .5)
    return 1+np.floor(8*np.mean(np.abs(history[remaining]-center), axis=1)).astype(np.int64)


def direction(k, n, observed, covariance=True):
    m = k.shape[1]
    x = np.asarray(observed, dtype=float).reshape(-1, m)
    center = (x.sum(axis=0)+.5)/(len(x)+1)
    cov = np.zeros((m, m)) if len(x)<2 else (x-x.mean(axis=0)).T@(x-x.mean(axis=0))/len(x)
    if not covariance:
        cov = np.diag(np.diag(cov))
    inverse = np.linalg.inv(cov+np.eye(m)*.25)
    return np.sign((center-k/n)@inverse).astype(np.int64)


def factor_integers(k, sums, directions, weights, chosen_weight, y):
    wmin, total = int(np.min(weights)), int(np.sum(weights))
    dsum = np.sum(directions*(sums-k), axis=1)
    negative = np.minimum(directions, 0).sum(axis=1)
    bound = np.maximum(wmin, -wmin*dsum-total*negative)
    denominator = 2*bound*int(chosen_weight)
    numerator = denominator+wmin*(int(chosen_weight)*dsum+total*(directions@y))
    assert (numerator>0).all() and max(int(numerator.max()), int(denominator.max())) < 2**53
    return numerator, denominator


def conservative_update(wealth, numerator, denominator):
    factor = np.nextafter(numerator.astype(float)/denominator, -np.inf)
    updated = np.maximum(0, np.nextafter(wealth*factor, -np.inf))
    if not np.isfinite(updated).all():
        raise FloatingPointError('Capital overflow')
    return updated


def project(k, edges):
    result = np.full(len(edges), 2, dtype=np.int8)
    if not len(k):
        return result
    for e, (a, b) in enumerate(edges):
        difference = k[:, a]-k[:, b]
        if np.all(difference>0): result[e] = 1
        elif np.all(difference<0): result[e] = -1
        elif np.all(difference==0): result[e] = 0
    return result


def run(n, m, oracle, history, uniforms, edges, covariance=True, adaptive=False, hook=None):
    history = np.asarray(history, dtype=float)
    if history.shape != (n, m) or not np.isfinite(history).all():
        raise ValueError('Fixed auxiliary row features required')
    k = grid(n, m)
    wealth = np.ones(len(k)); alive = np.ones(len(k), dtype=bool)
    sums = np.zeros(m, dtype=np.int64)
    remaining = list(range(n)); observed = []; queried = []
    decisions = np.full(len(edges), 2, dtype=np.int8)
    resolution = np.full(len(edges), -1, dtype=int)
    confidence_masks = []
    for t in range(n):
        weights = row_weights(history, observed, remaining, adaptive)
        cdf = np.cumsum(weights)/weights.sum(); cdf[-1] = 1.
        index = min(int(np.searchsorted(cdf, uniforms[t], side='right')), len(remaining)-1)
        item = remaining[index]
        active = np.flatnonzero(alive)
        d = direction(k[active], n, observed, covariance)
        if hook:
            hook(t, item, dict(weights=weights.copy(), direction=d.copy(), sums=sums.copy(), remaining=remaining.copy()))
        y = np.asarray(oracle(item))
        if y.shape != (m,) or not np.isin(y, (0, 1)).all():
            raise ValueError('Exact binary row oracle required')
        y = y.astype(np.int64)
        if len(active):
            numerator, denominator = factor_integers(k[active], sums, d, weights, weights[index], y)
            wealth[active] = conservative_update(wealth[active], numerator, denominator)
            alive[active] &= wealth[active] < 20.
        sums += y
        remaining.pop(index); queried.append(item); observed.append(y.copy())
        alive &= ((k>=sums)&(k<=sums+len(remaining))).all(axis=1)
        confidence_masks.append(np.packbits(alive))
        proposed = project(k[alive], edges)
        newly = (decisions==2)&(proposed!=2)
        decisions[newly] = proposed[newly]; resolution[newly] = (t+1)*m
        if t == n-1:
            # Deterministic full-population answer, including earlier statistical failure.
            newly = decisions==2
            decisions[newly] = np.sign(sums[edges[newly, 0]]-sums[edges[newly, 1]])
            resolution[newly] = n*m
        if (decisions!=2).all(): break
    return dict(cost=len(queried)*m, decisions=decisions, resolution=resolution,
                queried=np.array(queried), masks=np.stack(confidence_masks))


def uniform_path(uniforms, n):
    remaining = list(range(n)); path = []
    for u in uniforms[:n]:
        index = min(int(u*len(remaining)), len(remaining)-1)
        path.append(remaining.pop(index))
    return np.array(path, dtype=np.int32)
