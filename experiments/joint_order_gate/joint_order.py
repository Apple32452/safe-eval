"""Exact conditional null constraints for three finite binary system rows."""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, product

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

PAIRS = ((0, 1), (0, 2), (1, 2))
DIRECTED = tuple((a, b) for a in range(3) for b in range(3) if a != b)
ORDERS = tuple(r for r in product(range(3), repeat=3)
               if set(r) == set(range(max(r) + 1)))
RANK = np.asarray(ORDERS, dtype=int)
IMPLIED = tuple(tuple(i for i, (a, b) in enumerate(DIRECTED) if w[a] <= w[b])
                for w in ORDERS)
RHOS = np.array([.02, .05, .1, .2, .4, .8])


class NullPolytope:
    def __init__(self, relations):
        rows = [-np.eye(3), np.eye(3)]
        for a, b in relations:
            row = np.zeros((1, 3)); row[0, a] = 1; row[0, b] = -1
            rows.append(row)
        self.a = np.vstack(rows)
        indices, inverse = [], []
        for ids in combinations(range(len(self.a)), 3):
            matrix = self.a[list(ids)]
            if abs(np.linalg.det(matrix)) > .5:
                indices.append(ids); inverse.append(np.linalg.inv(matrix))
        self.indices = np.asarray(indices)
        self.inverse = np.asarray(inverse)

    def vertices(self, successes, remaining):
        b = np.r_[-successes, successes + remaining,
                  np.zeros(len(self.a) - 6)]
        values = np.einsum("kij,kj->ki", self.inverse, b[self.indices])
        rounded = np.rint(values).astype(int)
        if not np.allclose(rounded, values, atol=1e-9):
            raise AssertionError("Nonintegral box/order vertex")
        good = np.all(rounded @ self.a.T <= b + 1e-9, axis=1)
        return np.unique(rounded[good], axis=0)


JOINT_NULLS = tuple(NullPolytope([DIRECTED[i] for i in ids]) for ids in IMPLIED)
PAIR_NULLS = tuple(NullPolytope([pair]) for pair in DIRECTED)


def possible_orders(s, m):
    result = []
    for ranks in ORDERS:
        lower = -1
        feasible = True
        for rank in range(max(ranks) + 1):
            group = np.array(ranks) == rank
            lower = max(lower, int(np.max(s[group])))
            if lower > int(np.min((s + m)[group])):
                feasible = False
                break
        result.append(feasible)
    return np.asarray(result, bool)


def proposal(s, m, prior, n):
    if not m.sum():
        raise ValueError("No unpurchased cells")
    pred = np.clip((s + 4 * np.asarray(prior)) / (n - m + 4), .05, .95)
    uncertainty = np.array([sum(1 / max(abs(pred[v] - pred[w]), .1)
                                for w in range(3) if w != v) for v in range(3)])
    weight = m * uncertainty
    q = .2 * m / m.sum() + .8 * weight / weight.sum()
    return q, pred


def event_rows(vertices, s, m, q):
    r = np.divide(vertices - s, m, out=np.zeros_like(vertices, dtype=float),
                  where=m > 0)
    rows = np.empty((len(vertices), 6))
    rows[:, 0::2] = q * (1 - r)
    rows[:, 1::2] = q * r
    if np.any(rows < -1e-10) or not np.allclose(rows.sum(axis=1), 1):
        raise AssertionError("Invalid conditional event law")
    return rows


def fitted_factor(rows, q, pred):
    """Return only a factor with its full null constraints checked."""
    if not len(rows):
        return np.ones(6), False, False
    alt = np.empty(6)
    alt[0::2], alt[1::2] = q * (1 - pred), q * pred
    result = minimize(lambda f: -float(alt @ np.log(f)), np.ones(6),
                      jac=lambda f: -alt / f, method="SLSQP",
                      bounds=[(.001, 10000)] * 6,
                      constraints=[{"type": "ineq", "fun": lambda f: 1 - rows @ f,
                                    "jac": lambda f: -rows}],
                      options={"ftol": 1e-10, "maxiter": 500})
    candidate = result.x
    if not np.isfinite(candidate).all() or np.any(candidate <= 0):
        return np.ones(6), True, bool(result.success)
    candidate = candidate / ((1 + 1e-9) * max(1., float(np.max(rows @ candidate))))
    if float(alt @ np.log(candidate)) < 0:
        return np.ones(6), True, bool(result.success)
    if float(np.max(rows @ candidate)) > 1 + 1e-12:
        raise AssertionError("Uncertified optimized factor")
    return candidate, False, bool(result.success)


def centered_factors(s, m, q, pred):
    out = np.ones((6, 6, len(RHOS)))
    for edge, (a, b) in enumerate(DIRECTED):
        sign = np.zeros(3); sign[a] = 1; sign[b] = -1
        base = float(sign @ (s + m * pred))
        coefficient = np.divide(sign * m, q, out=np.zeros(3), where=q > 0)
        x = np.column_stack((base - coefficient * pred,
                             base + coefficient * (1 - pred))).ravel()
        available = np.repeat(q > 0, 2)
        low = float(np.min(x[available]))
        # E[X]=T[a]-T[b]; this factor tests the null T[a]<=T[b].
        out[edge] = 1 + x[:, None] * RHOS / max(1., -low)
        if np.any(out[edge, available] < .2 - 1e-9):
            raise AssertionError("Unsafe centered factor")
    return out


@lru_cache(maxsize=30000)
def state_update(s_tuple, m_tuple, prior, n):
    s, m = np.asarray(s_tuple), np.asarray(m_tuple)
    q, pred = proposal(s, m, prior, n)
    joint, pair, fallbacks, failed_status = [], [], 0, 0
    for target, nulls in ((joint, JOINT_NULLS), (pair, PAIR_NULLS)):
        for null in nulls:
            vertices = null.vertices(s, m)
            target_total = s + m * pred
            bound = np.r_[-s, s + m, np.zeros(len(null.a) - 6)]
            if len(vertices) and np.all(null.a @ target_total <= bound + 1e-12):
                # The predictive law itself lies in the convex null. Jensen's
                # inequality makes the unit factor exactly log-optimal.
                f = np.ones(6)
            elif len(vertices):
                f, fallback, success = fitted_factor(event_rows(vertices, s, m, q), q, pred)
                fallbacks += int(fallback)
                failed_status += int(not success)
            else:
                f = np.ones(6)
            target.append(f)
    return {"q": q, "pred": pred, "joint": np.asarray(joint),
            "pair": np.asarray(pair), "centered": centered_factors(s, m, q, pred),
            "fallbacks": fallbacks, "failed_status": failed_status}


def closure_logs(pair_logs):
    return np.array([logsumexp(pair_logs[list(ids)]) - np.log(len(ids))
                     for ids in IMPLIED])


def decide(s, m, rejected, previous):
    decision = previous.copy()
    survivors = RANK[~rejected & possible_orders(s, m)]
    for edge, (a, b) in enumerate(PAIRS):
        if decision[edge] != 2:
            continue
        if s[a] > s[b] + m[b]:
            decision[edge] = 1
        elif s[a] + m[a] < s[b]:
            decision[edge] = -1
        elif m[a] == m[b] == 0:
            decision[edge] = int(np.sign(s[a] - s[b]))
        elif len(survivors):
            signs = np.sign(survivors[:, a] - survivors[:, b])
            if np.all(signs == 1):
                decision[edge] = 1
            elif np.all(signs == -1):
                decision[edge] = -1
    return decision


class Evidence:
    def __init__(self, alpha=.05):
        self.threshold = np.log(1 / alpha)
        self.joint = np.zeros(13)
        self.pair = np.zeros(6)
        self.centered = np.zeros((6, len(RHOS)))
        self.rejected = np.zeros((3, 13), bool)
        self.decisions = np.full((3, 3), 2, int)

    def advance(self, update, event, s, m):
        self.joint += np.log(update["joint"][:, event])
        self.pair += np.log(update["pair"][:, event])
        self.centered += np.log(update["centered"][:, event])
        center_mix = logsumexp(self.centered, axis=1) - np.log(len(RHOS))
        logs = np.vstack((self.joint, closure_logs(self.pair), closure_logs(center_mix)))
        self.rejected |= logs >= self.threshold
        self.rejected |= ~possible_orders(s, m)[None, :]
        for method in range(3):
            self.decisions[method] = decide(s, m, self.rejected[method],
                                             self.decisions[method])
