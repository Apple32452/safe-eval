"""Small, exhaustive feasibility study for partial-block conditional e-factors.

This is a development calculation, not a scalable certificate or an ICML claim.
"""
from __future__ import annotations

import argparse
import itertools
import json

import numpy as np
from scipy.optimize import minimize, minimize_scalar


def instance(n: int, q: float, pa: float, pb: float):
    """Build all observable events and every binary fixed-population null."""
    if not 0 < q <= 1 or not 0 < pa < 1 or not 0 < pb < 1 or n < 2:
        raise ValueError("Invalid instance")
    events = [(i, a, b) for i in range(n) for a in (0, 1)
              for b in (-1, 0, 1) if q < 1 or b != -1]
    nulls = [np.array(bits, dtype=np.int8).reshape(2, n)
             for bits in itertools.product((0, 1), repeat=2 * n)
             if sum(bits[:n]) <= sum(bits[n:])]
    a_matrix = np.zeros((len(nulls), len(events)))
    alt = np.zeros(len(events))
    for k, (i, a, b) in enumerate(events):
        draw = (q if b != -1 else 1 - q) / n
        a_matrix[:, k] = draw * np.array([
            arr[0, i] == a and (b == -1 or arr[1, i] == b) for arr in nulls
        ])
        alt[k] = draw * (pa if a else 1 - pa) * (
            1 if b == -1 else pb if b else 1 - pb)
    assert np.allclose(a_matrix.sum(axis=1), 1)
    assert np.isclose(alt.sum(), 1)
    return events, nulls, a_matrix, alt


def ht_factor(events, n, q, pa, pb, rho):
    center = n * (pa - pb)
    x = np.array([center + n * (a - pa) -
                  (0 if b == -1 else n / q * (b - pb))
                  for _, a, b in events])
    bound = max(1, -x.min())
    return 1 + rho * x / bound


def separate_null(events, n, q, factors):
    """Find a worst fixed binary null by dynamic programming in O(n^2).

    The state is the running score difference. This is a constraint
    separation oracle for the *empty-history, two-system* observation model.
    """
    if len(events) != len(factors):
        raise ValueError("One factor is required per observable event")
    index = {event: k for k, event in enumerate(events)}
    offset = n
    value = np.full(2 * n + 1, -np.inf)
    value[offset] = 0
    predecessor = np.full((n + 1, 2 * n + 1), -1, dtype=int)
    assignment = np.full((n + 1, 2 * n + 1, 2), -1, dtype=int)
    for i in range(n):
        next_value = np.full_like(value, -np.inf)
        for old in np.flatnonzero(np.isfinite(value)):
            for a, b in itertools.product((0, 1), repeat=2):
                new = old + a - b
                local = q * factors[index[i, a, b]] / n
                if q < 1:
                    local += (1 - q) * factors[index[i, a, -1]] / n
                score = value[old] + local
                if score > next_value[new]:
                    next_value[new] = score
                    predecessor[i + 1, new] = old
                    assignment[i + 1, new] = a, b
        value = next_value
    state = int(np.argmax(value[:offset + 1]))
    optimum = float(value[state])
    worst = np.empty((2, n), dtype=np.int8)
    for i in range(n, 0, -1):
        worst[:, i - 1] = assignment[i, state]
        state = predecessor[i, state]
    if state != offset or worst[0].sum() > worst[1].sum():
        raise AssertionError("Invalid dynamic-programming null completion")
    return optimum, worst


def alternative_probs(events, n, q, pa, pb):
    return np.array([
        (q if b != -1 else 1 - q) / n * (pa if a else 1 - pa) *
        (1 if b == -1 else pb if b else 1 - pb)
        for _, a, b in events
    ])


def run(n=4, q=.25, pa=.85, pb=.15):
    events, nulls, a_matrix, alt = instance(n, q, pa, pb)
    # A growth-optimal factor for the given alternative and all fixed nulls.
    # Each row of A is an exact conditional expectation of a factor under
    # one possible fixed binary null matrix.
    result = minimize(
        lambda f: -np.dot(alt, np.log(f)),
        np.full(len(events), .9),
        jac=lambda f: -alt / f,
        bounds=[(1e-8, 1e5)] * len(events),
        constraints=[dict(type="ineq", fun=lambda f: 1 - a_matrix @ f,
                          jac=lambda f: -a_matrix)],
        method="SLSQP", options=dict(ftol=1e-12, maxiter=2000),
    )
    if not result.success or np.max(a_matrix @ result.x) > 1 + 1e-8:
        raise RuntimeError(f"Optimization or null audit failed: {result.message}")
    dp_max, _ = separate_null(events, n, q, result.x)
    if not np.isclose(dp_max, np.max(a_matrix @ result.x), atol=1e-10):
        raise AssertionError("DP and exhaustive null audits disagree")
    ht_opt = minimize_scalar(
        lambda rho: -np.dot(alt, np.log(ht_factor(events, n, q, pa, pb, rho))),
        bounds=(0, .999999), method="bounded", options=dict(xatol=1e-12),
    )
    ht = ht_factor(events, n, q, pa, pb, ht_opt.x)
    if np.max(a_matrix @ ht) > 1 + 1e-10:
        raise AssertionError("HT baseline failed fixed-null audit")
    reversed_alt = alternative_probs(events, n, q, 1 - pa, 1 - pb)
    return dict(n=n, q=q, pa=pa, pb=pb, null_matrices=len(nulls),
                exact_growth=float(np.dot(alt, np.log(result.x))),
                ht_growth=float(np.dot(alt, np.log(ht))),
                exact_growth_per_score=float(np.dot(alt, np.log(result.x)) / (1 + q)),
                ht_growth_per_score=float(np.dot(alt, np.log(ht)) / (1 + q)),
                exact_reversed_growth=float(np.dot(reversed_alt, np.log(result.x))),
                ht_rho=float(ht_opt.x), exact_max_null=float(np.max(a_matrix @ result.x)),
                dp_max_null=dp_max,
                ht_max_null=float(np.max(a_matrix @ ht)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps([run(n=args.n, q=q, pa=pa, pb=pb)
                      for pa, pb in ((.85, .15), (.95, .05))
                      for q in (.2, .5, 1.0)], indent=2))
