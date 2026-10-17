"""Exact small-pool reference for a novelty audit, not a benchmark method.

The top-k budget is elementary finite-cardinality optimization. Combining it
with capped sequential boosting does not by itself establish a new contribution.
All arithmetic is rational; historical probabilities are design inputs only.
"""
from dataclasses import dataclass
from fractions import Fraction


def _fraction(value):
    if not isinstance(value, (int, Fraction)):
        raise TypeError("Use integers or Fraction values, not floating point.")
    return Fraction(value)


def _count(k, r):
    if isinstance(k, bool) or not isinstance(k, int) or not 0 <= k <= r:
        raise ValueError("The remaining total must be an integer in [0, r].")


def _table(table, k):
    table = tuple(tuple(_fraction(x) for x in row) for row in table)
    if not table or any(len(row) != 2 for row in table):
        raise ValueError("A nonempty table of two-outcome factors is required.")
    if any(x < 0 for row in table for x in row):
        raise ValueError("Factors must be nonnegative.")
    _count(k, len(table))
    return table


def centered_factors(predictions, k, theta):
    """Prepare every possible factor before the random item and label arrive."""
    predictions = tuple(_fraction(x) for x in predictions)
    if not predictions or any(not 0 <= x <= 1 for x in predictions):
        raise ValueError("Predictions must be a nonempty vector in [0, 1].")
    r = len(predictions)
    _count(k, r)
    theta = _fraction(theta)
    mean = sum(predictions, Fraction(0)) / r
    center = Fraction(k, r)
    return _table(((1 + theta * (mean - center - m),
                    1 + theta * (1 + mean - center - m))
                   for m in predictions), k)


def capped_factors(table, k, multiplier, cap):
    table = _table(table, k)
    multiplier, cap = _fraction(multiplier), _fraction(cap)
    if multiplier < 1 or cap <= 1:
        raise ValueError("The multiplier must be >= 1 and the factor cap > 1.")
    return tuple(tuple(min(multiplier * f, cap) for f in row) for row in table)


def worst_expectation(table, k, multiplier=1, cap=2):
    """Exact maximum over all fixed binary assignments of remaining total k."""
    capped = capped_factors(table, k, multiplier, cap)
    differences = sorted((one - zero for zero, one in capped), reverse=True)
    return (sum((zero for zero, _ in capped), Fraction(0))
            + sum(differences[:k], Fraction(0))) / len(capped)


@dataclass(frozen=True)
class Boost:
    multiplier: Fraction
    finite_maximum: bool


def centered_boost(predictions, k, theta, cap):
    """Largest feasible boost for this centered family, or its saturated limit.

    For either sign of theta the capped outcome difference is nondecreasing
    in m_i. The same assignment (ones at the largest predictions) is therefore
    worst for every multiplier. Its budget is piecewise linear. This small
    reference is not a production confidence-sequence implementation.
    """
    predictions = tuple(_fraction(x) for x in predictions)
    table = centered_factors(predictions, k, theta)
    cap = _fraction(cap)
    if cap <= 1:
        raise ValueError("The factor cap must exceed one.")
    ones = set(sorted(range(len(table)), key=lambda i: predictions[i],
                      reverse=True)[:k])
    values = sorted((table[i][int(i in ones)] for i in range(len(table))),
                    reverse=True)
    positive = [x for x in values if x > 0]
    r = len(values)
    # Zero factors stay zero. If even the fully saturated budget is <= 1,
    # there is no finite maximum multiplier; return an equivalent finite one.
    if len(positive) * cap <= r:
        multiplier = max(Fraction(1), max(cap / x for x in positive))
        return Boost(multiplier, False)
    remaining = sum(positive, Fraction(0))
    for saturated, value in enumerate(positive):
        root = (r - saturated * cap) / remaining
        if root <= cap / value:
            if root < 1:
                raise ArithmeticError("Unexpected infeasible base factor.")
            return Boost(root, True)
        remaining -= value
    raise ArithmeticError("A finite piecewise-linear root was not found.")


def naive_plugin_counterexample():
    predictions = (Fraction(1, 10), Fraction(9, 10))
    table = centered_factors(predictions, 1, 1)
    cap, multiplier = Fraction(3, 2), Fraction(185, 181)
    capped = capped_factors(table, 1, multiplier, cap)
    working_mean = sum(((1 - m) * z + m * o
                        for m, (z, o) in zip(predictions, capped)), Fraction(0)) / 2
    # The fixed assignment is y=(0, 1); randomness is solely the next item.
    true_mean = (capped[0][0] + capped[1][1]) / 2
    robust = centered_boost(predictions, 1, 1, cap)
    return {"working_mean": working_mean, "true_mean": true_mean,
            "naive_multiplier": multiplier,
            "robust_multiplier": robust.multiplier}
