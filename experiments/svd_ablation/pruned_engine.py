"""Exact candidate pruning for Stage 9's budget_prediction95 output.

Raw95 exclusions are permanent. Wealth of a raw-excluded candidate cannot
affect this intersection or its raw fallback, so only surviving cells need
capital arithmetic. Every retained cell uses the original rounded operations.
"""
import numpy as np

from ablation import reference_features
from rounded_betting import (ratio_bounds, prediction_bounds, down, up,
                             ScaledCapital, average_crossed)
from stage9_engine import hull


def evaluate(history, oracle, repeats, seed, raw_table, calibrated_table, alpha,
             use_svd, prequery_hook=None):
    history = np.asarray(history, dtype=np.float64)
    n, rows = history.shape[1], np.arange(repeats)
    mean, x, _ = reference_features(history, rank=3 if use_svd else 0)
    d = x.shape[1]
    unseen = np.ones((repeats, n), dtype=bool)
    successes = np.zeros(repeats, dtype=int)
    ridge = np.broadcast_to(np.diag([.25]+[1.]*(d-1)), (repeats, d, d)).copy()
    b = np.zeros((repeats, d))
    sx, sxx, sxy, sy = (np.zeros(repeats) for _ in range(4))
    zmean, m2 = np.zeros(repeats), np.zeros(repeats)
    qlo, qhi = ratio_bounds(np.arange(n+1), n)
    plus, minus = ScaledCapital((repeats, n+1)), ScaledCapital((repeats, n+1))
    accepted = np.ones((repeats, n+1), dtype=bool)
    raw_lo, raw_hi = np.zeros(repeats, dtype=int), np.full(repeats, n, dtype=int)
    curves = np.empty((2, n, repeats), dtype=np.int16)
    ledger = np.empty((n, repeats), dtype=np.int16)
    repaired = np.zeros((n, repeats), dtype=bool)
    rng = np.random.default_rng(seed)
    for t in range(1, n+1):
        count, remaining = t-1, n-t+1
        strength = np.full(repeats, .5)
        if count:
            spread = np.maximum(0, sxx-sx*sx/count)
            covariance = sxy-sx*sy/count
            strength = np.clip((.125+covariance)/(.25+spread), 0, .5)
        beta = np.linalg.solve(ridge, b[..., None])[..., 0]
        full = np.clip(mean+beta@x.T, 0, 1)
        mu = .5+strength[:, None]*(full-.5)
        plo, phi, base = prediction_bounds(successes, unseen, mu, None, None)
        eta = np.minimum(100, .05/((.25+m2)/t+.05**2))
        cdf = np.cumsum(unseen/remaining, axis=1)
        cdf[:, -1] = 1.
        indices = np.sum(cdf <= rng.random(repeats)[:, None], axis=1)
        if not unseen[rows, indices].all():
            raise ValueError('Repeated query')
        if prequery_hook:
            prequery_hook(t, indices, dict(mu=mu.copy()))
        y = np.asarray(oracle(indices))
        if y.shape != (repeats,) or np.any((y != 0) & (y != 1)):
            raise ValueError('Exact binary outcomes required')
        zlo, zhi = prediction_bounds(successes, unseen, mu, indices, y)
        # Predictor updates use precisely the original order and arithmetic.
        xi = x[indices]
        ridge += xi[:, :, None]*xi[:, None, :]
        b += xi*(y-mean[indices])[:, None]
        score = full[rows, indices]
        sx += score; sxx += score**2; sxy += score*y; sy += y
        approx = base+remaining/n*(y-mu[rows, indices])
        diff = approx-zmean
        zmean += diff/t; m2 += diff*(approx-zmean)
        successes += y.astype(int)
        unseen[rows, indices] = False
        ledger[t-1] = indices
        raw_lo = np.maximum(raw_lo, raw_table[t, successes, 0])
        raw_hi = np.minimum(raw_hi, raw_table[t, successes, 1])
        k = np.arange(n+1)[None, :]
        accepted &= (k >= raw_lo[:, None]) & (k <= raw_hi[:, None])
        ri, ki = np.nonzero(accepted)
        if len(ri):
            # Each cell is independent, so pruning leaves its rounding unchanged.
            positive_distance = up(qhi[ki]-plo[ri])
            negative_distance = up(phi[ri]-qlo[ki])
            with np.errstate(over='ignore', divide='ignore'):
                ps = np.minimum(eta[ri], np.where(positive_distance > 0, down(.9/positive_distance), np.inf))
                ms = np.minimum(eta[ri], np.where(negative_distance > 0, down(.9/negative_distance), np.inf))
            fp = down(1+down(ps*down(zlo[ri]-qhi[ki])))
            fm = down(1-up(ms*up(zhi[ri]-qlo[ki])))
            if not np.isfinite(fp).all() or not np.isfinite(fm).all() or min(fp.min(), fm.min()) <= 0:
                raise ValueError('Invalid conservative factors')
            local_plus, local_minus = ScaledCapital((len(ri),)), ScaledCapital((len(ri),))
            for dense, local, factor in ((plus, local_plus, fp), (minus, local_minus, fm)):
                local.m, local.e = dense.m[ri, ki], dense.e[ri, ki]
                local.update(factor)
                dense.m[ri, ki], dense.e[ri, ki] = local.m, local.e
            accepted[ri, ki] &= ~average_crossed(local_plus, local_minus, alpha)
        lo, hi = hull(accepted)
        empty = lo > hi
        repaired[t-1] = empty
        raw_empty = raw_lo > raw_hi
        rlo, rhi = np.where(raw_empty, n, raw_lo), np.where(raw_empty, 0, raw_hi)
        lo, hi = np.where(empty, rlo, lo), np.where(empty, rhi, hi)
        if t == n:
            lo, hi = successes, successes
            repaired[t-1] = False
        curves[0, t-1], curves[1, t-1] = lo, hi
    return dict(prediction_counts=curves, selected=ledger, prediction_repaired=repaired)
