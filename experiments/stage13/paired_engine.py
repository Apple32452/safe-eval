"""Fixed-pool paired decisions; rejection arithmetic uses integers only.

PPR is the categorical Waudby-Smith--Ramdas construction. Historical correction
and the fixed reserve are existing principles; this is a paired application.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

Q = 2**20
P = 1024
PAIR_COUNT = 237
MAX_N = 820
CAP = 40 * PAIR_COUNT * Q
THRESHOLDS = np.array([40 * Q, CAP], dtype=np.int64)
METHODS = ('deterministic', 'paired_ppr', 'reserve_zero', 'reserve_aligned',
           'reserve_permuted', 'reserve_reversed')
LEVELS = ('pairwise_95', 'family_95')
BASE_NUM = 2 ** np.arange(8, dtype=np.int64)


@lru_cache(maxsize=3)
def binomial_table(n):
    """Python integers; no floating likelihood calculation or overflow."""
    if not 1 <= n <= MAX_N:
        raise ValueError('Unsupported pool size')
    return tuple(tuple(math.comb(i, j) for j in range(i + 1))
                 for i in range(n + 1))


def boundary_modes(n, a, b, c, parity):
    """Exact integer maximizers for null totals (k, k+parity, N-2k-parity).

    Used only when the observed first count exceeds the second count.
    Unavailable support is represented by -1.
    """
    a, b, c = np.broadcast_arrays(np.asarray(a, dtype=np.int64),
                                 np.asarray(b, dtype=np.int64),
                                 np.asarray(c, dtype=np.int64))
    lower = np.maximum(a, b - parity)
    upper = (n - c - parity) // 2
    valid = lower <= upper
    upper = np.maximum(lower, upper)
    while np.any(lower < upper):
        active = lower < upper
        middle = (lower + upper) // 2
        z = n - 2 * middle - parity
        left = (middle + 1) * (middle + parity + 1) * (z - c) * (z - c - 1)
        right = (middle + 1 - a) * (middle + parity + 1 - b) * z * (z - 1)
        increasing = left > right
        lower = np.where(active & increasing, middle + 1, lower)
        upper = np.where(active & ~increasing, middle, upper)
    return np.where(valid, lower, -1)


def raw_evidence(n, positive, negative, equal, table=None):
    """Directional composite-null PPR evidence, floored in units of Q.

    Opposing/zero sample contrasts use zero (a conservative lower bound).
    Empty null support uses CAP; deterministic certificates also apply there.
    """
    table = binomial_table(n) if table is None else table
    counts = np.asarray([positive, negative, equal], dtype=np.int64)
    if counts.ndim != 2 or np.any(counts < 0):
        raise ValueError('Nonnegative count vectors required')
    totals = counts.sum(axis=0)
    if np.any(totals > n) or not np.all(totals == totals[0]):
        raise ValueError('Counts must share a feasible query time')
    t = int(totals[0])
    numerator = 2 * Q * table[n][t]
    denominator_base = (t + 1) * (t + 2)
    result = np.zeros((2, counts.shape[1]), dtype=np.int64)
    for direction in range(2):
        a, b, c = counts[direction], counts[1 - direction], counts[2]
        indices = np.flatnonzero(a > b)
        if not len(indices):
            continue
        aa, bb, cc = a[indices], b[indices], c[indices]
        modes = [boundary_modes(n, aa, bb, cc, d) for d in (0, 1)]
        for j, index in enumerate(indices):
            maximum = 0
            for parity, mode in enumerate(modes):
                k = int(mode[j])
                if k >= 0:
                    product = (table[k][int(aa[j])] *
                               table[k + parity][int(bb[j])] *
                               table[n - 2 * k - parity][int(cc[j])])
                    maximum = max(maximum, product)
            result[direction, index] = (CAP if maximum == 0 else
                min(CAP, numerator // (denominator_base * maximum)))
    return result


def factor_integers(z, lower, upper, n):
    """Both directional expert factors chosen from pre-query bounds.

    Z=z/(P*N). Output shapes (direction,expert,repeat), exact rational factors.
    The observed z chooses a factor; bounds/stakes cannot use that observation.
    """
    z = np.asarray(z, dtype=np.int64)
    lower = np.asarray(lower, dtype=np.int64)
    upper = np.asarray(upper, dtype=np.int64)
    if np.any(z < lower) or np.any(z > upper):
        raise ValueError('Draw lies outside the predictable bounds')
    numerators, denominators = [], []
    den = P * n
    for signed_z, bound in ((z, lower), (-z, -upper)):
        base = BASE_NUM[:, None]
        distance = np.maximum(-bound, 1)[None, :]
        capped = (bound[None, :] < 0) & (2 * base * distance > 8 * den)
        divisor = np.where(capped, 2 * distance, 8 * den)
        numerator = divisor + np.where(capped, signed_z[None, :], base * signed_z[None, :])
        if np.any(2 * numerator < divisor):
            raise AssertionError('A factor fell below one half')
        numerators.append(numerator)
        denominators.append(divisor)
    return np.asarray(numerators), np.asarray(denominators)


def update_capital(capital, z, lower, upper, n):
    numerator, denominator = factor_integers(z, lower, upper, n)
    # N<=820 implies CAP * (392*P*N) < 2**63, including the largest base stake.
    next_capital = np.minimum(CAP, (capital * numerator) // denominator)
    return np.where(capital >= CAP, CAP, next_capital)


def features(history):
    h = np.asarray(history, dtype=float)
    if h.ndim != 2 or min(h.shape) < 2 or not np.isfinite(h).all() or np.any((h < 0) | (h > 1)):
        raise ValueError('A bounded historical matrix is required')
    mean = h.mean(axis=0)
    _, _, vt = np.linalg.svd(h - mean, full_matrices=False)
    basis = vt[:min(3, len(vt))].T * np.sqrt(h.shape[1])
    return mean, np.column_stack([np.ones(h.shape[1]), basis])


class PairedPredictor:
    def __init__(self, history, repeats):
        self.mean, self.x = features(history)
        d = self.x.shape[1]
        self.ridge = np.broadcast_to(np.diag([.25] + [1.] * (d - 1)), (repeats, d, d)).copy()
        self.rhs = np.zeros((repeats, d, 2))

    def predict(self):
        beta = np.linalg.solve(self.ridge, self.rhs)
        full = np.clip(self.mean[None, :, None] + np.einsum('id,rdk->rik', self.x, beta), 0, 1)
        difference = .5 * (full[:, :, 0] - full[:, :, 1])
        return np.rint(P * difference).astype(np.int64)

    def update(self, index, labels):
        xi = self.x[index]
        self.ridge += xi[:, :, None] * xi[:, None, :]
        residual = labels - self.mean[index, None]
        self.rhs += xi[:, :, None] * residual[:, None, :]


class PairOracle:
    """Simulation-only labels. The inference engine sees current pairs only."""
    def __init__(self, labels, repeats):
        self.labels = np.asarray(labels)
        if self.labels.ndim != 2 or self.labels.shape[0] != 2 or np.any((self.labels != 0) & (self.labels != 1)):
            raise ValueError('Two exact binary target rows required')
        self.seen = np.zeros((repeats, self.labels.shape[1]), dtype=bool)

    def __call__(self, index):
        index = np.asarray(index)
        rows = np.arange(len(self.seen))
        if index.shape != rows.shape or index.dtype.kind not in 'iu' or np.any(index < 0) or np.any(index >= self.seen.shape[1]):
            raise ValueError('One valid integer query per path required')
        if self.seen[rows, index].any():
            raise ValueError('Repeated paired query')
        self.seen[rows, index] = True
        return self.labels[:, index].T.copy()


def evaluate(histories, oracle, ledger):
    ledger = np.asarray(ledger)
    if ledger.ndim != 2 or ledger.dtype.kind not in 'iu':
        raise ValueError('Integer ledger required')
    n, repeats = ledger.shape
    if not 2 <= n <= MAX_N or repeats < 1 or len(histories) != 3:
        raise ValueError('Unsupported experiment dimensions')
    if not np.array_equal(np.sort(ledger, axis=0), np.broadcast_to(np.arange(n)[:, None], ledger.shape)):
        raise ValueError('Each ledger must be a permutation of the complete pool')
    predictors = [PairedPredictor(h, repeats) for h in histories]
    if any(len(p.mean) != n for p in predictors):
        raise ValueError('History/ledger misalignment')
    unseen = np.ones((repeats, n), dtype=bool)
    rows = np.arange(repeats)
    counts = np.zeros((3, repeats), dtype=np.int64)
    capital = np.full((4, 2, 8, repeats), Q, dtype=np.int64)
    raw = np.zeros((2, n, repeats), dtype=np.int64)
    bets = np.zeros((4, 2, n, repeats), dtype=np.int64)
    states = np.zeros((3, 4, n, repeats), dtype=np.int32)
    table = binomial_table(n)
    for time, index in enumerate(ledger):
        r = n - time
        observed = counts[0] - counts[1]
        # Every prediction, remaining-pool sum and bound precedes the oracle call.
        summaries = [np.stack([P * observed, np.zeros(repeats, dtype=int),
                               np.zeros(repeats, dtype=int), np.zeros(repeats, dtype=int)])]
        for j, predictor in enumerate(predictors):
            prediction = predictor.predict()
            center = P * observed + (prediction * unseen).sum(axis=1)
            minimum = np.where(unseen, prediction, P + 1).min(axis=1)
            maximum = np.where(unseen, prediction, -P - 1).max(axis=1)
            queried = prediction[rows, index]
            summary = np.stack([center, minimum, maximum, queried])
            states[j, :, time] = summary
            summaries.append(summary)
        labels = np.asarray(oracle(index))
        if labels.shape != (repeats, 2) or np.any((labels != 0) & (labels != 1)):
            raise ValueError('Oracle must reveal a binary pair per repeat')
        labels = labels.astype(np.int64)
        difference = labels[:, 0] - labels[:, 1]
        for j, summary in enumerate(summaries):
            center, minimum, maximum, queried = summary
            z = center + r * (P * difference - queried)
            lower = center + r * (-P - maximum)
            upper = center + r * (P - minimum)
            capital[j] = update_capital(capital[j], z, lower, upper, n)
            bets[j, :, time] = capital[j].sum(axis=1) // 8
        counts[0] += difference == 1
        counts[1] += difference == -1
        counts[2] += difference == 0
        raw[:, time] = raw_evidence(n, *counts, table=table)
        for predictor in predictors:
            predictor.update(index, labels)
        unseen[rows, index] = False
    return dict(ledger=ledger.astype(np.int16), raw=raw, bets=bets, states=states,
                feature_means=np.stack([p.mean for p in predictors]),
                feature_matrices=np.stack([p.x for p in predictors]))


def decisions(trace, differences, thresholds=THRESHOLDS):
    """First valid decisions, plus naive fixed-budget diagnostics.

    Direction 0 is exact full-pool tie; 2 is an unresolved smaller-budget query.
    All methods receive the same deterministic finite-pool certificate.
    """
    ledger, raw, bets = trace['ledger'], trace['raw'], trace['bets']
    n, repeats = ledger.shape
    d = np.asarray(differences)
    if d.shape != (n,) or np.any(~np.isin(d, (-1, 0, 1))):
        raise ValueError('Ternary paired differences required')
    cumulative = np.cumsum(d[ledger], axis=0)
    remaining = n - np.arange(1, n + 1)
    deterministic = np.where(cumulative > remaining[:, None], 1,
                             np.where(cumulative < -remaining[:, None], -1, 2))
    deterministic[-1] = np.sign(cumulative[-1])
    stop = np.full((len(METHODS), len(thresholds), repeats), n, dtype=np.int16)
    direction = np.zeros_like(stop, dtype=np.int8)
    for method in range(len(METHODS)):
        evidence = None if method == 0 else (raw if method == 1 else
                    (3 * raw + bets[method - 2]) // 4)
        for level, threshold in enumerate(thresholds):
            decision = deterministic.copy()
            if evidence is not None:
                plus, minus = evidence >= threshold
                sole = plus ^ minus
                statistical = np.where(plus, 1, -1)
                decision = np.where((decision == 2) & sole, statistical, decision)
            available = decision != 2
            first = available.argmax(axis=0)
            stop[method, level] = first + 1
            direction[method, level] = decision[first, np.arange(repeats)]
    checkpoints = np.maximum(1, np.floor(n * np.array([.25, .5, .75])).astype(int))
    naive = np.sign(cumulative[checkpoints - 1]).astype(np.int8)
    return dict(stop=stop, direction=direction, checkpoints=checkpoints.astype(np.int16), naive=naive)
