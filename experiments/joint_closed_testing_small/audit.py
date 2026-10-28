"""Exact small-case audit of closed testing with finite-pool cell e-factors.

This is a standard closed-testing baseline, not a new statistical method.
Scores are fixed binary cells; randomness is the uniformly shuffled query order.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from fractions import Fraction
from functools import lru_cache


SYSTEMS = 3
ITEMS = 2
CELLS = SYSTEMS * ITEMS
EDGES = ((0, 1), (0, 2))
MATRICES = tuple(itertools.product((0, 1), repeat=CELLS))
ORDERS = tuple(itertools.permutations(range(CELLS)))
RAW_FAVORABLE = Fraction(4, 1)


def agrees(state, matrix):
    return all(x is None or x == y for x, y in zip(state, matrix))


def null_holds(matrix, edge):
    a, b = edge
    return sum(matrix[a * ITEMS:(a + 1) * ITEMS]) <= sum(
        matrix[b * ITEMS:(b + 1) * ITEMS]
    )


def logical_rejection(state, edge):
    a, b = edge
    row_a = state[a * ITEMS:(a + 1) * ITEMS]
    row_b = state[b * ITEMS:(b + 1) * ITEMS]
    lower_a = sum(x for x in row_a if x is not None)
    upper_b = sum(x for x in row_b if x is not None) + row_b.count(None)
    return lower_a > upper_b


def raw_factor(cell, outcome, edge):
    a, b = edge
    if cell // ITEMS == a:
        return RAW_FAVORABLE if outcome else Fraction(1)
    if cell // ITEMS == b:
        return RAW_FAVORABLE if not outcome else Fraction(1)
    return Fraction(1)


@lru_cache(maxsize=None)
def calibrated_factor(state, cell, outcome, edge):
    """Maximize conditional expected raw factor over every null completion."""
    unseen = tuple(i for i, x in enumerate(state) if x is None)
    null_completions = (
        matrix for matrix in MATRICES if agrees(state, matrix)
        and null_holds(matrix, edge)
    )
    support = max(
        (sum(raw_factor(i, matrix[i], edge) for i in unseen) / len(unseen)
         for matrix in null_completions),
        default=None,
    )
    if support is None:
        # This null is already logically false on every completion.
        return Fraction(1)
    return raw_factor(cell, outcome, edge) / support


def stops(matrix, order, alpha):
    state = [None] * CELLS
    wealth = [Fraction(1), Fraction(1)]
    closed_stop = bonf_stop = None
    wrong_closed = wrong_bonf = False
    for step, cell in enumerate(order, 1):
        factors = [calibrated_factor(tuple(state), cell, matrix[cell], edge)
                   for edge in EDGES]
        wealth = [old * factor for old, factor in zip(wealth, factors)]
        state[cell] = matrix[cell]
        logical = [logical_rejection(state, edge) for edge in EDGES]
        bonf = [logical[i] or wealth[i] >= 2 / alpha for i in range(2)]
        # E12 = (E1 + E2)/2 is a supermartingale under H1 intersect H2.
        intersection_rejected = (any(logical) or
                                 sum(wealth) / 2 >= 1 / alpha)
        closed = [logical[i] or
                  (wealth[i] >= 1 / alpha and intersection_rejected)
                  for i in range(2)]
        if any(bonf[i] and not closed[i] for i in range(2)):
            raise AssertionError("Closed testing failed to include Bonferroni")
        wrong_closed |= any(closed[i] and null_holds(matrix, edge)
                            for i, edge in enumerate(EDGES))
        wrong_bonf |= any(bonf[i] and null_holds(matrix, edge)
                          for i, edge in enumerate(EDGES))
        if closed_stop is None and all(closed):
            closed_stop = step
        if bonf_stop is None and all(bonf):
            bonf_stop = step
    return closed_stop, bonf_stop, wrong_closed, wrong_bonf


def audit(alpha=Fraction(1, 20)):
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    # Exhaust every partial history and every null matrix to check the actual
    # conditional factor inequality in the full acquisition filtration.
    factor_checks = 0
    for state in itertools.product((None, 0, 1), repeat=CELLS):
        unseen = tuple(i for i, x in enumerate(state) if x is None)
        if not unseen:
            continue
        for edge in EDGES:
            for matrix in MATRICES:
                if not agrees(state, matrix) or not null_holds(matrix, edge):
                    continue
                average = sum(calibrated_factor(
                    state, cell, matrix[cell], edge) for cell in unseen
                ) / len(unseen)
                factor_checks += 1
                if average > 1:
                    raise AssertionError((state, edge, matrix, average))

    path_count = 0
    strict_paths = 0
    maximum_wrong_closed = maximum_wrong_bonf = 0
    target = (1, 1, 0, 0, 0, 0)
    target_costs = Counter()
    for matrix in MATRICES:
        wrong_closed = wrong_bonf = 0
        for order in ORDERS:
            path_count += 1
            closed_cost, bonf_cost, closed_error, bonf_error = stops(
                matrix, order, alpha)
            wrong_closed += closed_error
            wrong_bonf += bonf_error
            # Both are None if either desired direction is actually false;
            # the statistic below concerns the all-positive example only.
            if matrix == target:
                if closed_cost is None or bonf_cost is None:
                    raise AssertionError("Full-pool fallback failed")
                target_costs["closed"] += closed_cost
                target_costs["bonferroni"] += bonf_cost
                strict_paths += closed_cost < bonf_cost
                if closed_cost > bonf_cost:
                    raise AssertionError("Closed testing lost to Bonferroni")
        maximum_wrong_closed = max(maximum_wrong_closed, wrong_closed)
        maximum_wrong_bonf = max(maximum_wrong_bonf, wrong_bonf)
        if wrong_closed > alpha * len(ORDERS):
            raise AssertionError((matrix, wrong_closed, len(ORDERS)))
    return {
        "status": "passed",
        "alpha": str(alpha),
        "conditional_factor_checks": factor_checks,
        "fixed_matrices": len(MATRICES),
        "query_orders": len(ORDERS),
        "matrix_order_paths": path_count,
        "all_positive_target_mean_closed_cost": float(target_costs["closed"] / len(ORDERS)),
        "all_positive_target_mean_bonferroni_cost": float(
            target_costs["bonferroni"] / len(ORDERS)),
        "target_paths_with_strict_closed_gain": strict_paths,
        "maximum_closed_family_errors_per_720_orders": maximum_wrong_closed,
        "maximum_bonferroni_family_errors_per_720_orders": maximum_wrong_bonf,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha-denominator", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(audit(Fraction(1, args.alpha_denominator)),
                     indent=2, sort_keys=True))
