"""Exact small-pool audit of a cancellation-based joint cell bet.

This is a mathematical diagnostic, not a new ranking certificate.
"""
from __future__ import annotations

from itertools import product


N = 2
CELLS = tuple(product(range(3), range(N)))


def coefficients():
    """(r-b) + (c-r) = c-b, with r=0, b=1, c=2."""
    return {(v, i): (0 if v == 0 else -1 if v == 1 else 1)
            for v, i in CELLS}


def draw_distribution(known, coefficients_by_cell):
    """Unequal observable design; zero-coefficient reference need not be bought."""
    active = [cell for cell in CELLS
              if cell not in known and coefficients_by_cell[cell] != 0]
    if not active:
        return {}
    weights = {cell: 1 + cell[0] + cell[1] + sum(known.values())
               for cell in active}
    total = sum(weights.values())
    return {cell: weights[cell] / total for cell in active}


def conditional_audit(matrix, known, p, h, rho=0.8):
    """Return exact E[X], E[e-factor] and nonnegative factor minimum."""
    target = sum(h[c] * matrix[c] for c in CELLS)
    acquired = sum(h[c] * value for c, value in known.items())
    if not p:
        if acquired != target:
            raise AssertionError("Missing nonzero target coefficient")
        return target, 1.0, 1.0
    low = acquired + min(0., *(h[c] / prob for c, prob in p.items()))
    stake = rho / max(1., -low)
    signals = {cell: acquired + h[cell] * matrix[cell] / prob
               for cell, prob in p.items()}
    expected = sum(p[cell] * x for cell, x in signals.items())
    factors = {cell: 1 + stake * x for cell, x in signals.items()}
    expected_factor = sum(p[cell] * f for cell, f in factors.items())
    return expected, expected_factor, min(factors.values())


def audit():
    h = coefficients()
    states = nulls = 0
    for bits in product((0., 1.), repeat=len(CELLS)):
        matrix = dict(zip(CELLS, bits))
        t1 = sum(matrix[0, i] - matrix[1, i] for i in range(N))
        t2 = sum(matrix[2, i] - matrix[0, i] for i in range(N))
        for mask in product((False, True), repeat=len(CELLS)):
            known = {cell: matrix[cell] for cell, flag in zip(CELLS, mask)
                     if flag}
            p = draw_distribution(known, h)
            expected, e_factor, minimum = conditional_audit(matrix, known, p, h)
            if abs(expected - (t1 + t2)) > 1e-12 or minimum < 0.2 - 1e-12:
                raise AssertionError("Conditional mean or bounded factor failed")
            states += 1
            if t1 <= 0 and t2 <= 0:
                nulls += 1
                if e_factor > 1 + 1e-12:
                    raise AssertionError("Joint intersection null not protected")
    # Identical available leaf scores admit two incompatible reference
    # completions. The joint contrast c-b is +N in both worlds.
    leaf_scores = {(1, i): 0. for i in range(N)}
    leaf_scores.update({(2, i): 1. for i in range(N)})
    low_ref = {**leaf_scores, **{(0, i): 0. for i in range(N)}}
    high_ref = {**leaf_scores, **{(0, i): 1. for i in range(N)}}
    def signs(matrix):
        a = sum(matrix[0, i] - matrix[1, i] for i in range(N))
        b = sum(matrix[2, i] - matrix[0, i] for i in range(N))
        return (a, b)
    assert signs(low_ref) == (0, N)
    assert signs(high_ref) == (N, 0)
    # The same point can be made with *strictly opposite* signs in [0,1].
    # The two leaves stay fixed at .25 and .75 while the reference changes.
    fractional = {(1, i): .25 for i in range(N)}
    fractional.update({(2, i): .75 for i in range(N)})
    low_strict = {**fractional, **{(0, i): 0. for i in range(N)}}
    high_strict = {**fractional, **{(0, i): 1. for i in range(N)}}
    assert signs(low_strict) == (-.25 * N, .75 * N)
    assert signs(high_strict) == (.75 * N, -.25 * N)
    return dict(states=states, joint_null_states=nulls,
                same_leaf_worlds=(signs(low_ref), signs(high_ref)),
                opposite_strict_worlds=(signs(low_strict), signs(high_strict)))


if __name__ == "__main__":
    print(audit())
