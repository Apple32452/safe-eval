"""Exact small-pool audit of within-item, outcome-dependent label exposure.

This is a falsification check, not a proposed inference method. It examines
the invalid shortcut of applying an ordinary uniform-permutation pair test
after deciding whether to acquire a candidate label from the current
reference score. It also checks the elementary inverse-probability identity
for a full-support system-item acquisition policy.
"""
from __future__ import annotations

from itertools import combinations
from math import comb


def max_pair_wealth(differences: tuple[int, ...], pool_size: int) -> float:
    """Maximum of the one-sided finite-pool wealth, using a fixed half bet."""
    wealth = maximum = 1.0
    observed_sum = 0
    for t, difference in enumerate(differences, start=1):
        # This offset is valid only for a uniformly permuted, complete pair
        # prefix. Applying it to selected pairs is the intentional error.
        offset = max(-0.99, min(1.0, -observed_sum / (pool_size - t + 1)))
        wealth *= 1.0 + 0.5 * (difference - offset) / (1.0 + offset)
        observed_sum += difference
        maximum = max(maximum, wealth)
    return maximum


def exact_adaptive_filter_audit():
    """Enumerate the 252 distinct equal-weight random orders of five +/- items."""
    pool_size = 10
    threshold = 20.0  # alpha = 0.05, for a single one-sided comparison.
    full_rejections = filtered_rejections = 0
    filtered_labels = []
    for positive_positions in combinations(range(pool_size), pool_size // 2):
        positive = set(positive_positions)
        differences = tuple(1 if position in positive else -1
                            for position in range(pool_size))
        # A is observed for every item; B is queried only when A = 1. The
        # fixed benchmark has A-B=+1 on five items, -1 on five, so its
        # exact contrast is zero under every possible order.
        selected = tuple(value for value in differences if value == 1)
        full_rejections += max_pair_wealth(differences, pool_size) >= threshold
        filtered_rejections += max_pair_wealth(selected, pool_size) >= threshold
        filtered_labels.append(pool_size + len(selected))
    total = comb(pool_size, pool_size // 2)
    assert total == 252 and filtered_rejections == total
    assert full_rejections / total <= 0.05
    assert set(filtered_labels) == {15}
    return dict(alpha=0.05, pool_items=pool_size, null_mean_difference=0,
                possible_orders=total, complete_pair_false_rejections=full_rejections,
                filtered_pair_false_rejections=filtered_rejections,
                filtered_candidate_labels=5, filtered_total_system_item_labels=15)


def inverse_propensity_identity():
    """Check a conditional mean identity for two nonuniform acquisition laws."""
    # Fixed 3-system, 3-item matrix; test the signed mean of systems A and B.
    scores = ((1.0, 0.0, 0.8), (0.6, 0.9, 0.3), (0.5, 0.2, 0.1))
    coefficient = {(v, i): (1.0 / 3 if v == 0 else -1.0 / 3 if v == 1 else 0.0)
                   for v in range(3) for i in range(3)}
    target = sum(coefficient[cell] * scores[cell[0]][cell[1]]
                 for cell in coefficient)
    observed = {(0, 0), (0, 1), (0, 2), (1, 1)}
    remaining = sorted(set(coefficient) - observed)
    predictions = {cell: 0.2 + 0.07 * index
                   for index, cell in enumerate(remaining)}
    base = (sum(coefficient[cell] * scores[cell[0]][cell[1]]
                for cell in observed) +
            sum(coefficient[cell] * predictions[cell] for cell in remaining))
    checks = []
    for weights in ((1, 1, 1, 1, 1), (1, 3, 5, 2, 7)):
        normalizer = sum(weights)
        probabilities = {cell: weight / normalizer
                         for cell, weight in zip(remaining, weights)}
        signals = {cell: base + coefficient[cell] *
                   (scores[cell[0]][cell[1]] - predictions[cell]) /
                   probabilities[cell] for cell in remaining}
        expectation = sum(probabilities[cell] * signals[cell]
                          for cell in remaining)
        # Safe but coarse nonnegative one-step e-factor scale for H: D<=0.
        scale = abs(base) + max(abs(coefficient[cell]) / probabilities[cell]
                                for cell in remaining)
        assert min(1.0 + signal / scale for signal in signals.values()) >= -1e-12
        assert abs(expectation - target) < 1e-12
        assert abs(sum(probabilities[cell] * (1.0 + signals[cell] / scale)
                       for cell in remaining) - 1.0) < 1e-12
        checks.append(dict(weights=weights, expected_signal=expectation,
                           true_contrast=target, scale=scale))
    return checks


def main():
    import json
    print(json.dumps(dict(naive_filter=exact_adaptive_filter_audit(),
                          ipw_identity=inverse_propensity_identity()), indent=2))


if __name__ == "__main__":
    main()
