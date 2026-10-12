"""Published binary finite-population PPR confidence sequence.

Waudby-Smith & Ramdas, arXiv:2006.04347v4, Theorem 2.1. The working prior
is BetaBinomial(N, 1, 1), i.e. uniform over the unknown number of successes.
This exact binary control was added after initial Stage 4 results were seen;
it is supplemental and does not change the original locked comparisons.
"""
from __future__ import annotations
from functools import lru_cache
import math
import numpy as np


@lru_cache(maxsize=8)
def log_factorials(n):
    return np.array([math.lgamma(i + 1) for i in range(n + 2)])


def log_ppr(successes, queries, n):
    """Log(marginal ordered-sequence likelihood / fixed-K likelihood).

    The Beta(1,1) marginal is B(s+1,t-s+1), independent of N.
    Impossible success-count candidates have infinite ratio and are rejected.
    """
    successes = np.asarray(successes, dtype=int)
    if successes.ndim != 1 or not 0 <= queries <= n or np.any((successes < 0) | (successes > queries)):
        raise ValueError('invalid binary counts')
    k = np.arange(n + 1)[None, :]
    s = successes[:, None]; failures = queries - s
    possible = (k >= s) & (n - k >= failures)
    lf = log_factorials(n)
    log_likelihood = (lf[k] - lf[np.maximum(k - s, 0)] + lf[n - k]
                      - lf[np.maximum(n - k - failures, 0)] - lf[n] + lf[n - queries])
    log_marginal = lf[s] + lf[failures] - lf[queries + 1]
    return np.where(possible, log_marginal - log_likelihood, np.inf)


def ppr_interval(successes, queries, n, delta=.05):
    if not 0 < delta < 1:
        raise ValueError('invalid confidence level')
    accepted = log_ppr(successes, queries, n) < math.log(1 / delta)
    grid = np.arange(n + 1) / n
    lower = np.min(np.where(accepted, grid, np.inf), axis=1)
    upper = np.max(np.where(accepted, grid, -np.inf), axis=1)
    nonempty = accepted.any(axis=1)
    return np.where(nonempty, lower, 1.), np.where(nonempty, upper, 0.)


def evaluate_binary(oracle, n, trials, seed, delta=.05, epsilon=.05):
    """Same CDF-based uniform query stream as frozen Stage 3."""
    if n < 2 or trials < 1 or not 0 < epsilon < .5:
        raise ValueError('invalid benchmark settings')
    rng = np.random.default_rng(seed)
    unseen = np.ones((trials, n), dtype=bool)
    rows = np.arange(trials)
    successes = np.zeros(trials, dtype=int)
    lower = np.zeros(trials); upper = np.ones(trials)
    stop = np.zeros(trials, dtype=int)
    stop_l = np.full(trials, np.nan); stop_u = stop_l.copy()
    lows, highs, selected, estimates = [], [], [], []
    for t in range(1, n + 1):
        p = unseen / (n - t + 1)
        cdf = np.cumsum(p, axis=1); cdf[:, -1] = 1.
        indices = np.sum(cdf <= rng.random(trials)[:, None], axis=1)
        y = np.asarray(oracle(indices))
        if y.shape != (trials,) or np.any((y != 0) & (y != 1)):
            raise ValueError('PPR binary control requires exact binary outcomes')
        successes += y.astype(int); unseen[rows, indices] = False
        lo, hi = ppr_interval(successes, t, n, delta)
        lower = np.maximum(lower, lo); upper = np.minimum(upper, hi)
        if t == n:
            lower = successes / n; upper = lower.copy()
        new_stop = (stop == 0) & (upper >= lower) & (upper - lower <= 2 * epsilon + 1e-12)
        stop[new_stop] = t; stop_l[new_stop] = lower[new_stop]; stop_u[new_stop] = upper[new_stop]
        lows.append(lower.copy()); highs.append(upper.copy()); selected.append(indices.copy())
        estimates.append(successes / t)
    return dict(lower=np.asarray(lows), upper=np.asarray(highs), selected=np.asarray(selected),
                estimate=np.asarray(estimates), stop=stop, stop_lower=stop_l, stop_upper=stop_u)
